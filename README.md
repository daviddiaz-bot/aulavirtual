# 🎓 Aula Virtual - Sistema de Gestión Educativa

![Aula Virtual](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0-lightgrey.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

**Aula Virtual** es una plataforma completa de gestión educativa que conecta estudiantes con docentes profesionales para clases personalizadas en tiempo real.

🟢 **Estado Actual**: Sistema desplegado en producción en servidor 192.168.1.6 con Docker Compose, PostgreSQL 15, Redis 7, Nginx 1.25, y Jitsi Meet integrado.

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Novedades v2.1.0](#-novedades-v210)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Estado del Despliegue](#-estado-del-despliegue)
- [Instalación Rápida](#-instalación-rápida)
- [Documentación](#-documentación)
- [Contribuir](#-contribuir)

---

## 🚀 Características Principales

✅ **Sistema de Autenticación Completo**
- Registro y login seguro
- Autenticación de dos factores (2FA) con TOTP
- Recuperación de contraseña
- Gestión de sesiones seguras
- CSRF Protection

✅ **Tres Roles de Usuario**
- **Administradores**: Panel completo de gestión + clases especiales
- **Docentes**: Gestión de clases, materiales y disponibilidad horaria
- **Estudiantes**: Reserva y seguimiento de clases

✅ **Sistema de Disponibilidad Horaria** 🆕
- Docentes definen horarios recurrentes semanales
- Bloqueo de fechas específicas (vacaciones, eventos)
- Validación automática de reservas según disponibilidad
- Interfaz visual de calendario

✅ **Gestión Avanzada de Clases**
- Reserva de clases con docentes
- Videoconferencias integradas con Jitsi Meet
- **Control de acceso temporal**: Clases disponibles 15 min antes 🆕
- **Acceso único con seguridad mejorada** 🆕
- Calendario de clases
- Historial y seguimiento
- Cierre automático al finalizar

✅ **Clases Especiales para Administradores** 🆕
- Creación de clases gratuitas
- Configuración flexible de seguridad
- Notas administrativas internas

✅ **Sistema de Pagos**
- Integración con Stripe
- Pagos seguros con tarjeta
- Webhooks para confirmación automática
- Gestión de transacciones

✅ **Gestión de Materiales**
- Subida de archivos (PDF, DOCX, etc.)
- Compartir con estudiantes
- Descarga segura

✅ **Sistema de Notificaciones**
- Emails de confirmación
- Recordatorios automáticos
- Alertas de cambios

✅ **Sistema de Calificaciones y Reseñas**
- Calificación de docentes (1-5 estrellas)
- Comentarios y feedback
- Promedio de calificaciones

✅ **Materiales Educativos**
- Subida de archivos por lección
- Materiales públicos y privados
- Biblioteca de recursos

✅ **Panel de Administración**
- Estadísticas en tiempo real
- Gestión de usuarios y docentes
- Reportes financieros
- Verificación de docentes

✅ **API REST**
- Endpoints documentados
- Autenticación con API Key
- Integraciones externas

✅ **Notificaciones**
- Emails automáticos
- Confirmaciones de reserva
- Recordatorios de clase

---

## 🆕 Novedades v2.1.0 (6 de Marzo 2026)

### 🌟 Sistema de Disponibilidad Horaria

Los docentes ahora pueden definir su disponibilidad de dos formas:

**1. Disponibilidad Recurrente**
```
Ej: Lunes a Viernes de 9:00 a 18:00
    Sábados de 10:00 a 14:00
```
- Se repite automáticamente cada semana
- Los estudiantes solo pueden reservar en horarios disponibles
- Configurable desde `/disponibilidad`

**2. Bloqueos Específicos**
```
Ej: Bloquear 15-20 de marzo (vacaciones)
    Bloquear 5 de abril de 14:00 a 16:00 (reunión)
```
- Bloquear días completos o rangos horarios
- Tiene precedencia sobre disponibilidad recurrente
- Ideal para vacaciones, eventos personales

### 🔒 Control de Acceso Mejorado

**Ventana Temporal de Acceso**:
- ⏰ Las clases se habilitan **15 minutos antes** del inicio
- ⏰ Permanecen activas hasta la **hora de fin programada**
- ⏰ Se cierran automáticamente al finalizar

**Seguridad de Enlaces Jitsi**:
- 🔐 **Sin enlaces directos**: Todo pasa por endpoint `/clase/<id>/unirse`
- 🔐 **Validaciones backend**: Verificación de horario, permisos, y estado
- 🔐 **Acceso único**: Opcionalmente, enlaces de un solo uso
- 🔐 **Regeneración automática**: Nuevos enlaces después de cada acceso (configurable)

**Seguimiento de Conexiones**:
```python
# Cada acceso registra:
- Timestamp de primera conexión
- Número de conexiones (estudiante/docente)
- Estado del enlace (usado/no usado)
```

### 🎁 Clases Especiales para Admins

Los administradores pueden crear clases con configuración especial:

- ✅ **Clases gratuitas**: Sin costo para el estudiante
- ✅ **Configuración flexible**: Control sobre acceso único y regeneración
- ✅ **Notas administrativas**: Documentar el propósito
- ✅ **Casos de uso**:
  - Clases de demostración
  - Reposiciones por problemas técnicos
  - Cortesías o promocionales

### 📊 Nuevos Modelos de Base de Datos

```sql
-- Disponibilidad recurrente
CREATE TABLE disponibilidad_docente (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER,
    dia_semana INTEGER,  -- 0=Domingo, 6=Sábado
    hora_inicio TIME,
    hora_fin TIME,
    activo BOOLEAN DEFAULT TRUE
);

-- Bloqueos específicos
CREATE TABLE bloques_no_disponibles (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER,
    fecha DATE,
    hora_inicio TIME,  -- NULL = todo el día
    hora_fin TIME,
    motivo VARCHAR(200)
);

-- 12 nuevos campos en 'clases'
ALTER TABLE clases ADD COLUMN clase_cerrada BOOLEAN DEFAULT FALSE;
ALTER TABLE clases ADD COLUMN acceso_unico BOOLEAN DEFAULT TRUE;
ALTER TABLE clases ADD COLUMN conexiones_estudiante INTEGER DEFAULT 0;
ALTER TABLE clases ADD COLUMN conexiones_docente INTEGER DEFAULT 0;
ALTER TABLE clases ADD COLUMN es_gratuita BOOLEAN DEFAULT FALSE;
ALTER TABLE clases ADD COLUMN creada_por_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE clases ADD COLUMN notas_admin TEXT;
ALTER TABLE clases ADD COLUMN regenerar_link BOOLEAN DEFAULT TRUE;
-- ... y 4 más
```

### 📝 Ver Cambios Completos
- [CHANGELOG.md](CHANGELOG.md) - Registro detallado de cambios
- [MANUAL_TECNICO.md](MANUAL_TECNICO.md) - Documentación técnica completa
- [MANUAL_USUARIO.md](MANUAL_USUARIO.md) - Guía para usuarios finales

---

## 📋 Requisitos Previos

- **Docker y Docker Compose** instalados (recomendado)
  - O Python 3.10+, PostgreSQL 15+, Redis 7+ (instalación manual)
- **Cuenta de Stripe** (para procesar pagos)
- **Servidor SMTP** o cuenta Gmail con contraseña de aplicación
- **Dominio** (opcional, para despliegue en producción)

---

## 🚀 Instalación Rápida

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Clonar el repositorio (o navegar a la carpeta)
cd AulaVirtual

# 2. Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Construir y ejecutar contenedores
docker-compose up --build -d

# 4. Inicializar la base de datos
docker-compose exec web flask db upgrade

# 5. Crear usuario administrador (opcional)
docker-compose exec web python -c "from app import create_app, db; from app.models import Usuario; app = create_app(); app.app_context().push(); admin = Usuario(nombre='Admin', email='admin@aulavirtual.com', rol='admin'); admin.set_password('Admin123!'); db.session.add(admin); db.session.commit(); print('Admin creado')"

# 6. Acceder a la aplicación
# Abre tu navegador en: http://localhost
```

La aplicación estará corriendo en:
- **Frontend**: http://localhost
- **API**: http://localhost/api

---

## 🔧 Instalación Completa

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/aulavirtual.git
cd aulavirtual
```

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Editar `.env` con tus configuraciones reales:

```env
# Flask
SECRET_KEY=genera-una-clave-secreta-con-openssl-rand-hex-32

# Base de Datos
DATABASE_URL=postgresql://aulavirtual:tu_password@db:5432/aulavirtual

# Redis
REDIS_URL=redis://redis:6379/0

# Email (Gmail con contraseña de aplicación)
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=xxxx_xxxx_xxxx_xxxx

# Stripe (obtener en https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLIC_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxx
```

### 3. Construir y Ejecutar con Docker Compose

```bash
# Construir las imágenes
docker-compose build

# Iniciar todos los servicios en segundo plano
docker-compose up -d

# Ver los logs en tiempo real
docker-compose logs -f web
```

### 4. Inicializar la Base de Datos

```bash
# Crear las tablas en la base de datos
docker-compose exec web flask db upgrade

# (Opcional) Verificar conexión a la base de datos
docker-compose exec db psql -U aulavirtual -d aulavirtual -c "\dt"
```

### 5. Crear Usuario Administrador

```bash
# Opción A: Desde Flask Shell (interactivo)
docker-compose exec web flask shell

# Luego ejecutar dentro del shell:
from app.models import Usuario
admin = Usuario(nombre='Administrador', email='admin@aulavirtual.com', rol='admin')
admin.set_password('Admin123!')
db.session.add(admin)
db.session.commit()
exit()

# Opción B: Comando directo (una línea)
docker-compose exec web python -c "from app import create_app, db; from app.models import Usuario; app = create_app(); app.app_context().push(); admin = Usuario(nombre='Admin', email='admin@aulavirtual.com', rol='admin'); admin.set_password('Admin123!'); db.session.add(admin); db.session.commit(); print('✅ Usuario Admin creado')"
```

### 6. Acceder a la Aplicación

- **Aplicación**: http://localhost
- **API**: http://localhost/api

**Credenciales por defecto:**
- Admin: `admin@aulavirtual.com` / `Admin123!`
- Docente: `docente@aulavirtual.com` / `Docente123!`
- Estudiante: `estudiante@aulavirtual.com` / `Cliente123!`

## 📚 Documentación

La documentación completa del proyecto está disponible en los siguientes archivos:

### Documentación Principal
- **[README.md](README.md)**: Visión general del proyecto, inicio rápido e instalación
- **[CHANGELOG.md](CHANGELOG.md)**: Historial de cambios, notas de versión y migraciones
- **[MANUAL_TECNICO.md](MANUAL_TECNICO.md)**: Documentación técnica completa para desarrolladores y administradores de sistemas
- **[MANUAL_USUARIO.md](MANUAL_USUARIO.md)**: Guías de usuario para docentes, estudiantes y administradores

### Guías de Instalación y Configuración
- **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)**: Guía de inicio rápido para entornos de desarrollo
- **[INSTALACION_COMPLETA.md](INSTALACION_COMPLETA.md)**: Procedimiento completo de instalación en producción
- **[ARQUITECTURA.md](ARQUITECTURA.md)**: Arquitectura del sistema y diseño técnico

### Documentación Específica
- **[JITSI_MEET.md](JITSI_MEET.md)**: Configuración e integración de Jitsi Meet
- **[MANUAL_MATERIALES_PDF.md](MANUAL_MATERIALES_PDF.md)**: Gestión de materiales y PDFs de clases
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Guía de resolución de problemas comunes

### Documentación HTML
La documentación también está disponible en formato HTML en la carpeta `/docs/`:
- Abre `/docs/index.html` en tu navegador para acceso interactivo a todos los manuales

## 🏗️ Arquitectura

```
AulaVirtual/
├── app/                    # Aplicación Flask
│   ├── __init__.py        # Factory de la app
│   ├── models.py          # Modelos de base de datos
│   ├── routes.py          # Rutas principales
│   ├── auth.py            # Autenticación
│   ├── admin.py           # Panel de administración
│   ├── api.py             # API REST
│   ├── email.py           # Sistema de emails
│   ├── tasks.py           # Tareas asíncronas (Celery)
│   ├── utils.py           # Utilidades
│   └── templates/         # Plantillas HTML
├── migrations/            # Migraciones de base de datos
├── static/                # Archivos estáticos (CSS, JS, imágenes)
├── nginx/                 # Configuración de Nginx
├── docs/                  # Documentación HTML
├── config.py              # Configuración
├── run.py                 # Punto de entrada
├── requirements.txt       # Dependencias Python
├── Dockerfile             # Imagen Docker
└── docker-compose.yml     # Orquestación de servicios
```

## 🔧 Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Base de Datos**: PostgreSQL
- **Cache**: Redis
- **Tareas Asíncronas**: Celery
- **Servidor Web**: Nginx + Gunicorn
- **Pagos**: Stripe
- **Videoconferencias**: Jitsi Meet
- **Autenticación 2FA**: PyOTP
- **Contenedores**: Docker & Docker Compose

## 📊 Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `SECRET_KEY` | Clave secreta de Flask | Sí |
| `DATABASE_URL` | URL de PostgreSQL | Sí |
| `REDIS_URL` | URL de Redis | Sí |
| `STRIPE_PUBLISHABLE_KEY` | Clave pública de Stripe | Sí |
| `STRIPE_SECRET_KEY` | Clave privada de Stripe | Sí |
| `STRIPE_WEBHOOK_SECRET` | Secret del webhook de Stripe | Sí |
| `MAIL_SERVER` | Servidor SMTP | Sí |
| `MAIL_PORT` | Puerto SMTP | Sí |
| `MAIL_USERNAME` | Usuario de email | Sí |
| `MAIL_PASSWORD` | Contraseña de email | Sí |
| `API_KEY` | Clave para la API REST | Sí |
| `JITSI_SERVER` | Servidor de Jitsi | No |

## 🧪 Testing

```bash
# Ejecutar tests
docker-compose exec web pytest

# Con cobertura
docker-compose exec web pytest --cov=app tests/
```

## 📝 Comandos Útiles

```bash
# Ver logs
docker-compose logs -f web

# Acceder al shell de Flask
docker-compose exec web flask shell

# Crear usuario administrador
docker-compose exec web flask create-admin

# Backup de base de datos
docker-compose exec db pg_dump -U postgres aulavirtual_db > backup.sql

# Restaurar base de datos
docker-compose exec -T db psql -U postgres aulavirtual_db < backup.sql
```

## 🔒 Seguridad

- Contraseñas hasheadas con Werkzeug
- Autenticación de dos factores (2FA) opcional
- Protección CSRF
- Headers de seguridad configurados en Nginx
- Rate limiting
- Validación de inputs
- Sesiones seguras
- SQL injection protection con SQLAlchemy ORM

## 🚀 Despliegue en Producción

### Requisitos Adicionales

1. **Dominio propio**
2. **Certificado SSL** (Let's Encrypt recomendado)
3. **Servidor** (VPS, AWS, DigitalOcean, etc.)

### Pasos

1. Configurar DNS apuntando al servidor
2. Instalar Docker y Docker Compose en el servidor
3. Clonar el repositorio
4. Configurar `.env` con valores de producción
5. Generar certificados SSL
6. Ejecutar `docker-compose -f docker-compose.yml up -d`

Consulta el **Manual de Implementación** en `/docs` para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más información.

## 📧 Contacto

- **Email**: soporte@aulavirtual.com
- **Website**: https://aulavirtual.com

## 🎓 Créditos

Desarrollado con ❤️ para la comunidad educativa.

---

**¿Necesitas ayuda?** Consulta nuestra [documentación completa](./docs/index.html) o abre un [issue](https://github.com/tu-usuario/aulavirtual/issues).
