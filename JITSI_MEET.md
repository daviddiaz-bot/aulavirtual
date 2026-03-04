# 🎥 GUÍA COMPLETA DE JITSI MEET - AULA VIRTUAL

**Última actualización**: Marzo 2026  
**Integración**: Aula Virtual 1.0.0

---

## 📋 ÍNDICE

1. [¿Qué es Jitsi Meet?](#qué-es-jitsi-meet)
2. [Opciones de Uso](#opciones-de-uso)
3. [Opción 1: Servidor Público (meet.jit.si)](#opción-1-servidor-público)
4. [Opción 2: Servidor Propio](#opción-2-servidor-propio)
5. [Cómo Funciona en Aula Virtual](#cómo-funciona-en-aula-virtual)
6. [Manual de Uso para Estudiantes](#manual-de-uso-para-estudiantes)
7. [Manual de Uso para Docentes](#manual-de-uso-para-docentes)
8. [Personalización Avanzada](#personalización-avanzada)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 ¿QUÉ ES JITSI MEET?

**Jitsi Meet** es una plataforma de videoconferencias de código abierto, segura y gratuita.

### Características Principales

- **100% Gratuito**: No hay costos de licencias
- **Código Abierto**: Totalmente auditable
- **Seguro**: Encriptación end-to-end opcional
- **Sin Registro**: No requiere cuenta para participantes
- **Multi-plataforma**: Web, iOS, Android, Desktop
- **Sin Límites**: Reuniones ilimitadas
- **Calidad**: Hasta 4K de video

### ¿Por Qué Jitsi Meet en Aula Virtual?

1. **Gratuito**: No hay costos adicionales por videollamadas
2. **Fácil**: Un solo click para unirse
3. **Privado**: Salas únicas por clase
4. **Compatible**: Funciona en cualquier navegador moderno
5. **Sin Apps**: Solo se necesita un navegador web

---

## 🔀 OPCIONES DE USO

### Comparación de Opciones

| Característica | Servidor Público | Servidor Propio |
|----------------|------------------|-----------------|
| **Costo** | Gratis | $10-50/mes (VPS) |
| **Setup** | 0 minutos | 2-4 horas |
| **Mantenimiento** | Ninguno | Actualizaciones periódicas |
| **Personalización** | Limitada | Total |
| **Privacidad** | Compartida | Total |
| **Performance** | Variable | Controlado |
| **Límites** | Posibles | Sin límites |
| **Recomendado para** | MVP, Pruebas | Producción, Enterprise |

---

## 🌐 OPCIÓN 1: SERVIDOR PÚBLICO (meet.jit.si)

### Configuración en Aula Virtual

**Por defecto, Aula Virtual usa el servidor público de Jitsi.**

#### Paso 1: Verificar configuración

En tu archivo `.env`:

```bash
# Servidor de Jitsi Meet
JITSI_SERVER=meet.jit.si
```

#### Paso 2: ¡Listo!

No se requiere configuración adicional. Cada clase tendrá automáticamente un link único:

```
https://meet.jit.si/clase-abc123def4
```

### Ventajas

✅ **Configuración inmediata**: Solo agregar línea en `.env`  
✅ **Sin costos**: Completamente gratis  
✅ **Sin mantenimiento**: Gestionado por Jitsi  
✅ **Alta disponibilidad**: Servidores en todo el mundo  

### Desventajas

⚠️ **Compartido**: Recursos compartidos con otros usuarios  
⚠️ **Personalización limitada**: No puedes personalizar completamente  
⚠️ **Posibles límites**: En horas pico puede haber restricciones  

### ¿Es Seguro?

**SÍ**, Jitsi Meet usa:
- HTTPS para todas las conexiones
- WebRTC con encriptación
- Salas únicas (UUID aleatorio)
- No guarda grabaciones sin permiso

### Límites del Servidor Público

- **Participantes**: Recomendado hasta 35 personas
- **Calidad**: Puede variar según carga del servidor
- **Funciones**: Algunas funciones avanzadas pueden estar limitadas

---

## 🖥️ OPCIÓN 2: SERVIDOR PROPIO

### ¿Cuándo Instalar Tu Propio Servidor?

- Más de 50 estudiantes simultáneos
- Necesitas personalizar marca (logo, colores)
- Requieres grabación en servidor
- Necesitas control total de privacidad
- Quieres estadísticas detalladas

### Requisitos del Servidor

#### Hardware

**Mínimo** (hasta 20 participantes):
- CPU: 4 cores
- RAM: 8 GB
- Disco: 40 GB SSD
- Ancho de banda: 100 Mbps

**Recomendado** (hasta 50 participantes):
- CPU: 8 cores
- RAM: 16 GB
- Disco: 100 GB SSD
- Ancho de banda: 1 Gbps

**Producción** (100+ participantes):
- CPU: 16+ cores
- RAM: 32+ GB
- Disco: 200 GB SSD
- Ancho de banda: 1 Gbps+

#### Software

- Ubuntu 20.04 LTS o 22.04 LTS (recomendado)
- Dominio con DNS configurado
- Certificado SSL (Let's Encrypt gratuito)

### Instalación Paso a Paso

#### Paso 1: Preparar servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Configurar hostname
sudo hostnamectl set-hostname jitsi.tudominio.com

# Editar /etc/hosts
sudo nano /etc/hosts
# Agregar:
# TU_IP jitsi.tudominio.com jitsi

# Configurar firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 10000/udp
sudo ufw allow 22/tcp
sudo ufw enable
```

#### Paso 2: Instalar Jitsi Meet

```bash
# Agregar repositorio de Jitsi
curl https://download.jitsi.org/jitsi-key.gpg.key | sudo sh -c 'gpg --dearmor > /usr/share/keyrings/jitsi-keyring.gpg'

echo 'deb [signed-by=/usr/share/keyrings/jitsi-keyring.gpg] https://download.jitsi.org stable/' | sudo tee /etc/apt/sources.list.d/jitsi-stable.list > /dev/null

# Actualizar índice
sudo apt update

# Instalar Jitsi Meet
sudo apt install -y jitsi-meet
```

**Durante la instalación**:
1. Ingresa tu dominio: `jitsi.tudominio.com`
2. Selecciona: "Generate a new self-signed certificate (You will later get a chance to obtain a Let's Encrypt certificate)"

#### Paso 3: Obtener certificado SSL

```bash
# Instalar Let's Encrypt
sudo /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh

# Seguir instrucciones:
# - Ingresar email para notificaciones
# - Aceptar términos
```

#### Paso 4: Configurar autenticación (Opcional pero recomendado)

Por defecto, cualquiera puede crear salas. Para requerir autenticación:

```bash
# Editar configuración
sudo nano /etc/prosody/conf.avail/jitsi.tudominio.com.cfg.lua

# Cambiar:
# authentication = "anonymous"
# Por:
authentication = "internal_plain"

# Guardar y salir (Ctrl+X, Y, Enter)

# Crear usuario administrador
sudo prosodyctl register admin jitsi.tudominio.com tu_contraseña

# Reiniciar servicios
sudo systemctl restart prosody jicofo jitsi-videobridge2
```

#### Paso 5: Verificar instalación

Abre tu navegador en:
```
https://jitsi.tudominio.com
```

Deberías ver la pantalla de inicio de Jitsi Meet.

#### Paso 6: Integrar con Aula Virtual

En el archivo `.env` de Aula Virtual:

```bash
# Cambiar de meet.jit.si a tu servidor
JITSI_SERVER=jitsi.tudominio.com
```

Reiniciar servicios:

```bash
docker-compose restart web
```

---

## ⚙️ CÓMO FUNCIONA EN AULA VIRTUAL

### Flujo de Creación de Clase

```
1. Cliente reserva clase con docente
   ↓
2. Sistema crea registro en base de datos
   ↓
3. Sistema genera link único de Jitsi:
   https://meet.jit.si/clase-{UUID-único}
   Ejemplo: https://meet.jit.si/clase-a3b7c9d2ef
   ↓
4. Link se guarda en campo link_jitsi de la tabla clases
   ↓
5. Cliente realiza pago (Stripe)
   ↓
6. Clase pasa a estado "confirmada"
   ↓
7. Botón "Unirse a Videollamada" aparece en detalle de clase
```

### Código Relevante

En `app/routes.py` (línea 191):

```python
link_jitsi = f"https://{current_app.config.get('JITSI_SERVER', 'meet.jit.si')}/clase-{uuid.uuid4().hex[:10]}"
```

**Explicación**:
- `uuid.uuid4().hex[:10]`: Genera un ID único de 10 caracteres
- Ejemplo de sala: `clase-a3b7c9d2ef`
- Cada clase tiene una sala única que nadie más puede adivinar

### Seguridad del Link

✅ **Único por clase**: UUID aleatorio  
✅ **No predecible**: Imposible de adivinar  
✅ **Solo visibles**: Para estudiante y docente de la clase  
✅ **Solo cuando confirmada**: No aparece si no se ha pagado  

---

## 👨‍🎓 MANUAL DE USO PARA ESTUDIANTES

### Cómo Unirse a una Videollamada

#### Opción 1: Desde "Detalle de Clase"

1. Ve a **Dashboard** → **Mis Clases**
2. Click en la clase que deseas
3. Verás un botón verde: **"Unirse a la Videollamada"** (solo si está confirmada)
4. Click en el botón
5. Se abre Jitsi Meet en nueva pestaña

#### Opción 2: Desde "Mis Clases"

1. Ve a **Dashboard** → **Mis Clases**
2. En la lista de clases, busca la clase próxima
3. Click en el icono de video 🎥
4. Se abre Jitsi Meet

### Primera Vez Usando Jitsi Meet

#### Paso 1: Permisos del Navegador

Al abrir Jitsi por primera vez, el navegador pedirá permisos:

1. **Permitir acceso a cámara**: Click en "Permitir"
2. **Permitir acceso a micrófono**: Click en "Permitir"

⚠️ **Importante**: Sin estos permisos, no podrás ser visto ni escuchado.

#### Paso 2: Configurar Audio y Video

Antes de unirte:

1. Verás una vista previa de tu cámara
2. Verifica que te veas correctamente
3. Habla y verifica el indicador de micrófono
4. Si no funciona, click en ⚙️ (Configuración) para cambiar dispositivos

#### Paso 3: Ingresar tu Nombre

Jitsi pedirá tu nombre:
- Ya viene pre-llenado con tu nombre de Aula Virtual
- Puedes cambiarlo si deseas
- Click en "Unirse a la reunión"

### Controles de la Videollamada

#### Barra Inferior (Controles Principales)

| Icono | Función | Atajo |
|-------|---------|-------|
| 🎤 | Silenciar/activar micrófono | M |
| 📹 | Encender/apagar cámara | V |
| 🖥️ | Compartir pantalla | D |
| ✋ | Levantar mano | R |
| 💬 | Abrir chat | C |
| 👥 | Ver participantes | P |
| ... | Más opciones | |
| 📞 | Salir de la llamada | |

#### Más Opciones (...)

- **Estadísticas**: Ver calidad de conexión
- **Vista**: Cambiar entre vista de cuadrícula o presentador
- **Fondo difuminado**: Difuminar tu fondo
- **Configuración**: Cambiar dispositivos, calidad, etc.

### Consejos para una Buena Clase

#### Antes de la Clase

✅ **Prueba tu equipo**: Únete 5 minutos antes  
✅ **Buena iluminación**: Colócate frente a una ventana o luz  
✅ **Fondo despejado**: Evita distracciones en el fondo  
✅ **Internet estable**: Usa cable Ethernet si es posible  
✅ **Auriculares**: Evitan eco y mejoran audio  

#### Durante la Clase

✅ **Micrófono silenciado**: Actívalo solo al hablar  
✅ **Cámara encendida**: Ayuda a la interacción  
✅ **Chat**: Usa el chat para preguntas sin interrumpir  
✅ **Levantar mano**: Usa 🙋 para pedir la palabra  
✅ **No grabes**: Respeta la privacidad del docente  

### Solución de Problemas Comunes

#### Problema: "No me escuchan"

1. Verifica que el micrófono no esté silenciado (🎤)
2. Click en ⚙️ → Dispositivos de audio
3. Selecciona el micrófono correcto
4. Habla y verifica el indicador de nivel
5. Prueba con otro navegador (Chrome recomendado)

#### Problema: "No me ven"

1. Verifica que la cámara esté encendida (📹)
2. Click en ⚙️ → Dispositivos de video
3. Selecciona la cámara correcta
4. Verifica permisos del navegador
5. Cierra otras apps que puedan usar la cámara (Zoom, Skype, etc.)

#### Problema: "Se traba el video"

1. Apaga tu cámara temporalmente
2. Click en ⚙️ → Calidad de video → Baja
3. Cierra otras pestañas/programas
4. Acerca tu dispositivo al router
5. Pide a otros que apaguen su cámara

#### Problema: "Eco de audio"

1. Usa auriculares
2. Baja el volumen de tus parlantes
3. Pide a otros participantes que se silencien cuando no hablen

---

## 👨‍🏫 MANUAL DE USO PARA DOCENTES

### Antes de Empezar

Como docente, tienes roles adicionales en la videollamada:

✅ **Moderador**: Primer participante es automáticamente moderador  
✅ **Silenciar todos**: Puedes silenciar a todos los participantes  
✅ **Expulsar**: Puedes expulsar participantes disruptivos  
✅ **Grabar**: Puedes iniciar grabación (si está habilitado)  

### Preparación de la Clase

#### 1 Semana Antes

- [ ] Confirma que la clase esté reservada y pagada
- [ ] Revisa el material que compartirás
- [ ] Prepara slides o documentos (formato PDF recomendado)

#### 1 Día Antes

- [ ] Prueba tu equipo (cámara, micrófono, internet)
- [ ] Prueba compartir pantalla
- [ ] Ten el link de Jitsi a mano

#### 30 Minutos Antes

- [ ] Únete a la sala de Jitsi
- [ ] Verifica audio y video
- [ ] Ten materiales abiertos y listos
- [ ] Silencia notificaciones

### Durante la Clase

#### Inicio de la Clase (5 min)

1. **Bienvenida**: Saluda a cada estudiante que ingresa
2. **Verificación técnica**: ¿Todos me ven y escuchan?
3. **Reglas básicas**:
   - Micrófonos silenciados cuando no hablen
   - Usar 🙋 para levantar mano
   - Chat abierto para preguntas
4. **Agenda**: Explica qué se verá en la clase

#### Desarrollo de la Clase

**Técnicas de Enseñanza Virtual**:

1. **Pausas frecuentes**: Pregunta si hay dudas cada 10-15 min
2. **Interacción**: Hacer preguntas directas a estudiantes
3. **Compartir pantalla**: Para mostrar ejemplos
4. **Pizarra virtual**: Usa herramientas de dibujo
5. **Chat**: Lee el chat regularmente

**Controles de Moderador**:

| Acción | Cómo Hacerlo |
|--------|--------------|
| Silenciar a todos | Click en 👥 → "..." → Silenciar todos |
| Silenciar a uno | Click en participante → Silenciar |
| Expulsar | Click en participante → Expulsar |
| Iniciar grabación | Click en "..." → Iniciar grabación |
| Finalizar para todos | Click en 📞 → Finalizar reunión para todos |

#### Compartir Pantalla Efectivamente

**Qué Compartir**:
- ✅ Ventana específica (navegador, PDF, IDE)
- ✅ Ventana de aplicación
- ❌ Pantalla completa (muestra notificaciones)

**Cómo**:
1. Click en 🖥️ (Compartir pantalla)
2. Selecciona "Ventana" (no "Pantalla completa")
3. Elige la ventana que quieres compartir
4. Click en "Compartir"

**Consejos**:
- Cierra pestañas/ventanas innecesarias
- Desactiva notificaciones
- Aumenta zoom para que se vea bien
- Pregunta frecuentemente si se ve bien

#### Cierre de la Clase (5 min)

1. **Resumen**: Recapitula lo visto
2. **Tarea**: Si hay, explicarla claramente
3. **Preguntas finales**: Tiempo para dudas
4. **Despedida**: Agradece la participación
5. **Finalizar**: Click en 📞 → "Finalizar"

### Después de la Clase

- [ ] Envía materiales por email o en plataforma
- [ ] Responde dudas por chat si quedan
- [ ] Toma notas de mejoras para próxima clase

### Funciones Avanzadas para Docentes

#### Grabación de Clase

**⚠️ Importante**: Siempre informa que vas a grabar

```
Servidor público (meet.jit.si):
- Grabación se guarda en Dropbox (requiere cuenta)
- Calidad limitada

Servidor propio:
- Grabación local en el servidor
- Mejor calidad
- Más control
```

**Cómo Grabar**:
1. Click en "..." → "Iniciar grabación"
2. Aparecerá indicador "REC" en rojo
3. Al terminar: "..." → "Detener grabación"

#### Pizarra Virtual

Para escribir/dibujar en pantalla compartida:

1. Comparte pantalla
2. Click en "..." → "Inicio etherpad" (si disponible)
3. O usa herramientas externas como:
   - Google Jamboard
   - Microsoft Whiteboard
   - Miro

#### Breakout Rooms (Salas Separadas)

**No disponible nativamente**, pero puedes:

1. Crear múltiples clases con links diferentes
2. Dividir estudiantes en grupos
3. Enviar link a cada grupo
4. Visitar cada sala

### Métricas de Calidad

**Indicadores de buena conexión**:
- Barras verdes en estadísticas
- Sin lag al hablar
- Video fluido sin pixelado

**Indicadores de problemas**:
- Barras rojas/amarillas
- Video entrecortado
- Audio con eco o cortes

### Casos Especiales

#### Estudiante con Problemas Técnicos

1. Pídele que recargue la página
2. Sugiérele apagar cámara (solo audio)
3. Como último recurso:llamada telefónica
4. Continúa la clase, no esperes mucho

#### Participante Disruptivo

1. Siléncialo
2. Si persiste, escríbele por chat privado
3. Si continúa, expúlsalo: Click en su nombre → Expulsar

#### Internet Inestable (Tuyo)

1. Apaga tu cámara (mantén audio)
2. Pide que otros apaguen cámaras
3. Si se cae, reúnete por celular
4. Avisa que habrá reprogramación si es necesario

---

## 🎨 PERSONALIZACIÓN AVANZADA

### Servidor Propio: Personalización Completa

Si tienes tu propio servidor, puedes personalizar:

#### Cambiar Logo

```bash
# Reemplazar logo
sudo cp tu-logo.png /usr/share/jitsi-meet/images/watermark.png

# Reiniciar
sudo systemctl restart nginx
```

#### Cambiar Colores

Editar `/usr/share/jitsi-meet/interface_config.js`:

```javascript
// Cambiar colores de la interfaz
var interfaceConfig = {
    // Tu color principal
    DEFAULT_BACKGROUND: '#474747',
    
    // Color de botones
    DEFAULT_LOCAL_DISPLAY_NAME: 'yo',
    DEFAULT_REMOTE_DISPLAY_NAME: 'Participante',
    
    // Mostrar tu marca
    SHOW_JITSI_WATERMARK: false,
    SHOW_WATERMARK_FOR_GUESTS: false
};
```

#### Textos Personalizados

Editar `/usr/share/jitsi-meet/lang/main-es.json`:

```json
{
    "welcomepage": {
        "title": "Aula Virtual - Clases en Línea",
        "appDescription": "Plataforma de educación online"
    }
}
```

### Integración con iframe (Avanzado)

En lugar de abrir en nueva pestaña, puedes embeber Jitsi:

```html
<!-- En el template de clase -->
<iframe
    allow="camera; microphone; fullscreen"
    src="https://meet.jit.si/clase-{{ clase.id }}"
    style="height: 600px; width: 100%; border: 0;">
</iframe>
```

---

## 🔧 TROUBLESHOOTING

### Problemas del Servidor Público

#### "No puedo crear sala"

**Causa**: Servidor sobrecargado  
**Solución**: Espera unos minutos o usa servidor propio

#### "Video de baja calidad"

**Causa**: Muchos usuarios simultáneos  
**Solución**: 
- Baja resolución en configuración
- Considera servidor propio

### Problemas del Servidor Propio

#### "Error al conectar"

```bash
# Verificar servicios
sudo systemctl status prosody
sudo systemctl status jicofo
sudo systemctl status jitsi-videobridge2

# Si alguno está caído, reiniciar
sudo systemctl restart prosody jicofo jitsi-videobridge2
```

#### "Certificado SSL expirado"

```bash
# Renovar Let's Encrypt
sudo certbot renew

# Reiniciar nginx
sudo systemctl restart nginx
```

#### "No se conectan más de 2 personas"

**Causa**: Firewall bloqueando puertos UDP  
**Solución**:

```bash
# Abrir puerto UDP 10000
sudo ufw allow 10000/udp

# Verificar
sudo ufw status
```

### Logs Útiles

```bash
# Logs de Prosody (XMPP)
sudo tail -f /var/log/prosody/prosody.log

# Logs de Videobridge
sudo tail -f /var/log/jitsi/jvb.log

# Logs de Jicofo
sudo tail -f /var/log/jitsi/jicofo.log
```

---

## 📊 ESTADÍSTICAS Y MONITOREO

### Métricas Importantes

Si tienes servidor propio, puedes monitorear:

- Número de salas activas
- Participantes simultáneos
- Ancho de banda usado
- Calidad de conexiones (packet loss, jitter)

### Herramientas de Monitoreo

```bash
# Instalar grafana y prometheus (opcional)
# Ver guía oficial: https://jitsi.github.io/handbook/docs/devops-guide/monitoring
```

---

## 📚 RECURSOS ADICIONALES

### Documentación Oficial

- **Jitsi Meet**: https://jitsi.github.io/handbook/
- **Guía de DevOps**: https://jitsi.github.io/handbook/docs/devops-guide
- **API**: https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe

### Comunidad

- **Foro**: https://community.jitsi.org/
- **GitHub**: https://github.com/jitsi/jitsi-meet

### Alternativas a Considerar

Si Jitsi no cumple tus necesidades:

- **BigBlueButton**: Específico para educación
- **Zoom SDK**: Requiere cuenta paga
- **Microsoft Teams**: Para instituciones con licencia
- **Google Meet**: Requiere cuenta de Google Workspace

---

## 🎓 MEJORES PRÁCTICAS

### Para Instituciones Grandes

Si planeas escalar a cientos de usuarios:

1. **Servidor Propio**: Imprescindible
2. **Cluster**: Múltiples servidores para balanceo de carga
3. **CDN**: Para servir assets estáticamente
4. **Monitoring**: Prometheus + Grafana
5. **Backups**: De configuración y grabaciones

### Cumplimiento Legal

Si grabas clases:

- ⚠️ **Informa siempre**: Avisa que vas a grabar
- ⚠️ **Consentimiento**: Obtén consentimiento de participantes
- ⚠️ **Almacenamiento**: Cumple con GDPR/leyes locales
- ⚠️ **Retención**: Define política de cuánto tiempo guardar

---

**Elaborado por**: Equipo de Desarrollo de Aula Virtual  
**Soporte**: soporte@aulavirtual.com  
**Última actualización**: Marzo 2026

---
