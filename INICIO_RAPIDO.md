# 🚀 Guía de Inicio Rápido - Aula Virtual

## ¿Cómo Empezar?

Acabas de completar la instalación de Aula Virtual. Aquí tienes los pasos para comenzar a usar la plataforma:

---

## 📌 Paso 1: Verificar que Todo Esté Corriendo

```bash
# Ver el estado de los contenedores
docker-compose ps

# Deberías ver 4 servicios corriendo:
# - web (Flask application)
# - db (PostgreSQL)
# - redis (Redis)
# - nginx (Reverse proxy)
```

---

## 🌐 Paso 2: Acceder a la Aplicación

1. Abre tu navegador web
2. Navega a: **http://localhost**
3. Deberías ver la página de inicio de Aula Virtual

---

## 👤 Paso 3: Crear Tu Primera Cuenta

### Opción A: Registrarse como Estudiante

1. Haz clic en **"Registrarse"** en la barra de navegación
2. Completa el formulario:
   - Nombre completo
   - Email
   - Contraseña (mínimo 8 caracteres)
   - Selecciona rol: **"Estudiante"**
3. Acepta los términos y condiciones
4. Haz clic en **"Crear Cuenta"**
5. ¡Listo! Ya puedes buscar docentes

### Opción B: Registrarse como Docente

1. Haz clic en **"Registrarse"**
2. Completa el formulario seleccionando rol: **"Docente"**
3. Después del registro, necesitarás:
   - Completar tu perfil profesional
   - Agregar especialidades
   - Configurar tu tarifa por hora
   - Esperar verificación del administrador

### Opción C: Usar la Cuenta de Administrador (Ya Creada)

Si creaste el usuario admin durante la instalación:

- **Email**: admin@aulavirtual.com
- **Contraseña**: Admin123!

---

## 🎯 Paso 4: Explorar las Funcionalidades

### Como Estudiante 👨‍🎓

1. **Buscar Docentes**
   - Ve a "Buscar Docentes" en el menú
   - Filtra por especialidad, precio, calificación
   - Revisa perfiles y reseñas

2. **Reservar una Clase**
   - Haz clic en un docente
   - Selecciona fecha y hora disponible
   - Completa el pago con tarjeta de prueba de Stripe
   
   **Tarjeta de Prueba Stripe:**
   ```
   Número: 4242 4242 4242 4242
   Fecha: Cualquier fecha futura (ej: 12/25)
   CVC: Cualquier 3 dígitos (ej: 123)
   ```

3. **Unirse a una Clase**
   - Ve a "Mi Calendario"
   - 15 minutos antes de la clase aparecerá el botón "Unirse"
   - Se abrirá una videollamada con Jitsi Meet

4. **Dejar una Reseña**
   - Después de la clase, podrás calificar al docente
   - Calificación de 1-5 estrellas + comentario

### Como Docente 👨‍🏫

1. **Completar Perfil**
   - Ve a "Dashboard"
   - Haz clic en "Completar Perfil"
   - Agrega:
     - Especialidades
     - Descripción profesional
     - Experiencia y educación
     - Tarifa por hora

2. **Configurar Disponibilidad**
   - Ve a "Calendario"
   - Configura tus horarios disponibles
   - Los estudiantes solo podrán reservar en esos horarios

3. **Gestionar Clases**
   - Recibe notificaciones de nuevas reservas
   - Prepara materiales en el dashboard
   - Únete puntualmente a las videollamadas

4. **Ver Finanzas**
   - Panel de ingresos en "Finanzas"
   - Recibes el 85% de cada clase (15% comisión de plataforma)
   - Solicita retiros cuando tengas mínimo $50

### Como Administrador 👑

1. **Panel de Administración**
   - Accede a estadísticas generales
   - Vista de todos los usuarios
   - Métricas financieras

2. **Verificar Docentes**
   - Lista de docentes pendientes de verificación
   - Revisar credenciales
   - Aprobar o rechazar perfiles

3. **Gestión de Usuarios**
   - Buscar y editar usuarios
   - Suspender cuentas si es necesario
   - Ver historial de actividad

4. **Reportes**
   - Transacciones y pagos
   - Estadísticas de uso
   - Exportar datos

---

## 🔒 Paso 5: Activar Autenticación de Dos Factores (2FA)

