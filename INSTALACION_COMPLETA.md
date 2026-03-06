# 🚀 GUÍA COMPLETA DE INSTALACIÓN - AULA VIRTUAL

**Versión**: 2.1.0  
**Sistema Operativo**: Linux (CentOS/RHEL 9, Ubuntu 20.04+)  
**Última actualización**: Marzo 2026

---

## 📋 ÍNDICE

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Instalación de Docker](#instalación-de-docker)
3. [Instalación de Docker Compose](#instalación-de-docker-compose)
4. [Clonación del Repositorio](#clonación-del-repositorio)
5. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
6. [Construcción e Inicio de Contenedores](#construcción-e-inicio-de-contenedores)
7. [Inicialización de Base de Datos](#inicialización-de-base-de-datos)
8. [Verificación del Sistema](#verificación-del-sistema)
9. [Configuración de Servicios Externos](#configuración-de-servicios-externos)
10. [Troubleshooting](#troubleshooting)

---

## 💻 REQUISITOS DEL SISTEMA

### Hardware Mínimo

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disco**: 20 GB disponible
- **Red**: Conexión a internet estable

### Hardware Recomendado (Producción)

- **CPU**: 4 cores o más
- **RAM**: 8 GB o más
- **Disco**: 50 GB SSD
- **Red**: 100 Mbps o superior

### Software Base

- **Sistema Operativo**: 
  - CentOS/RHEL 9.x
  - Ubuntu 20.04 LTS o superior
  - Debian 11+
- **Usuario**: root o usuario con sudo
- **Puertos abiertos**: 80, 443, 5000 (opcional)

---

## 🐳 INSTALACIÓN DE DOCKER

### Opción 1: CentOS/RHEL 9

#### Paso 1: Instalar dependencias

```bash
# Actualizar el sistema
sudo yum update -y

# Instalar utilidades necesarias
sudo yum install -y yum-utils device-mapper-persistent-data lvm2
```

**Explicación**:
- `yum-utils`: Proporciona herramientas para gestionar repositorios YUM
- `device-mapper-persistent-data` y `lvm2`: Necesarios para el driver de almacenamiento de Docker

#### Paso 2: Agregar repositorio de Docker

```bash
# Agregar repositorio oficial de Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```

**¿Qué hace esto?**  
Añade el repositorio oficial de Docker CE (Community Edition) para poder instalar la última versión estable.

#### Paso 3: Instalar Docker

```bash
# Instalar Docker Engine, CLI y containerd
sudo yum install -y docker-ce docker-ce-cli containerd.io
```

**Componentes instalados**:
- `docker-ce`: Docker Engine (motor principal)
- `docker-ce-cli`: Línea de comandos de Docker
- `containerd.io`: Runtime de contenedores

####Paso 4: Configurar servicio de Docker

```bash
# Habilitar Docker para que inicie con el sistema
sudo systemctl enable docker

# Iniciar el servicio de Docker
sudo systemctl start docker

# Verificar estado
sudo systemctl status docker
```

**Salida esperada**:
```
● docker.service - Docker Application Container Engine
   Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled)
   Active: active (running) since...
```

#### Paso 5: Verificar instalación

```bash
# Verificar versión de Docker
docker --version

# Ejecutar contenedor de prueba
docker run hello-world
```

**Salida esperada**:
```
Docker version 24.0.7, build...
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

---

### Opción 2: Ubuntu/Debian

#### Paso 1: Actualizar sistema e instalar dependencias

```bash
# Actualizar índice de paquetes
sudo apt-get update

# Instalar dependencias
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

#### Paso 2: Agregar GPG key y repositorio de Docker

```bash
# Agregar GPG key oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Configurar repositorio estable
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

#### Paso 3: Instalar Docker Engine

```bash
# Actualizar índice de paquetes
sudo apt-get update

# Instalar Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

#### Paso 4: Configurar y verificar

```bash
# Iniciar y habilitar Docker
sudo systemctl enable docker
sudo systemctl start docker

# Verificar instalación
docker --version
docker run hello-world
```

---

### Configuración Post-Instalación

#### Agregar usuario al grupo docker (Opcional)

Esto permite ejecutar Docker sin `sudo`:

```bash
# Agregar usuario actual al grupo docker
sudo usermod -aG docker $USER

# Cerrar sesión y volver a iniciar para aplicar cambios
# O ejecutar:
newgrp docker

# Verificar
docker run hello-world
```

**⚠️ Importante**: Agregar un usuario al grupo docker es equivalente a darle privilegios de root.

---

## 🔧 INSTALACIÓN DE DOCKER COMPOSE

Docker Compose es una herramienta para definir y ejecutar aplicaciones Docker multi-contenedor.

### Método 1: Instalación Binaria (Recomendado)

#### Paso 1: Descargar Docker Compose

```bash
# Descargar la última versión
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

**Explicación**:
- `-L`: Seguir redirecciones
- `$(uname -s)`: Nombre del sistema operativo (Linux)
- `$(uname -m)`: Arquitectura del sistema (x86_64, aarch64, etc.)
- `-o /usr/local/bin/docker-compose`: Guardar en directorio de binarios

#### Paso 2: Dar permisos de ejecución

```bash
# Hacer ejecutable el binario
sudo chmod +x /usr/local/bin/docker-compose
```

#### Paso 3: Crear enlace simbólico (Opcional)

```bash
# Crear symlink en /usr/bin para compatibilidad
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

#### Paso 4: Verificar instalación

```bash
# Verificar versión
docker-compose --version
```

**Salida esperada**:
```
Docker Compose version v2.24.0
```

---

### Método 2: Desde repositorios (Ubuntu/Debian)

```bash
# Instalar desde repositorio
sudo apt-get install docker-compose-plugin

# Uso (Nota: comando diferente)
docker compose version
```

**Nota**: Con el plugin, el comando es `docker compose` (con espacio) en lugar de `docker-compose` (con guión).

---

## 📦 CLONACIÓN DEL REPOSITORIO

### Paso 1: Instalar Git (si no está instalado)

```bash
# CentOS/RHEL
sudo yum install -y git

# Ubuntu/Debian
sudo apt-get install -y git
```

### Paso 2: Navegar al directorio deseado

```bash
# Ir al directorio home o donde prefieras
cd ~

# O crear un directorio específico
mkdir -p /opt/aulavirtual
cd /opt/aulavirtual
```

### Paso 3: Clonar el repositorio

```bash
# Clonar repositorio
git clone https://github.com/daviddiaz-bot/aulavirtual.git

# Entrar al directorio
cd aulavirtual
```

### Paso 4: Verificar archivos

```bash
# Listar archivos
ls -la

# Deberías ver:
# - app/ (código de la aplicación)
# - nginx/ (configuración de nginx)
# - docs/ (documentación)
# - docker-compose.yml
# - Dockerfile
# - requirements.txt
# - etc.
```

---

## 🔐 CONFIGURACIÓN DE VARIABLES DE ENTORNO

Las variables de entorno contienen información sensible y configuración de la aplicación.

### Paso 1: Copiar archivo de ejemplo

```bash
# Si existe .env.example
cp .env.example .env

# Si no existe, crear uno nuevo
nano .env
```

### Paso 2: Configurar variables esenciales

Edita el archivo `.env` con tu editor preferido:

```bash
nano .env
# o
vim .env
# o
vi .env
```

### Contenido del archivo .env

```bash
# ====================
# FLASK CONFIGURATION
# ====================

# Clave secreta de Flask (generar con: openssl rand -hex 32)
SECRET_KEY=tu-clave-secreta-aqui

# Entorno (development, production)
FLASK_ENV=production

# ====================
# DATABASE
# ====================

# URL de PostgreSQL
DATABASE_URL=postgresql://aulavirtual:password_seguro@db:5432/aulavirtual

# Nota: Cambia 'password_seguro' por una contraseña fuerte

# ====================
# STRIPE (Pagos)
# ====================

# Claves de Stripe (obtener en https://dashboard.stripe.com/apikeys)
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# ====================
# EMAIL
# ====================

# Configuración de email (ejemplo con Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion

# Nota: Para Gmail, usa una "Contraseña de aplicación", no tu contraseña normal

# ====================
# REDIS
# ====================

# URL de Redis (no cambiar si usas Docker Compose)
REDIS_URL=redis://redis:6379/0

# ====================
# JITSI MEET
# ====================

# Servidor de Jitsi (por defecto: meet.jit.si público)
JITSI_SERVER=meet.jit.si

# Para servidor propio, cambiar a tu dominio:
# JITSI_SERVER=jitsi.tudominio.com

# ====================
# OTROS
# ====================

# API Key para endpoints públicos (generar aleatoria)
API_KEY=tu-api-key-secreta
```

### Paso 3: Generar SECRET_KEY segura

```bash
# Método 1: Usando OpenSSL
openssl rand -hex 32

# Método 2: Usando Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copia el output y pégalo en SECRET_KEY
```

**Ejemplo de SECRET_KEY generada**:
```
9b5cb037ea4a0869b0d059a9d5b3e45cb251b3384083d18aac16bd1f70e1f5ec
```

### Paso 4: Configurar contraseña de base de datos

En el archivo `.env`, cambia `password_seguro` por una contraseña fuerte:

```bash
DATABASE_URL=postgresql://aulavirtual:MiPasswordSeguro2024!@db:5432/aulavirtual
```

### Paso 5: Proteger el archivo .env

```bash
# Cambiar permisos (solo propietario puede leer/escribir)
chmod 600 .env

# Verificar permisos
ls -l .env
# Debería mostrar: -rw------- (solo owner)
```

**⚠️ IMPORTANTE**: Nunca subas el archivo `.env` a Git. Debe estar en `.gitignore`.

---

## 🏗️ CONSTRUCCIÓN E INICIO DE CONTENEDORES

### Entender docker-compose.yml

El archivo `docker-compose.yml` define todos los servicios de la aplicación:

```yaml
version: '3.8'

services:
  # Base de Datos PostgreSQL
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: aulavirtual
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: aulavirtual
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "aulavirtual"]
    
  # Redis (Cache)
  redis:
    image: redis:7-alpine
    
  # Aplicación Web
  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - db
      - redis
    env_file:
      - .env
      
  # Nginx (Proxy)
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
      
  # Celery Worker
  celery_worker:
    build: .
    command: celery -A app.celery_app worker
    depends_on:
      - redis
      - db
```

### Paso 1: Construir imágenes

```bash
# Construir todas las imágenes
docker-compose build

# Esto puede tardar varios minutos la primera vez
```

**¿Qué hace esto?**
- Lee el `Dockerfile`
- Descarga la imagen base de Python
- Instala dependencias del sistema
- Instala paquetes Python (requirements.txt)
- Copia el código de la aplicación
- Crea la imagen final

**Salida esperada**:
```
Building web
[+] Building 45.3s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 812B
 => [internal] load .dockerignore
 ...
Successfully built 8a72b3e5f6d4
Successfully tagged aulavirtual-web:latest
```

### Paso 2: Iniciar todos los servicios

```bash
# Iniciar en modo detached (segundo plano)
docker-compose up -d

# Esperar a que todos los servicios estén listos
```

**Salida esperada**:
```
Creating network "aulavirtual_default" with the default driver
Creating volume "aulavirtual_postgres_data" with default driver
Creating aulavirtual_db ... done
Creating aulavirtual_redis ... done
Creating aulavirtual_web ... done
Creating aulavirtual_nginx ... done
Creating aulavirtual_celery ... done
```

### Paso 3: Verificar que los contenedores estén corriendo

```bash
# Ver estado de contenedores
docker-compose ps
```

**Salida esperada**:
```
NAME                  STATUS          PORTS
aulavirtual_db        Up (healthy)    5432/tcp
aulavirtual_redis     Up              6379/tcp
aulavirtual_web       Up              0.0.0.0:5000->5000/tcp
aulavirtual_nginx     Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
aulavirtual_celery    Up              
```

### Paso 4: Ver logs (opcional)

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs web

# Seguir logs en tiempo real
docker-compose logs -f web
```

---

## 🗄️ INICIALIZACIÓN DE BASE DE DATOS

### Paso 1: Inicializar Flask-Migrate

```bash
# Entrar al contenedor web
docker-compose exec web bash

# Dentro del contenedor, inicializar migraciones
flask db init
```

**¿ Qué hace esto?**
- Crea carpeta `migrations/` con configuración de Alembic
- Prepara el sistema de migraciones de base de datos

### Paso 2: Crear migración inicial

```bash
# Generar migración basada en modelos
flask db migrate -m "Initial migration"
```

**Salida esperada**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'usuarios'
INFO  [alembic.autogenerate.compare] Detected added table 'docentes'
INFO  [alembic.autogenerate.compare] Detected added table 'clases'
...
Generating /app/migrations/versions/abc123_initial_migration.py ... done
```

### Paso 3: Aplicar migraciones

```bash
# Ejecutar migraciones
flask db upgrade
```

**Salida esperada**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial migration
```

### Paso 4: Salir del contenedor

```bash
# Salir
exit
```

### Paso 5: Crear usuario administrador

```bash
# Opción 1: Interactivo
docker-compose exec web python crear_admin.py

# Opción 2: Automático
echo -e "Admin\nadmin@aulavirtual.com\nadmin123\nadmin123" | docker-compose exec -T web python crear_admin.py
```

**Salida esperada**:
```
==================================================
CREAR USUARIO ADMINISTRADOR
==================================================
Nombre completo [Admin]: Admin
Email [admin@aulavirtual.com]: admin@aulavirtual.com
Contraseña [Admin123!]: admin123  

==================================================
✅ USUARIO ADMINISTRADOR CREADO EXITOSAMENTE
==================================================
Nombre: Admin
Email: admin@aulavirtual.com
Contraseña: admin123

⚠️  IMPORTANTE: Guarda estas credenciales en un lugar seguro
==================================================
```

**⚠️ IMPORTANTE**: Cambia la contraseña inmediatamente después del primer login.

---

## ✅ VERIFICACIÓN DEL SISTEMA

### Paso 1: Ejecutar script de verificación

```bash
# Ejecutar verificación completa
docker-compose exec web python verificar_sistema.py
```

**Salida esperada (exitosa)**:
```
============================================================
🔍 VERIFICACIÓN DEL SISTEMA AULA VIRTUAL
============================================================

1️⃣  Verificando aplicación Flask...
   ✅ Aplicación Flask inicializada correctamente

2️⃣  Verificando conexión a PostgreSQL...
   ✅ Conexión a PostgreSQL exitosa

3️⃣  Verificando tablas de la base de datos...
   ✅ Tabla 'usuarios' existe
   ✅ Tabla 'docentes' existe
   ✅ Tabla 'clases' existe
   ✅ Tabla 'pagos' existe
   ...

4️⃣  Verificando usuarios en el sistema...
   📊 Total de usuarios: 1
   👑 Administradores: 1

5️⃣  Verificando variables de entorno...
   ✅ SECRET_KEY configurada
   ✅ DATABASE_URL configurada
   ✅ STRIPE_SECRET_KEY configurada
   ...

6️⃣  Verificando conexión a Redis...
   ✅ Conexión a Redis exitosa

7️⃣  Verificando estructura de carpetas...
   ✅ app/templates existe
   ✅ app/static/css existe
   ✅ app/static/js existe
   ✅ app/static/uploads existe

============================================================
📋 RESUMEN DE VERIFICACIÓN
============================================================

✅ El sistema está correctamente configurado y listo para usar.

============================================================
```

### Paso 2: Verificar acceso web

```bash
# Obtener IP del servidor
ip addr show | grep "inet " | grep -v "127.0.0.1"

# O
hostname -I
```

**Probar en navegador**:
```
http://TU_IP_AQUI
http://TU_IP_AQUI:5000  (acceso directo a Flask)
```

### Paso 3: Verificar puertos abiertos

```bash
# Ver puertos en uso
ss -tulpn | grep -E ':(80|443|5000|5432|6379)'
```

**Salida esperada**:
```
tcp   LISTEN 0.0.0.0:80      # Nginx HTTP
tcp   LISTEN 0.0.0.0:443     # Nginx HTTPS
tcp   LISTEN 0.0.0.0:5000    # Flask app
tcp   LISTEN 127.0.0.1:5432  # PostgreSQL (solo local)
tcp   LISTEN 127.0.0.1:6379  # Redis (solo local)
```

---

## 🔧 CONFIGURACIÓN DE SERVICIOS EXTERNOS

### 1. Stripe (Pagos)

Documentado en [SERVICIOS_EXTERNOS.md](SERVICIOS_EXTERNOS.md#stripe)

Ver sección completa para:
- Crear cuenta de Stripe
- Obtener claves API
- Configurar webhooks
- Modo test vs producción

### 2. Jitsi Meet (Videollamadas)

Documentado en [JITSI_MEET.md](JITSI_MEET.md)

Opciones:
- Usar servidor público (meet.jit.si) - Por defecto
- Instalar servidor propio
- Personalización

### 3.SMTP (Emails)

#### Opción 1: Gmail

1. Habilitar verificación en 2 pasos en tu cuenta de Gmail
2. Ir a: https://myaccount.google.com/apppasswords
3. Generar contraseña de aplicación
4. Usar en `.env`:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Contraseña de aplicación
```

#### Opción 2: SendGrid

1. Crear cuenta en https://sendgrid.com
2. Generar API Key
3. Configurar:

```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.xxxxxxxxx  # Tu API key
```

---

## 🔥 TROUBLESHOOTING

### Problema 1: Contenedor de Nginx no inicia

**Error**: `cannot load certificate "/etc/nginx/ssl/cert.pem"`

**Solución**:
```bash
# Generar certificados SSL autofirmados
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=AulaVirtual/CN=localhost"

# Reiniciar nginx
docker-compose restart nginx
```

### Problema 2: Celery worker no inicia

**Error**: `Unable to load celery application`

**Solución**:
```bash
# Verificar que existe app/celery_app.py o app/tasks.py
ls -l app/celery_app.py app/tasks.py

# Revisar configuración en docker-compose.yml
# El comando debe apuntar al módulo correcto
```

### Problema 3: Base de datos no conecta

**Error**: `could not connect to server`

**Solución**:
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps db

# Ver logs de PostgreSQL
docker-compose logs db

# Reiniciar contenedor de DB
docker-compose restart db

# Esperar a que esté "healthy"
docker-compose ps db
```

### Problema 4: Puerto 80 ya en uso

**Error**: `bind: address already in use`

**Solución**:
```bash
# Ver qué proceso usa el puerto 80
sudo lsof -i :80

# O con ss
sudo ss -tulpn | grep :80

# Opción 1: Detener el servicio que lo usa
# Por ejemplo, si es Apache:
sudo systemctl stop httpd

# Opción 2: Cambiar puerto en docker-compose.yml
# Editar la sección de nginx:
# ports:
#   - "8080:80"  # Usar puerto 8080 en su lugar
```

### Problema 5: Permisos de archivos

**Error**: `Permission denied`

**Solución**:
```bash
# Dar permisos al directorio
sudo chown -R $USER:$USER /ruta/a/aulavirtual

# O ejecutar con sudo
sudo docker-compose up -d
```

### Comandos Útiles de Troubleshooting

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs web
docker-compose logs db

# Entrar a un contenedor
docker-compose exec web bash
docker-compose exec db psql -U aulavirtual

# Reiniciar un servicio
docker-compose restart web

# Reconstruir un servicio
docker-compose up -d --build web

# Limpiar y empezar de cero
docker-compose down -v  # ⚠️ Elimina TODOS los datos
docker-compose up -d --build
```

**Para problemas más complejos y detallados**: Ver **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** que incluye:
- Error 500: Templates Admin Faltantes
- Error: Atributos de Modelo Incorrectos  
- Error: Endpoints Incorrectos
- Error: Material Upload - Formulario No Aparece
- Error 500: Vista Detalle Material
- BuildError: Parámetro Incorrecto en URL
- Error 500: Descarga de Materiales
- Login Requiere Checkbox "Recordar" (SESSION_COOKIE_SECURE)
- Limpieza de Cache Python

---

## ✅ POST-INSTALACIÓN Y VERIFICACIÓN

### Verificar Estado del Sistema

**1. Verificar que todos los containers están corriendo**:
```bash
docker-compose ps
```

**Output esperado** (todos deben estar "Up"):
```
NAME                        STATE    PORTS
aulavirtual_nginx           Up       0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
aulavirtual_web             Up       0.0.0.0:5000->5000/tcp
aulavirtual_db              Up       0.0.0.0:5432->5432/tcp
aulavirtual_redis           Up       0.0.0.0:6379->6379/tcp
aulavirtual_celery          Up       
```

**2. Verificar logs sin errores**:
```bash
# Revisar logs de aplicación web
docker-compose logs --tail=50 web | grep -i error

# Revisar logs de base de datos
docker-compose logs --tail=50 db | grep -i error
```

**3. Test de conexión HTTP**:
```bash
# Desde el servidor
curl -I http://localhost

# Desde otro equipo en la red
curl -I http://192.168.1.6
```

**Output esperado**:
```
HTTP/1.1 200 OK
Server: nginx/1.25.x
Content-Type: text/html; charset=utf-8
```

**4. Verificar base de datos**:
```bash
# Entrar a PostgreSQL
docker-compose exec db psql -U postgres -d aulavirtual_db

# Verificar tablas creadas
\dt

# Verificar usuario admin existe
SELECT email, rol FROM usuario WHERE rol='admin';

# Salir
\q
```

**5. Verificar configuración Flask**:
```bash
# Ver configuración actual
docker-compose exec web python -c "
from app import create_app
app = create_app()
print('FLASK_ENV:', app.config.get('FLASK_ENV'))
print('SECRET_KEY configured:', bool(app.config.get('SECRET_KEY')))
print('DATABASE_URL:', app.config.get('SQLALCHEMY_DATABASE_URI'))
print('REDIS_URL:', app.config.get('REDIS_URL'))
print('SESSION_COOKIE_SECURE:', app.config.get('SESSION_COOKIE_SECURE'))
"
```

**Output esperado**:
```
FLASK_ENV: production
SECRET_KEY configured: True
DATABASE_URL: postgresql://postgres:AulaVirtual2026!@db:5432/aulavirtual_db
REDIS_URL: redis://redis:6379/0
SESSION_COOKIE_SECURE: False  # Debe ser False si no hay HTTPS
```

### Configuraciones Post-Instalación

**1. Cambiar Password del Admin**

```bash
# Opción A: Usando script Python
docker-compose exec web python
>>> from app.models import Usuario
>>> from app import db, create_app
>>> app = create_app()
>>> with app.app_context():
...     admin = Usuario.query.filter_by(email='admin@aulavirtual.com').first()
...     admin.set_password('TuNuevaPasswordSegura123!')
...     db.session.commit()
...     print('Password actualizada')
>>> exit()
```

```bash
# Opción B: Usando script del proyecto
cd /root/aulavirtual
docker-compose exec web python reset_password_admin.py
# Seguir las instrucciones
```

**2. Probar funcionalidad básica**:

a) **Acceder a la interfaz web**:
   - Abrir navegador: `http://192.168.1.6`
   - Debe cargar la página de inicio

b) **Login como admin**:
   - Click en "Iniciar Sesión"
   - Email: `admin@aulavirtual.com`
   - Password: (el que configuraste)
   - ✅ Debe iniciar sesión correctamente

c) **Acceder al panel admin**:
   - Una vez logueado, ir a `/admin`
   - Debe mostrar dashboard con estadísticas

d) **Probar registro de usuario**:
   - Logout del admin
   - Click en "Registrarse"
   - Completar formulario
   - ✅ Debe crear usuario y enviar email (si SMTP configurado)

**3. Configurar Email SMTP (Gmail)**

```bash
# Editar .env
nano /root/aulavirtual/.env
```

Agregar/verificar:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_app_password_gmail
MAIL_DEFAULT_SENDER=tu_email@gmail.com
```

**Obtener App Password de Gmail**:
1. Ir a https://myaccount.google.com/apppasswords
2. Seleccionar "Mail" y el dispositivo
3. Copiar la contraseña de 16 caracteres
4. Pegarla en MAIL_PASSWORD (sin espacios)

Reiniciar para aplicar:
```bash
docker-compose restart web celery
```

**Probar envío de email**:
```bash
docker-compose exec web python -c "
from app import create_app, mail
from flask_mail import Message
app = create_app()
with app.app_context():
    msg = Message(
        'Test desde Aula Virtual',
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=['tu_email@gmail.com']
    )
    msg.body = 'Este es un email de prueba para verificar configuración SMTP'
    try:
        mail.send(msg)
        print('✅ Email enviado correctamente')
    except Exception as e:
        print(f'❌ Error: {e}')
"
```

**4. Configurar Stripe (Pagos)** - ⚠️ PENDIENTE

```bash
# Editar .env
nano /root/aulavirtual/.env
```

Agregar:
```
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

Obtener keys:
1. Ir a https://dashboard.stripe.com/apikeys
2. Copiar las keys (usar "Test mode" para pruebas)
3. Configurar webhook en https://dashboard.stripe.com/webhooks
   - URL: `https://tu-dominio.com/api/webhook/stripe`
   - Eventos: `payment_intent.succeeded`, `payment_intent.payment_failed`

Reiniciar:
```bash
docker-compose restart web
```

**5. Configurar Jitsi Meet (Videollamadas)**

El sistema usa Jitsi Meet público por defecto. Para servidor privado:

```bash
# Editar .env
nano /root/aulavirtual/.env
```

```
# Opción 1: Usar servidor público (por defecto)
JITSI_SERVER=meet.jit.si

# Opción 2: Usar tu propio servidor Jitsi
JITSI_SERVER=jitsi.tu-dominio.com
```

Ver [JITSI_MEET.md](./JITSI_MEET.md) para configurar servidor propio.

### Configurar Backups Automáticos

**Crear script de backup**:

```bash
# Crear directorio de backups
mkdir -p /root/backups/aulavirtual

# Crear script de backup
nano /root/backups/backup-aulavirtual.sh
```

Contenido del script:
```bash
#!/bin/bash

# Configuración
BACKUP_DIR="/root/backups/aulavirtual"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Crear backup de base de datos
echo "Iniciando backup de base de datos..."
cd /root/aulavirtual
docker-compose exec -T db pg_dump -U postgres aulavirtual_db > ${BACKUP_DIR}/db_backup_${DATE}.sql

# Comprimir backup
gzip ${BACKUP_DIR}/db_backup_${DATE}.sql

# Backup de archivos subidos
echo "Backing up archivos subidos..."
tar -czf ${BACKUP_DIR}/uploads_backup_${DATE}.tar.gz -C /root/aulavirtual app/static/uploads

# Eliminar backups antiguos
echo "Limpiando backups antiguos..."
find ${BACKUP_DIR} -name "db_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "uploads_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup completado: ${DATE}"
```

```bash
# Dar permisos de ejecución
chmod +x /root/backups/backup-aulavirtual.sh

# Probar el script
/root/backups/backup-aulavirtual.sh
```

**Configurar cron job para backups automáticos**:

```bash
# Editar crontab
crontab -e
```

Agregar línea (backup diario a las 2 AM):
```
0 2 * * * /root/backups/backup-aulavirtual.sh >> /var/log/aulavirtual-backup.log 2>&1
```

**Verificar backups**:
```bash
# Ver backups creados
ls -lh /root/backups/aulavirtual/

# Ver logs de backup
tail -f /var/log/aulavirtual-backup.log
```

### Configurar SSL/HTTPS con Let's Encrypt

**Prerequisitos**:
- Tener un dominio apuntando al servidor
- Puerto 80 y 443 abiertos en firewall

**Instalar Certbot**:

```bash
# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx

# Ubuntu/Debian
sudo apt-get install -y certbot python3-certbot-nginx
```

**Obtener certificado**:

```bash
# Detener nginx temporalmente
docker-compose stop nginx

# Obtener certificado
sudo certbot certonly --standalone -d aulavirtual.com -d www.aulavirtual.com

# Los certificados se guardan en:
# /etc/letsencrypt/live/aulavirtual.com/fullchain.pem
# /etc/letsencrypt/live/aulavirtual.com/privkey.pem
```

**Configurar nginx para usar certificados**:

```bash
# Editar docker-compose.yml
nano /root/aulavirtual/docker-compose.yml
```

Agregar volumen en nginx:
```yaml
nginx:
  # ... resto de config ...
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro  # ← AGREGAR ESTA LÍNEA
    - ./static:/usr/share/nginx/html/static:ro
```

```bash
# Editar configuración de nginx
nano /root/aulavirtual/nginx/nginx.conf
```

Agregar bloque SSL:
```nginx
server {
    listen 80;
    server_name aulavirtual.com www.aulavirtual.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aulavirtual.com www.aulavirtual.com;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/aulavirtual.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aulavirtual.com/privkey.pem;
    
    # Configuración SSL segura
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';

    # ... resto de configuración proxy_pass, etc ...
}
```

```bash
# Actualizar .env para HTTPS
nano /root/aulavirtual/.env
```

```
SESSION_COOKIE_SECURE=True  # ← Cambiar a True con HTTPS
```

```bash
# Reiniciar
docker-compose down
docker-compose up -d
```

**Configurar renovación automática**:

```bash
# Probar renovación
sudo certbot renew --dry-run

# Agregar a crontab para renovación automática
sudo crontab -e
```

Agregar línea (renovar cada 3 meses, a las 3 AM del día 1):
```
0 3 1 */3 * certbot renew --quiet && docker-compose -f /root/aulavirtual/docker-compose.yml restart nginx
```

### Monitoreo y Logs

**Ver logs en tiempo real**:
```bash
# Todos los servicios
docker-compose logs -f

# Solo aplicación web
docker-compose logs -f web

# Con filtro de errores
docker-compose logs -f web | grep -i error
```

**Configurar rotación de logs**:

```bash
# Crear configuración logrotate
sudo nano /etc/logrotate.d/aulavirtual
```

Contenido:
```
/var/log/aulavirtual-backup.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
}
```

**Monitoreo de recursos**:

```bash
# Ver uso de CPU/Memoria de containers
docker stats

# Ver espacio en disco
df -h
docker system df

# Ver logs de sistema
journalctl -u docker -f
```

---

## 📚 PRÓXIMOS PASOS

Una vez instalado y verificado:

1. **Cambiar contraseña de admin**: Login y cambiar contraseña por defecto
2. **Configurar Stripe**: Activar modo producción cuando estés listo
3. **Configurar dominio**: Apuntar dominio al servidor
4. **SSL en producción**: Usar Let's Encrypt para certificados válidos
5. **Backups**: Configurar backups automáticos de la base de datos
6. **Monitoreo**: Instalar Prometheus/Grafana para métricas

---

## 📖 DOCUMENTACIÓN ADICIONAL

- [Arquitectura del Sistema](ARQUITECTURA.md)
- [Configuración de Jitsi Meet](JITSI_MEET.md)
- [Servicios Externos (Stripe, SMTP)](SERVICIOS_EXTERNOS.md)
- [Manual de Administración](docs/index.html#administracion-section)
- [Manual de Usuario](docs/index.html#usuario-section)
- [Reporte de QA](REPORTE_QA.md)

---

**Elaborado por**: Equipo de Desarrollo  
**Soporte**: soporte@aulavirtual.com  
**Última actualización**: Marzo 2026

---
