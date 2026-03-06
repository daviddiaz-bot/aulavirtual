# Registro de Cambios - Aula Virtual

## [Versión 2.1.0] - 2026-03-06

### 🎯 Nuevas Funcionalidades Principales

#### 1. Sistema de Disponibilidad Horaria para Docentes
- **Disponibilidad Recurrente**: Los docentes pueden definir su disponibilidad por días de la semana y rangos horarios
- **Bloques No Disponibles**: Capacidad para bloquear fechas/horas específicas (vacaciones, eventos personales)
- **Interfaz de Gestión**: Panel `/disponibilidad` para configurar horarios disponibles
- **Tablas de Base de Datos**:
  - `disponibilidad_docente`: Horarios recurrentes semanales
  - `bloques_no_disponibles`: Bloqueos específicos por fecha

#### 2. Control de Acceso Avanzado a Clases
- **Ventana de Acceso Temporal**: Las clases solo son accesibles 15 minutos antes del inicio y hasta el final programado
- **Acceso Único**: Implementación de acceso de un solo uso por enlace Jitsi
- **Seguimiento de Conexiones**: Registro de conexiones de estudiantes y docentes
- **Cierre Automático**: Las clases se cierran automáticamente después de su finalización
- **Campos Nuevos en Tabla `clases`**:
  - `clase_cerrada`: Estado de cierre de la clase
  - `fecha_cierre`: Timestamp del cierre
  - `acceso_unico`: Flag para forzar acceso único
  - `conexiones_estudiante`: Contador de accesos del estudiante
  - `conexiones_docente`: Contador de accesos del docente
  - `primera_conexion_estudiante`: Timestamp primer acceso estudiante
  - `primera_conexion_docente`: Timestamp primer acceso docente
  - `es_gratuita`: Marca clases sin costo
  - `creada_por_admin`: Identifica clases especiales del admin
  - `notas_admin`: Notas internas del administrador
  - `regenerar_link`: Flag para regeneración de enlaces
  - `link_jitsi_usado`: Control de uso del enlace

#### 3. Clases Especiales para Administradores
- **Creación sin Costo**: El admin puede crear clases gratuitas para casos especiales
- **Configuración Flexible**: Control sobre acceso único y regeneración de enlaces
- **Notas Administrativas**: Campo para documentar el propósito de la clase especial
- **Interfaz Dedicada**: Panel en `/admin/clases/crear` para crear clases especiales

#### 4. Seguridad de Enlaces Jitsi
- **Endpoint Controlado**: Ruta `/clase/<id>/unirse` con validación de acceso
- **Sin Enlaces Directos**: Los correos ya no envían links directos de Jitsi
- **Validaciones Temporales**: Verificación de horarios antes de permitir acceso
- **Regeneración Automática**: Los enlaces se regeneran después del primer uso (configurable)

### 🔧 Mejoras Técnicas

#### Modelos de Base de Datos
```python
# Nuevo modelo DisponibilidadDocente
- docente_id (FK)
- dia_semana (0-6, Domingo=0)
- hora_inicio, hora_fin (TIME)
- activo (boolean)

# Nuevo modelo BloqueNoDisponible
- docente_id (FK)
- fecha (DATE)
- hora_inicio, hora_fin (TIME, opcional)
- motivo (string)

# Clase (actualizado con 12 nuevos campos)
- Control de acceso temporal
- Seguimiento de conexiones
- Flags administrativos
```

#### Lógica de Negocio
- **`Clase.puede_acceder(usuario_id, es_docente)`**: Método que valida acceso con ventana temporal
- **`Clase.registrar_acceso(usuario_id, es_docente)`**: Registra accesos y regenera enlaces
- **`Clase.cerrar_automaticamente()`**: Cierra clase al finalizar el tiempo programado
- **Validación de timedelta**: Importación correcta de datetime para cálculos temporales

#### API y Rutas
- `/disponibilidad` [GET]: Ver y gestionar disponibilidad del docente
- `/disponibilidad/agregar` [POST]: Agregar horario disponible
- `/disponibilidad/eliminar/<id>` [POST]: Eliminar horario
- `/bloque/agregar` [POST]: Bloquear fecha/hora específica
- `/bloque/eliminar/<id>` [POST]: Eliminar bloqueo
- `/clase/<id>/unirse` [GET]: Acceso controlado a clase
- `/admin/clases/crear` [GET/POST]: Crear clase especial

### 📧 Actualizaciones de Templates

#### Emails Actualizados
- `confirmacion_clase.html`: Usa `url_for('main.unirse_clase')` en lugar de link directo
- `recordatorio_clase.html`: Usa `url_for('main.unirse_clase')` en lugar de link directo
- Seguridad mejorada: No se exponen enlaces Jitsi en correos

#### Vistas Admin
- `admin/clases.html`: Corrección de referencias de campos (docente_rel, cliente, monto)
- `admin/crear_clase.html`: Nuevo formulario para clases especiales
- Context variables: Agregado `now=datetime.utcnow()` para comparaciones

#### Vistas Docente
- `docentes/disponibilidad.html`: Nueva interfaz para gestión de horarios
- `calendario.html`: Integración con sistema de disponibilidad

### 🐛 Correcciones de Bugs

1. **Error de Cache de Python**: 
   - Problema: Archivos .pyc cacheados impedían actualización de código
   - Solución: Eliminación de cache + docker-compose down/up completo

2. **Sintaxis SQLAlchemy**:
   - Problema: Uso de sintaxis Django `fecha_fin__gte`
   - Solución: Cambiado a sintaxis correcta `BloqueNoDisponible.fecha >= date.today()`