1. Ve a "Configuración"
2. Sección "Seguridad"
3. Haz clic en "Activar 2FA"
4. Escanea el código QR con una app como:
   - Google Authenticator
   - Authy
   - Microsoft Authenticator
5. Guarda los códigos de respaldo en un lugar seguro

---

## 📧 Paso 6: Configurar Notificaciones

1. Ve a "Configuración" > "Notificaciones"
2. Personaliza qué notificaciones deseas recibir:
   - Confirmaciones de clases
   - Mensajes nuevos
   - Recordatorios (15 min antes de clase)
   - Pagos y facturas
   - Promociones (opcional)

---

## 🎥 Probar Videollamadas

Para probar el sistema de videollamadas Jitsi:

1. Como estudiante, reserva una clase
2. Como docente, confirma la clase (o se confirmará automáticamente tras el pago)
3. Espera a que llegue el horario (o cambia la hora a "dentro de 5 minutos" en la BD para pruebas)
4. El botón "Unirse a Clase" se activará 15 minutos antes
5. Ambos usuarios podrán unirse a la misma sala de Jitsi

---

## 🧪 Datos de Prueba

### Tarjetas de Prueba Stripe

```bash
# Tarjeta exitosa
4242 4242 4242 4242

# Tarjeta declinada
4000 0000 0000 0002

# Requiere autenticación 3D Secure
4000 0025 0000 3155
```

### Emails de Prueba

Si no configuraste SMTP, los emails se mostrarán en los logs:

```bash
docker-compose logs -f web | grep "Email"
```

---

## 🔧 Comandos Útiles

```bash
# Ver logs de la aplicación
docker-compose logs -f web

# Reiniciar la aplicación
docker-compose restart web

# Detener todos los servicios
docker-compose down

# Reiniciar todo limpiamente
docker-compose down -v  # ⚠️ Esto borra la BD
docker-compose up --build -d

# Acceder al shell de Flask
docker-compose exec web flask shell

# Acceder a PostgreSQL
docker-compose exec db psql -U aulavirtual -d aulavirtual

# Ver uso de recursos
docker stats
```

---

## 🐛 Solución de Problemas Comunes

### Error: "Port 80 already in use"

```bash
# Cambiar el puerto en docker-compose.yml
ports:
  - "8080:80"  # Usar puerto 8080 en lugar de 80

# Luego acceder a http://localhost:8080
```

### Error: "Database connection failed"

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps db

# Revisar logs de la base de datos
docker-compose logs db

# Reintentar conexión
docker-compose restart web
```

### Error: "Templates no se renderizan correctamente"

```bash
# Verificar que Flask encuentre los templates
docker-compose exec web ls -la app/templates/

# Limpiar cache y reiniciar
docker-compose restart web
```

### Los emails no llegan

1. Verifica las credenciales en `.env`
2. Si usas Gmail, asegúrate de usar "Contraseña de Aplicación" (no tu contraseña normal)
3. Mira los logs: `docker-compose logs -f web | grep -i mail`

---

## 📚 Próximos Pasos

1. **Lee la documentación completa**: Abre `docs/index.html` en tu navegador
2. **Personaliza la plataforma**: Edita colores y logos en `app/static/css/style.css`
3. **Configura tu dominio**: Ve la sección de "Despliegue en Producción" en el README
4. **Conecta tu cuenta Stripe real**: Cambia las claves de test por las de producción
5. **Configura backups**: Implementa backups automáticos de PostgreSQL

---

## 🆘 Necesitas Ayuda?

- **Documentación Completa**: `docs/index.html`
- **Logs de la aplicación**: `docker-compose logs -f web`
- **Email de soporte**: soporte@aulavirtual.com

---

## ✅ Checklist de Verificación

- [ ] Todos los contenedores Docker están corriendo
- [ ] Puedo acceder a http://localhost
- [ ] Puedo registrarme como estudiante
- [ ] Puedo registrarme como docente
- [ ] Puedo iniciar sesión como admin
- [ ] Las páginas se ven correctamente (no muestran código Jinja2)
- [ ] Puedo buscar docentes
- [ ] Puedo procesar un pago de prueba con Stripe
- [ ] Las videollamadas funcionan
- [ ] Recibo notificaciones por email (o aparecen en logs)

---

¡Felicidades! 🎉 Tu plataforma Aula Virtual está lista para usar.
