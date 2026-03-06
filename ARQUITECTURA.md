# 🏗️ ARQUITECTURA DE AULA VIRTUAL

**Versión**: 1.0.0  
**Fecha**: Marzo 2026  
**Tipo**: Aplicación Web con Arquitectura de Microservicios

---

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Diagrama de Arquitectura](#diagrama-de-arquitectura)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Flujo de Datos](#flujo-de-datos)
5. [Seguridad](#seguridad)
6. [Escalabilidad](#escalabilidad)

---

## 🎯 VISIÓN GENERAL

Aula Virtual es una plataforma educativa que conecta estudiantes con docentes para clases virtuales. La arquitectura está diseñada para ser:

- **Escalable**: Puede crecer horizontalmente
- **Segura**: Múltiples capas de seguridad
- **Mantenible**: Código modular y bien documentado
- **Resiliente**: Tolerante a fallos

### Arquitectura de Capas

```
┌────────────────────────────────────────────────────┐
│                  CAPA DE PRESENTACIÓN              │
│           (Nginx + Templates Jinja2)               │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│              CAPA DE APLICACIÓN                    │
│         (Flask + Gunicorn + API REST)              │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│             CAPA DE NEGOCIO                        │
│    (Lógica de Negocio + Workers Celery)           │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│            CAPA DE DATOS                           │
│      (PostgreSQL + Redis + Archivos)               │
└────────────────────────────────────────────────────┘
```

---

## 📐 DIAGRAMA DE ARQUITECTURA

### Arquitectura Completa

```
                                                    Internet
                                                       │
                                                       ↓
                                     ┌─────────────────────────────┐
                                     │   FIREWALL / LOAD BALANCER  │
                                     └─────────────────────────────┘
                                                       │
                                                       ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                                 NGINX (Proxy Inverso)                         │
│  • SSL/TLS Termination                                                       │
│  • Rate Limiting                                                             │
│  • Static Files                                                              │
│  • Compresión Gzip                                                           │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↙                 ↓             ↘
                        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
                        │   Web App    │   │   Web App    │   │   Web App    │
                        │   (Flask)    │   │   (Flask)    │   │   (Flask)    │
                        │   Container  │   │   Container  │   │   Container  │
                        └──────────────┘   └──────────────┘   └──────────────┘
                                     ↘                 ↓             ↙
                                         ┌──────────────────────┐
                                         │    Redis (Cache)     │
                                         │  • Sesiones          │
                                         │  • Cola de mensajes  │
                                         └──────────────────────┘
                                                       │
                          ┌────────────────────────────┴────────────────────────┐
                          ↓                                                     ↓
              ┌──────────────────────┐                         ┌──────────────────────┐
              │  PostgreSQL          │                         │  Celery Workers      │
              │  • Usuarios          │                         │  • Emails            │
              │  • Clases            │                         │  • Tareas async      │
              │  • Pagos             │                         │  • Reportes          │
              └──────────────────────┘                         └──────────────────────┘
                          │
                          ↓
              ┌──────────────────────┐
              │  File Storage        │
              │  • Avatares          │
              │  • Materiales        │
              │  • Backups           │
              └──────────────────────┘

                                     SERVICIOS EXTERNOS
                          ┌────────────────────────────────────┐
                          │  • Stripe (Pagos)                  │
                          │  • Jitsi Meet (Videollamadas)      │
                          │  • SendGrid/SMTP (Emails)          │
                          └────────────────────────────────────┘
```

---

## 🔧 COMPONENTES DEL SISTEMA

### 1. NGINX (Proxy Inverso)

**Función**: Servidor web y proxy inverso

**Responsabilidades**:
- Terminar conexiones SSL/TLS
- Servir archivos estáticos
- Balanceo de carga
- Rate limiting (prevención de abuso)
- Compresión de respuestas
- Headers de seguridad

**Características**:
- Puerto 80 (HTTP) y 443 (HTTPS)
- Configuración personalizada en `nginx/nginx.conf`
- Certificados SSL en `nginx/ssl/`

**Flujo de Peticiones**:
```
Cliente → Nginx (80/443) → Gunicorn (5000) → Flask App
```

---

### 2. FLASK (Framework Web)

**Función**: Framework de aplicación web en Python

**Estructura de la Aplicación**:

```
app/
├── __init__.py          # Inicialización de la app Flask
├── models.py            # Modelos de base de datos (SQLAlchemy)
├── routes.py            # Rutas principales de la aplicación
├── auth.py              # Autenticación y registro
├── admin.py             # Panel de administración
├── api.py               # API REST
├── tasks.py             # Tareas asíncronas (Celery)
├── email.py             # Envío de emails
├── utils.py             # Funciones auxiliares
├── static/              # Archivos estáticos (CSS, JS, imágenes)
└── templates/           # Templates HTML (Jinja2)
```

**Módulos Principales**:

#### `app/__init__.py`
- **Función**: Inicializar la aplicación Flask
- **Responsabilidades**:
  - Configurar Flask
  - Inicializar extensiones (SQLAlchemy, Flask-Login, etc.)
  - Registrar Blueprints
  - Configurar manejo de errores

#### `app/models.py`
- **Función**: Definir modelos de datos
- **Modelos**:
  - `Usuario`: Usuarios del sistema (estudiantes, docentes, admins)
  - `Docente`: Información adicional de docentes
  - `Clase`: Clases programadas
  - `Pago`: Transacciones de pago
  - `Resena`: Reseñas de clases
  - `Material`: Materiales educativos
  - `Calificacion`: Calificaciones de clases
  - `Asistencia`: Control de asistencia
  - `Notificacion`: Notificaciones del sistema

#### `app/routes.py`
- **Función**: Rutas principales de la aplicación
- **Endpoints principales**:
  - `/` - Página de inicio
  - `/dashboard` - Panel del usuario
  - `/docentes` - Listado de docentes
  - `/reservar-clase/<id>` - Reservar clase
  - `/mis-clases` - Clases del usuario
  - `/clase/<id>` - Detalle de clase
  - `/perfil` - Perfil del usuario

#### `app/auth.py`
- **Función**: Sistema de autenticación
- **Funcionalidades**:
  - Registro de usuarios
  - Login/Logout
  - Recuperación de contraseña
  - Autenticación de dos factores (2FA)
  - Códigos de respaldo

#### `app/admin.py`
- **Función**: Panel de administración
- **Funcionalidades**:
  - Gestión de usuarios
  - Verificación de docentes
  - Gestión de clases
  - Gestión de pagos
  - Reportes y estadísticas

#### `app/api.py`
- **Función**: API REST para integraciones
- **Endpoints**:
  - `/api/health` - Estado del sistema
  - `/api/docentes` - CRUD de docentes
  - `/api/clases` - CRUD de clases
  - `/api/materiales` - CRUD de materiales
  - `/api/estadisticas` - Estadísticas generales

#### `app/tasks.py`
- **Función**: Tareas asíncronas con Celery
- **Tareas**:
  - Envío de emails
  - Generación de reportes
  - Procesamiento de pagos
  - Recordatorios de clases

#### `app/email.py`
- **Función**: Envío de correos electrónicos
- **Tipos de emails**:
  - Confirmación de registro
  - Confirmación de clase
  - Recordatorio de clase
  - Aprobación de docente
  - Reporte diario (admin)

#### `app/utils.py`
- **Función**: Funciones auxiliares
- **Utilidades**:
  - Validación de archivos
  - Generación de slugs
  - Formato de fechas y monedas
  - Helpers para templates

---

### 3. GUNICORN (Servidor WSGI)

**Función**: Servidor de aplicaciones Python

**Características**:
- Maneja múltiples workers
- Configurado en puerto 5000
- Workers: CPU cores × 2 + 1
- Timeout: 60 segundos

**Configuración** (en `Dockerfile`):
```bash
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --timeout 60 \
         run:app
```

---

### 4. POSTGRESQL (Base de Datos)

**Función**: Base de datos relacional principal

**Esquema de Datos**:

```sql
-- Tabla: usuarios
usuarios
├── id (PK)
├── nombre
├── email (UNIQUE)
├── password_hash
├── rol (admin/docente/cliente)
├── telefono
├── avatar_url
├── fecha_registro
├── ultimo_acceso
├── activo
├── totp_secret (2FA)
├── is_2fa_enabled
└── backup_codes

-- Tabla: docentes (extiende usuarios)
docentes
├── id (PK)
├── usuario_id (FK → usuarios)
├── especialidad
├── biografia
├── titulo_profesional
├── experiencia_anos
├── tarifa_por_hora
├── disponibilidad (JSON)
├── calificacion_promedio
├── total_clases
├── verificado
└── documento_verificacion

-- Tabla: clases
clases
├── id (PK)
├── cliente_id (FK → usuarios)
├── docente_id (FK → docentes)
├── titulo
├── descripcion
├── fecha_inicio
├── fecha_fin
├── duracion_minutos
├── link_jitsi
├── estado (pendiente/confirmada/cancelada/completada)
├── monto
└── notas

-- Tabla: pagos
pagos
├── id (PK)
├── clase_id (FK → clases)
├── monto
├── metodo_pago
├── stripe_payment_intent_id
├── estado (pendiente/completado/fallido/reembolsado)
├── fecha_pago
└── detalles (JSON)

-- Relaciones entre tablas:
usuarios 1 → N docentes
usuarios 1 → N clases (como cliente)
docentes 1 → N clases (como docente)
clases 1 → 1 pagos
clases 1 → N resenas
clases 1 → N materiales
```

**Puerto**: 5432  
**Volumen persistente**: `postgres_data`

---

### 5. REDIS (Cache y Cola de Mensajes)

**Función**: Base de datos en memoria

**Usos**:
1. **Cache de sesiones**: Almacena sesiones de usuarios
2. **Cola de mensajes**: Para Celery (tareas asíncronas)
3. **Cache de datos**: Resultados de consultas frecuentes
4. **Rate limiting**: Control de peticiones por usuario

**Configuración**:
- Puerto: 6379
- URL: `redis://redis:6379/0`
- TTL de sesiones: 24 horas

---

### 6. CELERY (Tareas Asíncronas)

**Función**: Sistema de tareas en segundo plano

**Arquitectura de Celery**:

```
┌─────────────────┐
│  Flask App      │
│  (Productor)    │
└────────┬────────┘
         │
         ↓ Encola tarea
┌─────────────────┐
│     Redis       │
│  (Message Broker)│
└────────┬────────┘
         │
         ↓ Consume tarea
┌─────────────────┐
│ Celery Worker   │
│  (Consumidor)   │
└─────────────────┘
```

**Tareas Configuradas**:

1. **Envío de Emails Asíncrono**:
   - Confirmaciones
   - Recordatorios
   - Notificaciones

2. **Tareas Programadas** (Celery Beat):
   - Recordatorios de clases (30 min antes)
   - Reportes diarios (administrador)
   - Limpieza de sesiones expiradas

---

## 🚀 ESTADO ACTUAL DEL DESPLIEGUE

### Información del Servidor de Producción

**Servidor**: 192.168.1.6 (LXR-AUVI01)
- **Sistema Operativo**: Linux (CentOS/RHEL)
- **Usuario**: root
- **Ruta del proyecto**: `/root/aulavirtual` (importante: lowercase)
- **Commit actual**: `d5e9f89`
- **Branch**: main
- **Repositorio**: https://github.com/daviddiaz-bot/aulavirtual.git

### Configuración de Contenedores

**5 Containers en ejecución**:

1. **aulavirtual_nginx** (nginx:1.25-alpine)
   - Puertos: 80:80, 443:443
   - Función: Proxy inverso + archivos estáticos
   - Config: `/root/aulavirtual/nginx/nginx.conf`
   - Estado: ✅ Funcionando

2. **aulavirtual_web** (custom Flask image)
   - Puerto interno: 5000
   - Workers Gunicorn: 4
   - Framework: Flask 2.3+
   - Estado: ✅ Funcionando

3. **aulavirtual_db** (postgres:15-alpine)
   - Puerto: 5432
   - Base de datos: `aulavirtual_db`
   - Usuario/Password: `postgres` / `AulaVirtual2026!`
   - Volumen: `postgres_data:/var/lib/postgresql/data`
   - Estado: ✅ Funcionando

4. **aulavirtual_redis** (redis:7-alpine)
   - Puerto: 6379
   - Modo: AOF (Append Only File)
   - Volumen: `redis_data:/data`
   - Estado: ✅ Funcionando

5. **aulavirtual_celery** (mismo image que web)
   - Worker Celery para tareas asíncronas
   - Conectado a Redis para cola
   - Estado: ✅ Funcionando

### Variables de Entorno (.env)

```bash
# Configuración actual en /root/aulavirtual/.env
FLASK_ENV=production
SECRET_KEY=(configurado)
DATABASE_URL=postgresql://postgres:postgres@db:5432/aulavirtual
REDIS_URL=redis://redis:6379/0

# Email SMTP (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=davideduardo2010@gmail.com
MAIL_PASSWORD=fpybippzzrkdozll
MAIL_DEFAULT_SENDER=davideduardo2010@gmail.com

# Sesión (CRÍTICO para HTTP)
SESSION_COOKIE_SECURE=False

# Jitsi Meet
JITSI_SERVER=meet.jit.si

# Stripe (PENDIENTE CONFIGURAR)
STRIPE_PUBLISHABLE_KEY=(vacío)
STRIPE_SECRET_KEY=(vacío)
STRIPE_WEBHOOK_SECRET=(vacío)
```

### Arquitectura Real Desplegada

```
                    Internet (HTTP - Puerto 80)
                                ↓
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Proxy Inverso)                │
│  • Maneja peticiones HTTP en puerto 80                  │
│  • Proxy pass a Gunicorn en puerto 5000                 │
│  • Sirve archivos estáticos desde /app/static           │
│  • Sin SSL configurado (HTTP only)                      │
└───────────────────────┬─────────────────────────────────┘
                        ↓ proxy_pass http://web:5000
┌─────────────────────────────────────────────────────────┐
│            Gunicorn WSGI Server (4 workers)             │
│  • Ejecuta aplicación Flask                             │
│  • Workers: 4 procesos                                  │
│  • Timeout: 60 segundos                                 │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   Flask Application                      │
│  • Framework: Flask 2.3+                                │
│  • Config: ProductionConfig                             │
│  • Debug: False                                         │
│  • Logging: INFO level                                  │
└───────────────────────┬─────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│   PostgreSQL 15  │          │     Redis 7      │
│                  │          │                  │
│ • DB: aulavirtual_db        │ • Cache sesiones │
│ • Port: 5432     │          │ • Cola Celery    │
│ • User: postgres │          │ • Port: 6379     │
│ • Persistent data│          │ • AOF enabled    │
└──────────────────┘          └────────┬─────────┘
                                       ↓
                             ┌──────────────────┐
                             │  Celery Worker   │
                             │  • Emails        │
                             │  • Tareas async  │
                             │  • Reportes      │
                             └──────────────────┘
```

### Flujo de Petición HTTP

```
1. Cliente HTTP → http://192.168.1.6/dashboard
2. Nginx recibe en :80
3. Nginx hace proxy_pass a http://web:5000/dashboard
4. Gunicorn recibe la petición
5. Gunicorn asigna a worker disponible
6. Worker ejecuta código Flask
7. Flask consulta PostgreSQL si necesita datos
8. Flask consulta Redis para sesión del usuario
9. Flask renderiza template con Jinja2
10. HTML se devuelve a Gunicorn
11. Gunicorn devuelve a Nginx
12. Nginx devuelve al cliente
```

### Configuración de Sesiones (CRÍTICO)

**Problema Resuelto**: Login requería checkbox "Recordar"

**Causa**: SESSION_COOKIE_SECURE=True en servidor HTTP

**Solución implementada**:
1. `.env` configurado con `SESSION_COOKIE_SECURE=False`
2. `config.py` lee correctamente la variable
3. `docker-compose.yml` pasa la variable al container:
   ```yaml
   environment:
     - SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-False}
   ```

**Estado**: ✅ Resuelto en commit `d5e9f89` (puede requerir limpieza de cache)

**Verificación**:
```bash
# Verificar en container
docker-compose exec web printenv | grep SESSION_COOKIE_SECURE
# Output esperado: SESSION_COOKIE_SECURE=False

# Verificar en Flask config
docker-compose exec web python -c "from app import create_app; app = create_app(); print(app.config['SESSION_COOKIE_SECURE'])"
# Output esperado: False
```

### Problemas Resueltos (7 commits)

#### Commit ee11efc: Templates Admin Faltantes
- Creados 6 templates de administración
- Archivos: docentes.html, clases.html, pagos.html, reportes.html, configuracion.html, retiros.html

#### Commit c01c4a8: Atributos de Modelo
- Fix: `tarifa_hora` → `precio_hora`
- Fix: `materias` → `especialidad`

#### Commit 1a3f241: Endpoints Incorrectos
- Fix: `docentes.perfil` → `main.perfil_docente`
- Fix: Paginación en retiros

#### Commit 1c0d5dd: Código Duplicado
- Eliminadas 187 líneas de función `mis_materiales()` duplicada
- Fix: Upload de materiales funcionando

#### Commits c221ed6 + 5883643: Validación Templates
- Agregada validación `{% if material.docente %}`
- Fix parámetro: `user_id` → `usuario_id`

#### Commit 9d2036d: Descarga de Materiales
- Path absoluto con `current_app.root_path`
- Compatibilidad Flask 2.x (download_name)

#### Commits e26917f + d5e9f89: SESSION_COOKIE_SECURE
- Eliminado hardcoded en ProductionConfig
- Agregado a docker-compose.yml environment

**Ver detalles**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### Funcionalidades Probadas

✅ **Autenticación**
- Login funciona (requiere limpiar cache Python para fix final)
- Registro de usuarios
- Logout

✅ **Panel Admin**
- Acceso correcto con permisos admin
- Gestión de docentes (listado, aprobación)
- Gestión de materiales (listado, detalle, descarga)
- Templates completos y funcionando

✅ **Gestión de Materiales**
- Docentes pueden subir PDFs
- Límite de 10 materiales funciona correctamente
- Descarga de materiales funciona
- Vista de detalle con validaciones

✅ **Sistema de Base de Datos**
- PostgreSQL operativo
- Modelos correctos (Usuario, Docente, Clase, Pago, Material, etc.)
- Migraciones aplicadas

✅ **Cache y Sesiones**
- Redis funcionando
- Sesiones guardadas en Redis
- Celery conectado a Redis

### Pendientes de Configurar

🔴 **Limpieza Cache Python** (URGENTE)
```bash
docker-compose exec web find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
docker-compose exec web find /app -type f -name "*.pyc" -delete
docker-compose restart web
```

🟡 **Email SMTP** (Gmail)
- Contraseña configurada: `fpybippzzrkdozll`
- Estado: Configurado, validez desconocida
- Probar envío: Ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#error-email)

🟡 **Stripe Payments** (NO CONFIGURADO)
- Variables vacías en .env:
  - STRIPE_PUBLISHABLE_KEY
  - STRIPE_SECRET_KEY
  - STRIPE_WEBHOOK_SECRET
- Obtener de: https://dashboard.stripe.com/apikeys
- Configurar webhook en: https://dashboard.stripe.com/webhooks

### Testing Pendiente

- [ ] Login sin checkbox "recordar" (después de limpiar cache)
- [ ] Registro completo de usuario nuevo
- [ ] Registro y verificación de docente
- [ ] Búsqueda de docentes
- [ ] Reservar y pagar clase (requiere Stripe)
- [ ] Videollamada Jitsi
- [ ] Sistema de reseñas
- [ ] Envío de emails (bienvenida, confirmación, recordatorio)
- [ ] Retiros de fondos de docentes
- [ ] Reportes de administración
- [ ] Reset de password

### Comandos de Gestión

**Ver logs**:
```bash
docker-compose logs -f web
docker-compose logs --tail=100 web
docker-compose logs web | grep ERROR
```

**Reiniciar servicios**:
```bash
docker-compose restart web      # Solo aplicación
docker-compose restart           # Todos los servicios
```

**Acceso a containers**:
```bash
docker-compose exec web bash    # Shell en container web
docker-compose exec db psql -U postgres -d aulavirtual_db  # PostgreSQL
```

**Actualizar código**:
```bash
cd /root/aulavirtual
git fetch origin
git reset --hard origin/main  # ⚠️ Borra cambios locales
docker-compose down
docker-compose up -d
```

**Backup de base de datos**:
```bash
docker-compose exec db pg_dump -U postgres aulavirtual_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore de base de datos**:
```bash
docker-compose exec -T db psql -U postgres aulavirtual_db < backup_20260306_120000.sql
```

### Monitoreo

**Espacio en disco**:
```bash
df -h
du -sh /root/aulavirtual
docker system df
```

**Recursos de containers**:
```bash
docker stats
```

**Estado de servicios**:
```bash
docker-compose ps
systemctl status docker
```

### Seguridad

**Configurado**:
- ✅ Passwords hasheados (bcrypt)
- ✅ Sesiones seguras en Redis
- ✅ CSRF protection (Flask-WTF)
- ✅ SQL Injection protection (SQLAlchemy ORM)
- ✅ XSS protection (Jinja2 autoescape)

**Pendiente**:
- 🔴 SSL/HTTPS con Let's Encrypt
- 🟡 Firewall configuración (iptables/firewalld)
- 🟡 Rate limiting en Nginx
- 🟡 Fail2ban para SSH
- 🟡 Regular security audits

### Backups

**Configurado**:
- Volúmenes Docker persistentes
- Directorio `/root/aulavirtual/backups` montado en container db

**Recomendado configurar**:
```bash
# Cron job para backups diarios
# Agregar a crontab: crontab -e
0 2 * * * cd /root/aulavirtual && docker-compose exec -T db pg_dump -U postgres aulavirtual_db > backups/backup_$(date +\%Y\%m\%d).sql
0 3 * * * find /root/aulavirtual/backups -name "backup_*.sql" -mtime +7 -delete
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

- **[INSTALACION_COMPLETA.md](./INSTALACION_COMPLETA.md)**: Guía paso a paso de instalación desde cero
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)**: Solución de problemas comunes con detalles técnicos
- **[INICIO_RAPIDO.md](./INICIO_RAPIDO.md)**: Guía rápida para desarrollo
- **[JITSI_MEET.md](./JITSI_MEET.md)**: Configuración de videollamadas
- **[Manual de Usuario](./docs/index.html)**: Documentación completa para usuarios y administradores

---

**Última actualización**: 6 de Marzo 2026  
**Versión**: 1.0.0  
**Maintainer**: David Diaz (davideduardo2010@gmail.com)

3. **Procesamiento de Pagos**:
   - Verificación de pagos pendientes
   - Actualización de estados

**Configuración** (en `config.py`): ```python
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
```

---

### 7. DOCKER & DOCKER COMPOSE (Containerización)

**Función**: Orquestación de contenedores

**Contenedores Definidos** (en `docker-compose.yml`):

```yaml
services:
  # Base de datos
  db:
    image: postgres:15-alpine
    ports: 5432:5432
    volumes: postgres_data
    
  # Cache
  redis:
    image: redis:7-alpine
    ports: 6379:6379
    
  # Aplicación web
  web:
    build: .
    ports: 5000:5000
    depends_on: [db, redis]
    
  # Proxy inverso
  nginx:
    image: nginx:1.25-alpine
    ports: 80:80, 443:443
    depends_on: [web]
    
  # Workers
  celery_worker:
    build: .
    command: celery worker
    depends_on: [redis, db]
```

**Ventajas**:
- Entorno consistente en desarrollo y producción
- Fácil escalamiento horizontal
- Aislamiento de servicios
- Despliegue rápido

---

## 🔄 FLUJO DE DATOS

### Flujo de Reserva de Clase

```
1. Cliente → [Nginx] → [Flask] → Ver lista de docentes
                                   ↓
                            [PostgreSQL]
                                   ↓
2. Cliente selecciona docente → [Flask] → Formulario de reserva
                                   ↓
3. Cliente completa formulario → [Flask] → Crear clase (pendiente)
                                   ↓
                            [PostgreSQL] (clase guardada)
                                   ↓
4. Cliente → [Flask] → Página de pago
           ↓
    [Stripe API] → Procesar pago
           ↓
5. Webhook ← [Stripe] → [Flask] → Actualizar estado de clase
                          ↓
                   [PostgreSQL] (clase confirmada)
                          ↓
                   [Celery] → Enviar emails de confirmación
                          ↓
                   [SMTP] → Email a cliente y docente
```

### Flujo de Videollamada (Jitsi Meet)

```
1. Sistema crea clase → Genera link único de Jitsi
                        format: https://meet.jit.si/clase-{uuid}
                        ↓
2. Clase confirmada → Link disponible en detalle de clase
                        ↓
3. Usuario hace click → Nueva pestaña con Jitsi Meet
                        ↓
4. Jitsi Meet → Solicita permisos de cámara/micrófono
                        ↓
5. Usuarios en sala → Videollamada en tiempo real
```

---

## 🔒 SEGURIDAD

### Capas de Seguridad

#### 1. Capa de Red (Nginx)
- **SSL/TLS**: Encriptación de datos en tránsito
- **Rate Limiting**: Protección contra ataques DDoS
- **Headers de Seguridad**:
  - `X-Frame-Options`: Previene clickjacking
  - `X-Content-Type-Options`: Previene MIME sniffing
  - `X-XSS-Protection`: Protección XSS
  - `Strict-Transport-Security`: Forzar HTTPS

#### 2. Capa de Aplicación (Flask)
- **Autenticación**: Sistema de login con hash bcrypt
- **Autorización**: Control de acceso por roles
- **2FA (Opcional)**: TOTP con códigos de respaldo
- **CSRF Protection**: Tokens en formularios
- **SQL Injection**: Protección con SQLAlchemy ORM
- **XSS**: Escapado automático en templates Jinja2

#### 3. Capa de Datos (PostgreSQL)
- **Encriptación**: Contraseñas con bcrypt
- **Usuarios limitados**: Usuario DB con permisos mínimos
- **Backup automático**: Snapshots diarios

#### 4. Secretos y Configuración
- **Variables de entorno**: Secretos fuera del código
- **SECRET_KEY**: Clave aleatoria de 32 bytes
- **API Keys**: Almacenadas en `.env`

---

## 📈 ESCALABILIDAD

### Escalamiento Horizontal

**Aplicación Web (Flask)**:
```yaml
# Aumentar replicas
services:
  web:
    scale: 3
```

**Workers (Celery)**:
```yaml
services:
  celery_worker:
    scale: 5
```

### Escalamiento Vertical

- **Base de Datos**: Aumentar CPU y RAM
- **Redis**: Configurar cluster
- **Nginx**: Optimizar workers

### Optimizaciones

1. **Cache**:
   - Redis para sesiones
   - Cache de consultas frecuentes
   - CDN para archivos estáticos

2. **Base de Datos**:
   - Índices en columnas frecuentes
   - Conexiones pool
   - Read replicas

3. **Archivos Estáticos**:
   - CDN (CloudFlare, AWS CloudFront)
   - Compresión Gzip
   - Versionado de assets

---

## 🔧 ARCHIVOS AUXILIARES

### config.py
**Función**: Configuración central de la aplicación

**Contenido**:
- Variables de entorno
- Configuración de Flask
- Configuración de base de datos
- Configuración de servicios externos (Stripe, SMTP, etc.)

### run.py
**Función**: Punto de entrada de la aplicación

**Contenido**:
- Inicializa la app Flask
- Ejecuta el servidor de desarrollo
- Maneja migraciones

### requirements.txt
**Función**: Dependencias de Python

**Paquetes principales**:
- Flask: Framework web
- SQLAlchemy: ORM para base de datos
- Flask-Login: Gestión de sesiones
- Stripe: Pagos
- Celery: Tareas asíncronas
- Gunicorn: Servidor WSGI

### docker-compose.yml
**Función**: Orquestación de servicios

**Define**:
- Servicios (web, db, redis, nginx, celery)
- Redes
- Volúmenes
- Variables de entorno

### Dockerfile
**Función**: Imagen de la aplicación

**Pasos**:
1. Base: Python 3.11 slim
2. Instalar dependencias del sistema
3. Copiar código
4. Instalar dependencias Python
5. Exponer puerto 5000

### crear_admin.py
**Función**: Script para crear usuario administrador

**Uso**:
```bash
python crear_admin.py
```

### verificar_sistema.py
**Función**: Script de verificación del sistema

**Verifica**:
- Conexión a bases de datos
- Existencia de tablas
- Variables de entorno
- Estructura de carpetas

---

## 🌐 INTEGRACIONES EXTERNAS

### Stripe (Procesamiento de Pagos)

**Flujo**:
```
Cliente → Frontend → Stripe.js → Stripe API
                                      ↓
                               Payment Intent
                                      ↓
                           Webhook → Backend
                                      ↓
                         Confirmar clase en DB
```

**Webhooks Escuchados**:
- `payment_intent.succeeded` - Pago exitoso
- `payment_intent.failed` - Pago fallido

### Jitsi Meet (Videollamadas)

**Integración**:
- **Tipo**: Iframe embed o enlace directo
- **Servidor**: meet.jit.si (público) o servidor propio
- **Seguridad**: Salas con nombres únicos (UUID)

**Formato de sala**:
```
https://meet.jit.si/clase-{uuid}
```

**Personalización**:
- Logo personalizado
- Colores corporativos
- Dominios propios (opcional)

### SMTP (Envío de Emails)

**Proveedores soportados**:
- Gmail (uso de aplicación)
- SendGrid
- Mailgun
- Amazon SES

**Configuración**:
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'tu-email@gmail.com'
MAIL_PASSWORD = 'contraseña-de-aplicacion'
```

---

## 📊 MONITOREO Y LOGGING

### Logs de Aplicación

**Ubicación**:
- Stdout/Stderr en Docker
- Archivos en `/var/log/aulavirtual/`

**Niveles**:
- DEBUG: Información detallada
- INFO: Eventos normales
- WARNING: Advertencias
- ERROR: Errores manejados
- CRITICAL: Errores críticos

### Métricas

**Recomendado implementar**:
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Sentry (error tracking)

---

## 🚀 DESPLIEGUE

### Entornos

1. **Desarrollo**: Local con Docker Compose
2. **Staging**: Servidor de pruebas
3. **Producción**: Servidor con SSL y dominio

### Proveedores Recomendados

- **VPS**: DigitalOcean, Linode, Vultr
- **Cloud**: AWS, Google Cloud, Azure
- **PaaS**: Heroku, Railway, Render

### Checklist de Producción

- [ ] Variables de entorno configuradas
- [ ] SSL/TLS configurado
- [ ] Backup automático de DB
- [ ] Monitoreo configurado
- [ ] Firewall configurado
- [ ] Dominio configurado
- [ ] Emails de notificación funcionando
- [ ] Webhooks de Stripe configurados

---

## 📚 REFERENCIAS TÉCNICAS

### Tecnologías Utilizadas

| Tecnología | Versión | Documentación |
|------------|---------|---------------|
| Python | 3.11+ | https://docs.python.org/3/ |
| Flask | 3.0+ | https://flask.palletsprojects.com/ |
| PostgreSQL | 15+ | https://www.postgresql.org/docs/ |
| Redis | 7+ | https://redis.io/docs/ |
| Nginx | 1.25+ | https://nginx.org/en/docs/ |
| Docker | 24+ | https://docs.docker.com/ |
| Celery | 5.3+ | https://docs.celeryproject.org/ |
| Stripe | API 2023+ | https://stripe.com/docs |

---

**Documento elaborado por**: Equipo de Desarrollo  
**Última actualización**: Marzo 2026  
**Próxima revisión**: Cada release mayor

---