3. **Discrepancia Modelo-BD**:
   - Problema: Modelo con `fecha_inicio/fecha_fin` (DateTime), BD con `fecha` (Date)
   - Solución: Alineación del modelo con estructura real de la tabla

4. **Import de timedelta**:
   - Problema: `NameError: name 'timedelta' is not defined`
   - Solución: `from datetime import datetime, timedelta` en models.py

5. **Contexto de Templates**:
   - Problema: Variables `now`, `datetime`, `timedelta` no disponibles en templates
   - Solución: Pasadas explícitamente en render_template

### 📊 Migraciones de Base de Datos

#### Script: `migrar_db_control_acceso.py`
Agrega 12 columnas a tabla `clases` y crea 2 tablas nuevas:
```sql
-- Columnas agregadas a 'clases'
ALTER TABLE clases ADD COLUMN clase_cerrada BOOLEAN DEFAULT FALSE;
ALTER TABLE clases ADD COLUMN fecha_cierre TIMESTAMP;
ALTER TABLE clases ADD COLUMN acceso_unico BOOLEAN DEFAULT TRUE;
ALTER TABLE clases ADD COLUMN conexiones_estudiante INTEGER DEFAULT 0;
ALTER TABLE clases ADD COLUMN conexiones_docente INTEGER DEFAULT 0;
ALTER TABLE clases ADD COLUMN primera_conexion_estudiante TIMESTAMP;
ALTER TABLE clases ADD COLUMN primera_conexion_docente TIMESTAMP;
ALTER TABLE clases ADD COLUMN es_gratuita BOOLEAN DEFAULT FALSE;
ALTER TABLE clases ADD COLUMN creada_por_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE clases ADD COLUMN notas_admin TEXT;
ALTER TABLE clases ADD COLUMN regenerar_link BOOLEAN DEFAULT TRUE;
ALTER TABLE clases ADD COLUMN link_jitsi_usado BOOLEAN DEFAULT FALSE;

-- Nuevas tablas
CREATE TABLE disponibilidad_docente (...);
CREATE TABLE bloques_no_disponibles (...);
```

### 🚀 Despliegue

#### Ambiente de Producción
- Servidor: 192.168.1.6 (LXR-AUVI01)
- Stack Docker: aulavirtual_web, aulavirtual_db, aulavirtual_nginx, aulavirtual_redis, aulavirtual_celery
- Base de Datos: PostgreSQL 15-alpine (nombre: aulavirtual_db)
- Aplicación: Gunicorn 21.2.0 con 4 workers sync
- Proxy: Nginx 1.25-alpine

#### Proceso de Actualización
1. Copiar archivos actualizados a `/root/aulavirtual/`
2. Ejecutar migraciones de BD desde contenedor `aulavirtual_db`
3. Eliminar archivos .pyc: `find /app -name "*.pyc" -delete`
4. Reinicio completo: `docker-compose down && docker-compose up -d`
5. Verificación: `docker logs --tail 30 aulavirtual_web`

### ⚠️ Notas de Implementación

#### Configuración Recomendada
- **Ventana de acceso**: 15 minutos antes del inicio (configurable en `models.py`)
- **Acceso único**: Activado por defecto (se puede deshabilitar por clase)
- **Regeneración de enlaces**: Desactivada por defecto para clases normales
- **Clases administrativas**: Máxima flexibilidad en configuración

#### Consideraciones de Seguridad
- Los enlaces Jitsi ya no se exponen en correos electrónicos
- Todo acceso pasa por validación en el backend
- Se registra timestamp de cada intento de acceso
- Los enlaces pueden regenerarse automáticamente después del primer uso

### 📝 Archivos Modificados

#### Python
- `app/models.py`: Modelos DisponibilidadDocente, BloqueNoDisponible, actualización Clase
- `app/routes.py`: Rutas de disponibilidad, unirse_clase con control de acceso
- `app/admin.py`: Ruta crear_clase_especial, context variables
- `app/auth.py`: Ruta cambiar_password (corrección)

#### Templates
- `app/templates/docentes/disponibilidad.html`: Nueva interfaz
- `app/templates/admin/crear_clase.html`: Nuevo formulario
- `app/templates/admin/clases.html`: Correcciones de campos
- `app/templates/calendario.html`: Integración disponibilidad
- `app/templates/email/confirmacion_clase.html`: Seguridad enlaces
- `app/templates/email/recordatorio_clase.html`: Seguridad enlaces

#### Scripts de Migración
- `migrar_db_control_acceso.py`: Migración principal
- `migrar_seguridad_jitsi.py`: Actualización seguridad
- `verificar_enlaces_jitsi.py`: Verificación post-migración

### 🔜 Próximos Pasos Recomendados

1. **Celery Worker**: Investigar y corregir errores de reinicio del worker
2. **Notificaciones**: Implementar alertas cuando una clase está por iniciar (5 min antes)
3. **Dashboard**: Agregar métricas de uso de enlaces y conexiones
4. **Reportes**: Panel de estadísticas de disponibilidad de docentes
5. **Mobile**: Optimizar interfaz de disponibilidad para dispositivos móviles

### 🆘 Soporte y Resolución de Problemas

Ver archivo [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para problemas comunes y soluciones.

---

**Fecha de Release**: 6 de marzo de 2026  
**Versión Anterior**: 2.0.0  
**Responsable**: Equipo de Desarrollo Aula Virtual  
**Estado**: ✅ En Producción
