# Manual Técnico - Aula Virtual v2.1.0

## Índice
1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Modelos de Datos](#modelos-de-datos)
3. [API y Endpoints](#api-y-endpoints)
4. [Sistema de Disponibilidad](#sistema-de-disponibilidad)
5. [Control de Acceso a Clases](#control-de-acceso-a-clases)
6. [Seguridad](#seguridad)
7. [Despliegue](#despliegue)
8. [Mantenimiento](#mantenimiento)

---

## Arquitectura del Sistema

### Stack Tecnológico
- **Backend**: Flask 3.0.0 + SQLAlchemy
- **Base de Datos**: PostgreSQL 15-alpine
- **WSGI Server**: Gunicorn 21.2.0 (4 workers sync)
- **Proxy Inverso**: Nginx 1.25-alpine
- **Cache**: Redis 7-alpine
- **Task Queue**: Celery
- **Videoconferencia**: Jitsi Meet
- **Contenedorización**: Docker + Docker Compose

### Contenedores Docker
```yaml
services:
  db:           # PostgreSQL 15
  redis:        # Redis 7
  web:          # Flask + Gunicorn
  nginx:        # Nginx proxy
  celery:       # Celery worker
```

### Estructura de Directorios
```
AulaVirtual/
├── app/
│   ├── __init__.py           # Factory app
│   ├── models.py             # Modelos SQLAlchemy
│   ├── routes.py             # Rutas principales
│   ├── admin.py              # Panel admin
│   ├── auth.py               # Autenticación
│   ├── api.py                # API REST
│   ├── tasks.py              # Tareas Celery
│   ├── email.py              # Emails
│   ├── utils.py              # Utilidades
│   ├── static/               # CSS, JS, uploads
│   └── templates/            # Jinja2 templates
├── nginx/
│   └── nginx.conf            # Config Nginx
├── docker-compose.yml        # Orquestación
├── Dockerfile                # Imagen web
├── requirements.txt          # Dependencias Python
├── config.py                 # Configuración
└── run.py                    # Entry point
```

---

## Modelos de Datos

### Modelo: DisponibilidadDocente
**Tabla**: `disponibilidad_docente`

```python
class DisponibilidadDocente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'))
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Domingo, 6=Sábado
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
```

**Uso**:
- Define la disponibilidad recurrente semanal del docente
- `dia_semana`: 0 (Domingo) a 6 (Sábado)
- Permite múltiples bloques por día
- Flag `activo` para deshabilitar sin eliminar

**Relación**:
- `docente_rel`: Relación 1:N con modelo `Docente`

---

### Modelo: BloqueNoDisponible
**Tabla**: `bloques_no_disponibles`

```python
class BloqueNoDisponible(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'))
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time)              # Opcional
    hora_fin = db.Column(db.Time)                 # Opcional
    motivo = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
```

**Uso**:
- Bloquea fechas/horas específicas (vacaciones, eventos)
- Si `hora_inicio` y `hora_fin` son NULL, bloquea todo el día
- Tiene precedencia sobre disponibilidad recurrente

**Método**:
```python
def incluye_fecha_hora(self, fecha_hora):
    """Verifica si fecha_hora está bloqueada"""
    if fecha_hora.date() != self.fecha:
        return False
    if self.hora_inicio and self.hora_fin:
        return self.hora_inicio <= fecha_hora.time() <= self.hora_fin
    return True  # Bloqueo de día completo
```

---

### Modelo: Clase (Actualizado)
**Tabla**: `clases`

**Nuevos Campos v2.1.0**:
```python
# Control de estado
clase_cerrada = db.Column(db.Boolean, default=False)
fecha_cierre = db.Column(db.DateTime)

# Control de acceso
acceso_unico = db.Column(db.Boolean, default=True)
conexiones_estudiante = db.Column(db.Integer, default=0)
conexiones_docente = db.Column(db.Integer, default=0)
primera_conexion_estudiante = db.Column(db.DateTime)
primera_conexion_docente = db.Column(db.DateTime)

# Clases especiales
es_gratuita = db.Column(db.Boolean, default=False)
creada_por_admin = db.Column(db.Boolean, default=False)
notas_admin = db.Column(db.Text)

# Seguridad enlaces
regenerar_link = db.Column(db.Boolean, default=True)
link_jitsi_usado = db.Column(db.Boolean, default=False)
```

**Métodos Clave**:

#### `puede_acceder(usuario_id, es_docente=False)`
```python
def puede_acceder(self, usuario_id, es_docente=False):
    """
    Valida si un usuario puede acceder a la clase
    
    Returns:
        tuple: (puede_acceder: bool, mensaje: str)
    """
    ahora = datetime.utcnow()
    
    # 1. Verificar que la clase no esté cerrada
    if self.clase_cerrada:
        return False, 'Esta clase ha sido cerrada'
    
    # 2. Ventana temporal: 15 minutos antes hasta fin programado
    margen_antes = timedelta(minutes=15)
    tiempo_inicio_permitido = self.fecha_inicio - margen_antes
    
    if ahora < tiempo_inicio_permitido:
        minutos_faltantes = int((tiempo_inicio_permitido - ahora).total_seconds() / 60)
        return False, f'La clase estará disponible en {minutos_faltantes} minutos'
    
    if ahora > self.fecha_fin:
        return False, 'La clase ha finalizado'
    
    # 3. Control de acceso único
    if self.acceso_unico:
        if es_docente and self.conexiones_docente > 0:
            return False, 'Ya has utilizado tu acceso único a esta clase'
        if not es_docente and self.conexiones_estudiante > 0:
            return False, 'Ya has utilizado tu acceso único a esta clase'
    
    # 4. Verificar enlace usado (si aplica)
    if self.link_jitsi_usado and not self.regenerar_link:
        return False, 'El enlace de esta clase ya fue utilizado'
    
    return True, 'Acceso permitido'
```

#### `registrar_acceso(usuario_id, es_docente=False)`
```python
def registrar_acceso(self, usuario_id, es_docente=False):
    """
    Registra el acceso de un usuario y regenera enlace si es necesario
    """
    ahora = datetime.utcnow()
    
    if es_docente:
        if not self.primera_conexion_docente:
            self.primera_conexion_docente = ahora
        self.conexiones_docente += 1
    else:
        if not self.primera_conexion_estudiante:
            self.primera_conexion_estudiante = ahora
        self.conexiones_estudiante += 1
    
    # Marcar enlace como usado
    if not self.link_jitsi_usado:
        self.link_jitsi_usado = True
    
    # Regenerar enlace si está configurado
    if self.regenerar_link and self.link_jitsi_usado:
        self.link_jitsi = generar_enlace_jitsi()
        self.link_jitsi_usado = False
    
    db.session.commit()
```

#### `cerrar_automaticamente()`
```python
def cerrar_automaticamente(self):
    """
    Cierra la clase automáticamente al finalizar
    Debe ser llamado por tarea Celery programada
    """
    if datetime.utcnow() > self.fecha_fin and not self.clase_cerrada:
        self.clase_cerrada = True
        self.fecha_cierre = datetime.utcnow()
        db.session.commit()
```

---

## API y Endpoints

### Disponibilidad Horaria

#### `GET /disponibilidad`
**Descripción**: Panel de gestión de disponibilidad del docente  
**Autenticación**: Requerida (rol: docente)  
**Response**: HTML template con disponibilidades y bloques

```python
@main.route('/disponibilidad')
@login_required
def disponibilidad():
    if current_user.rol != 'docente':
        flash('Esta función es solo para docentes', 'warning')
        return redirect(url_for('main.dashboard'))
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    disponibilidades = DisponibilidadDocente.query.filter_by(
        docente_id=docente.id
    ).order_by(DisponibilidadDocente.dia_semana).all()
    
    from datetime import date
    bloques = BloqueNoDisponible.query.filter(
        BloqueNoDisponible.docente_id == docente.id,
        BloqueNoDisponible.fecha >= date.today()
    ).order_by(BloqueNoDisponible.fecha).all()
    
    return render_template('docentes/disponibilidad.html', 
                         docente=docente,
                         disponibilidades=disponibilidades,
                         bloques=bloques)
```

#### `POST /disponibilidad/agregar`
**Descripción**: Agregar horario disponible  
**Autenticación**: Requerida (rol: docente)  
**Parámetros**:
- `dia_semana` (int): 0-6
- `hora_inicio` (time): HH:MM
- `hora_fin` (time): HH:MM

**Response**: JSON
```json
{
  "success": true,
  "message": "Disponibilidad agregada"
}
```

#### `POST /disponibilidad/eliminar/<int:id>`
**Descripción**: Eliminar horario disponible  
**Autenticación**: Requerida (rol: docente)  
**Response**: Redirect

#### `POST /bloque/agregar`
**Descripción**: Bloquear fecha/hora específica  
**Autenticación**: Requerida (rol: docente)  
**Parámetros**:
- `fecha` (date): YYYY-MM-DD
- `hora_inicio` (time, opcional): HH:MM
- `hora_fin` (time, opcional): HH:MM
- `motivo` (string, opcional)

**Response**: JSON

#### `POST /bloque/eliminar/<int:id>`
**Descripción**: Eliminar bloqueo  
**Autenticación**: Requerida (rol: docente)  
**Response**: Redirect

---

### Acceso a Clases

#### `GET /clase/<int:clase_id>/unirse`
**Descripción**: Acceso controlado a clase con validaciones  
**Autenticación**: Requerida  
**Flujo**:
1. Verificar que usuario pertenece a la clase
2. Validar permisos con `puede_acceder()`
3. Capturar enlace antes de posible regeneración
4. Registrar acceso con `registrar_acceso()`
5. Redirigir a Jitsi

**Código**:
```python
@main.route('/clase/<int:clase_id>/unirse')
@login_required
def unirse_clase(clase_id):
    clase = Clase.query.get_or_404(clase_id)
    
    # Determinar si es docente
    es_docente = (current_user.id == clase.docente_id or 
                  (hasattr(current_user, 'docente') and 
                   current_user.docente and 
                   current_user.docente.id == clase.docente_id))
    
    # Verificar pertenencia
    if not es_docente and clase.cliente_id != current_user.id:
        flash('No tienes acceso a esta clase', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Validar acceso
    puede_acceder, mensaje = clase.puede_acceder(current_user.id, es_docente)
    if not puede_acceder:
        flash(mensaje, 'warning')
        return redirect(url_for('main.detalle_clase', clase_id=clase.id))
    
    # Capturar link antes de registrar (puede regenerarse)
    link_para_esta_sesion = clase.link_jitsi
    
    # Registrar acceso
    clase.registrar_acceso(current_user.id, es_docente)
    
    # Redirigir a Jitsi
    return redirect(link_para_esta_sesion)
```

---

### Clases Especiales (Admin)

#### `GET/POST /admin/clases/crear`
**Descripción**: Crear clase especial con configuración avanzada  
**Autenticación**: Requerida (rol: admin)  
**Parámetros (POST)**:
- `cliente_id` (int)
- `docente_id` (int)
- `fecha_inicio` (datetime)
- `duracion` (int, minutos)
- `es_gratuita` (bool)
- `acceso_unico` (bool)
- `regenerar_link` (bool)
- `notas_admin` (text)

**Características**:
- Permite crear clases sin cobro
- Control granular de seguridad de enlaces
- Notas administrativas internas

---

## Sistema de Disponibilidad

### Lógica de Validación

#### Verificar Disponibilidad de Docente
```python
def docente_disponible(docente_id, fecha_hora):
    """
    Verifica si docente está disponible en fecha/hora específica
    
    Args:
        docente_id (int)
        fecha_hora (datetime)
    
    Returns:
        bool: True si está disponible
    """
    # 1. Verificar bloques específicos (tienen precedencia)
    bloques = BloqueNoDisponible.query.filter_by(
        docente_id=docente_id
    ).filter(
        BloqueNoDisponible.fecha == fecha_hora.date()
    ).all()
    
    for bloque in bloques:
        if bloque.incluye_fecha_hora(fecha_hora):
            return False  # Bloqueado
    
    # 2. Verificar disponibilidad recurrente
    dia_semana = fecha_hora.weekday()  # 0=Lunes, 6=Domingo
    if dia_semana == 6:  # Ajustar: 0=Domingo
        dia_semana = 0
    else:
        dia_semana += 1
    
    disponibilidades = DisponibilidadDocente.query.filter_by(
        docente_id=docente_id,
        dia_semana=dia_semana,
        activo=True
    ).all()
    
    hora = fecha_hora.time()
    for disp in disponibilidades:
        if disp.hora_inicio <= hora <= disp.hora_fin:
            return True  # Disponible
    
    return False  # No hay disponibilidad configurada
```

### Tarea Celery Recomendada
```python
@celery.task
def validar_disponibilidad_clases():
    """
    Tarea programada para validar que clases agendadas
    coincidan con disponibilidad del docente
    """
    clases_proximas = Clase.query.filter(
        Clase.fecha_inicio > datetime.utcnow(),
        Clase.fecha_inicio < datetime.utcnow() + timedelta(days=7),
        Clase.clase_cerrada == False
    ).all()
    
    for clase in clases_proximas:
        if not docente_disponible(clase.docente_id, clase.fecha_inicio):
            # Enviar alerta al admin
            enviar_alerta_conflicto_disponibilidad(clase)
```

---

## Control de Acceso a Clases

### Flujo de Acceso Completo

```mermaid
graph TD
    A[Usuario hace click en "Unirse"] --> B{¿Autenticado?}
    B -->|No| C[Redirect a Login]
    B -->|Sí| D{¿Pertenece a clase?}
    D -->|No| E[Error 403]
    D -->|Sí| F{¿Clase cerrada?}
    F -->|Sí| G[Mensaje: Clase cerrada]
    F -->|No| H{¿Dentro de ventana temporal?}
    H -->|< 15 min antes| I[Mensaje: Disponible en X min]
    H -->|> fin programado| J[Mensaje: Clase finalizada]
    H -->|Sí| K{¿Acceso único activo?}
    K -->|No| M[Registrar acceso]
    K -->|Sí| L{¿Ya accedió antes?}
    L -->|Sí| N[Mensaje: Acceso ya utilizado]
    L -->|No| M
    M --> O{¿Regenerar link?}
    O -->|Sí| P[Generar nuevo enlace]
    O -->|No| Q[Usar enlace actual]
    P --> R[Redirect a Jitsi]
    Q --> R
```

### Ventana Temporal Configurable
```python
# En models.py, método puede_acceder()
margen_antes = timedelta(minutes=15)  # Configurable

# Para cambiar el margen, modificar este valor
# Opciones recomendadas:
# - 10 minutos: Clases muy estructuradas
# - 15 minutos: Balance (actual)
# - 30 minutos: Clases informales
```

### Regeneración de Enlaces
**Escenarios de uso**:
1. **Acceso único SIN regeneración**: Enlace se desactiva después del primer uso
2. **Acceso único CON regeneración**: Nuevo enlace se genera para cada acceso
3. **Acceso múltiple**: Mismo enlace usado múltiples veces

**Configuración por clase**:
```python
# Clase normal (creada por usuario)
clase.acceso_unico = True
clase.regenerar_link = False

# Clase especial admin (máxima flexibilidad)
clase.acceso_unico = False  # o True
clase.regenerar_link = True  # Se regenera siempre
```

---

## Seguridad

### Protección de Enlaces Jitsi

**Problema original**: Enlaces Jitsi enviados por email podían ser accedidos directamente sin validaciones.

**Solución implementada**:
1. **Endpoint de Control**: `/clase/<id>/unirse` como único punto de acceso
2. **Sin Enlaces Directos**: Emails usan `url_for('main.unirse_clase', clase_id=X)`
3. **Validación Backend**: Todas las reglas de negocio verificadas antes de redirect
4. **Registro de Accesos**: Timestamp y contador de cada intento

**Templates actualizados**:
```jinja2
{# Antes (INSEGURO) #}
<a href="{{ clase.link_jitsi }}">Unirse a clase</a>

{# Después (SEGURO) #}
<a href="{{ url_for('main.unirse_clase', clase_id=clase.id, _external=True) }}">
    Unirse a clase
</a>
```

### Autenticación y Autorización
- **Flask-Login**: Gestión de sesiones
- **2FA**: Autenticación de dos factores opcional
- **RBAC**: Roles (admin, docente, cliente)
- **CSRF Protection**: Token en formularios

### Variables de Entorno Sensibles
```bash
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@db:5432/aulavirtual_db
JITSI_DOMAIN=meet.jit.si
MAIL_USERNAME=<email>
MAIL_PASSWORD=<app-password>
STRIPE_SECRET_KEY=<sk_live_xxx>
```

**Nunca commitear** `.env` a Git. Usar `.env.example` como plantilla.

---

## Despliegue

### Requisitos del Servidor
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM mínimo (4GB recomendado)
- 20GB espacio en disco
- Puertos 80, 443, 5000, 5432, 6379 disponibles

### Instalación Inicial
```bash
# Clonar repositorio
git clone <url-repo> /root/aulavirtual
cd /root/aulavirtual

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con valores reales

# Construir e iniciar
docker-compose up -d --build

# Verificar
docker ps
docker logs aulavirtual_web
```

### Migración de Base de Datos
```bash
# Conectar al contenedor de BD
docker exec -i aulavirtual_db psql -U postgres -d aulavirtual_db

# Ejecutar script SQL
-- Ver CHANGELOG.md para SQL completo
```

### Actualización de Código
```bash
# Opción 1: Con Docker Compose (recomendado)
cd /root/aulavirtual
git pull origin main  # O copiar archivos manualmente
docker exec -i aulavirtual_web find /app -name "*.pyc" -delete
docker-compose down
docker-compose up -d

# Opción 2: Solo reiniciar contenedor (cambios menores)
docker cp app/routes.py aulavirtual_web:/app/app/routes.py
docker exec -i aulavirtual_web find /app -name "*.pyc" -delete
docker restart aulavirtual_web

# Verificar logs
docker logs --tail 30 aulavirtual_web
```

### Backup de Base de Datos
```bash
# Backup completo
docker exec aulavirtual_db pg_dump -U postgres aulavirtual_db > backup_$(date +%Y%m%d).sql

# Restaurar
docker exec -i aulavirtual_db psql -U postgres aulavirtual_db < backup_20260306.sql
```

---

## Mantenimiento

### Monitoreo
```bash
# Estado de contenedores
docker ps
docker stats

# Logs en tiempo real
docker logs -f aulavirtual_web
docker logs -f aulavirtual_nginx

# Espacio en disco
docker system df
docker volume ls
```

### Limpieza de Cache Python
```bash
# Si hay comportamiento extraño después de actualizar código
docker exec -i aulavirtual_web find /app -type f -name "*.pyc" -delete
docker exec -i aulavirtual_web find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
docker restart aulavirtual_web
```

### Tareas Celery Recomendadas
```python
# En app/tasks.py

@celery.task
def cerrar_clases_finalizadas():
    """Ejecutar cada 5 minutos"""
    clases = Clase.query.filter(
        Clase.fecha_fin < datetime.utcnow(),
        Clase.clase_cerrada == False
    ).all()
    for clase in clases:
        clase.cerrar_automaticamente()

@celery.task
def enviar_recordatorios_15min():
    """Ejecutar cada minuto"""
    tiempo_objetivo = datetime.utcnow() + timedelta(minutes=15)
    clases = Clase.query.filter(
        Clase.fecha_inicio.between(tiempo_objetivo, tiempo_objetivo + timedelta(minutes=1))
    ).all()
    for clase in clases:
        enviar_email_recordatorio(clase)
```

### Health Check
```bash
# Endpoint de salud (implementar)
curl http://localhost:5000/health

# Verificar BD
docker exec aulavirtual_db psql -U postgres -d aulavirtual_db -c "SELECT 1;"

# Verificar Redis
docker exec aulavirtual_redis redis-cli ping
```

---

## Solución de Problemas

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para lista completa.

### Error: NameError 'timedelta' not defined
```bash
# Síntoma: Error 500 en /clase/<id>/unirse
# Causa: Import faltante o cache de .pyc

# Solución:
docker exec -i aulavirtual_web grep "from datetime import" /app/app/models.py
# Debe mostrar: from datetime import datetime, timedelta

# Si falta, agregar import y limpiar cache:
docker exec -i aulavirtual_web find /app -name "*.pyc" -delete
docker-compose down && docker-compose up -d
```

### Error: BloqueNoDisponible has no attribute 'fecha'
```bash
# Síntoma: Error 500 en /disponibilidad
# Causa: Discrepancia modelo vs tabla BD

# Verificar estructura:
docker exec aulavirtual_db psql -U postgres -d aulavirtual_db -c "\d bloques_no_disponibles"

# Debe tener columnas: fecha (date), hora_inicio (time), hora_fin (time)
# NO: fecha_inicio (timestamp), fecha_fin (timestamp)
```

---

## Referencias

- [Documentación Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Jitsi Meet API](https://jitsi.github.io/handbook/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Gunicorn](https://docs.gunicorn.org/)

---

**Versión**: 2.1.0  
**Última Actualización**: 6 de marzo de 2026  
**Autor**: Equipo Técnico Aula Virtual
