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
