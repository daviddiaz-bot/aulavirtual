# Limitaciones y Consideraciones de Seguridad - Enlaces Jitsi

## Contexto del Problema

Al usar Jitsi Meet público (meet.jit.si o servidor propio sin autenticación), existe una **limitación inherente de seguridad**:

- Las salas de Jitsi son **públicas** por defecto
- Cualquiera con el enlazpuede entrar a la sala
- **No es posible "invalidar" una sala** desde nuestra aplicación
- Si alguien guarda un enlace, puede usarlo directamente

## ¿Qué Implementamos?

### 1. Control de Acceso en Nuestra Plataforma ✅

- Todo acceso debe pasar por `/clase/<id>/unirse`
- Validaciones: permisos, estado, acceso único, clase cerrada
- Registro de todas las conexiones

### 2. Regeneración Automática de Enlaces ✅

- Los enlaces cambian después del primer acceso de ambos
- Enlaces antiguos guardados llevan a salas diferentes
- Dificulta (pero no imposibilita) la reutilización

### 3. Cierre Automático de Clases ✅

- Las clases se marcan como cerradas después de su horario
- No se permite acceder desde nuestra plataforma a clases cerradas

## Limitaciones Actuales

### ⚠️ Lo que SÍ podemos prevenir:

1. **Acceso sin pago**: Solo usuarios que pagaron pueden obtener el enlace
2. **Acceso fuera de horario**: Clases cerradas no permiten nuevos accesos
3. **Acceso de personas no autorizadas**: Solo docente y estudiante asignados
4. **Múltiples accesos (si está activado)**: Control de acceso único funciona en nuestra plataforma

### ⚠️ Lo que NO podemos prevenir completamente:

1. **Si alguien guarda el enlace exacto**: Puede entrar directamente a Jitsi
   - **Mitigación**: El enlace cambia, entrará a una sala diferente/vacía
   - **Impacto**: Reducido, dificulta pero no elimina completamente

2. **Compartir enlaces**: Si docente/estudiante comparte el enlace con terceros
   - **Mitigación**: El enlace cambia constantemente
   - **Impacto**: La tercera persona entraría a una sala que ya no se usa

3. **Grabaciones de pantalla**: Si guardan el nombre de la sala
   - **Mitigación**: Los nombres incluyen timestamp, no son reutilizable
   - **Impacto**: Muy reducido

## Escenarios y Comportamiento

### Escenario 1: Uso Normal ✅
```
1. Estudiante accede desde plataforma → Entra a sala A
2. Docente accede desde plataforma → Entra a sala A (mismo enlace)
3. Sistema regenera enlace → Sala B creada para próxima vez
4. Si hay segunda sesión → Usarán sala B
```

### Escenario 2: Intento de Reutilizar Enlace ⚠️
```
1. Usuario guarda enlace de sala A
2. Después de clase, enlace cambia a sala B
3. Usuario intenta usar enlace guardado sala A:
   a) Si nadie está → Entra a sala vacía
   b) Si entra por plataforma → Va a sala B (activa)
   → No se encuentran, debe usar plataforma
```

### Escenario 3: Acceso Único + Regeneración ✅
```
1. Primera sesión: Ambos entran con sala A
2. Enlace cambia a sala B
3. Intentos posteriores:
   - Desde plataforma → Denegado (acceso único)
   - Con enlace guardado → Inútil, no pueden acceder de todas formas
```

### Escenario 4: Compartir Enlace ⚠️
```
1. Estudiante comparte enlace sala A con amigo
2. Amigo intenta acceder → Entra a Jitsi directamente
3. Pero:
   a) Si enlace ya cambió → Entra a sala vacía/vieja
   b) Si accede durante la clase → Podría entrar (limitación de Jitsi)
   c) Si acceso único activado → Solo funciona primera vez
```

## Soluciones para Máxima Seguridad

Si necesitas seguridad absoluta, considera:

### Opción 1: Jitsi con JWT (Recomendado) 🔒

**Requisitos**:
- Servidor propio de Jitsi
- Configurar autenticación JWT
- Generar tokens firmados temporalmente

**Ventajas**:
- Control total sobre quién puede entrar
- Tokens expiran automáticamente
- Imposible reutilizar sin nuevo token
- Verificación criptográfica

**Implementación**:
```python
import jwt
from datetime import datetime, timedelta

def generar_token_jitsi(clase, usuario, es_moderador=False):
    payload = {
        'iss': 'tu_app',
        'aud': 'jitsi',
        'exp': datetime.utcnow() + timedelta(hours=2),
        'room': f'clase-{clase.id}',
        'context': {
            'user': {
                'name': usuario.nombre,
                'email': usuario.email,
                'moderator': es_moderador
            }
        }
    }
    token = jwt.encode(payload, JITSI_SECRET, algorithm='HS256')
    return f"https://tu-jitsi.com/clase-{clase.id}?jwt={token}"
```

### Opción 2: Moderación de Sala 🔐

**En Jitsi**:
- Primera persona que entra = moderador
- Solo moderador puede admitir otros
- Configurar sala con contraseña

**En nuestra plataforma**:
```python
# Generar contraseña única por clase
clase.password_jitsi = secrets.token_urlsafe(8)

# Mostrar contraseña solo a usuarios autorizados
# O incluirla en el enlace: sala?pwd=xxx
```

### Opción 3: Webhooks de Jitsi 📡

**Configurar**:
- Webhooks para eventos de entrada/salida
- Verificar en tiempo real quién está en la sala
- Expulsar usuarios no autorizados

### Opción 4: Alternativas a Jitsi

- **Zoom SDK**: Control total con Zoom API
- **Agora SDK**: Video SDK con autenticación
- **Daily.co**: Video API con tokens
- **Twilio Video**: Control granular de acceso

## Recomendación Actual

Para el caso de uso actual (clases 1 a 1):

✅ **La implementación actual es suficiente** porque:

1. Acceso único limita a una conexión por persona
2. Regeneración de enlaces dificulta compartir
3. Cierre automático previene accesos fuera de horario
4. En clases 1 a 1, el docente notaría un intruso inmediatamente

⚠️ **Considera JWT si**:

- Tienes clases grupales grandes
- Manejas contenido muy sensible
- Necesitas cumplimiento normativo estricto
- Quieres auditoría completa de accesos

## Monitoreo y Auditoría

Actualmente registramos:
- ✅ Cuántas veces se conectó cada usuario
- ✅ Timestamp de primera conexión
- ✅ Cuándo se regeneró cada enlace
- ✅ Si la clase fue cerrada automáticamente

Para mejorar:
- [ ] Log de cada intento de acceso (exitoso/rechazado)
- [ ] Alertas si se detectan patrones sospechosos
- [ ] Dashboard de seguridad para administradores

## Conclusión

**Balance actual**: Seguridad buena ✅ para el caso de uso

**Limitaciones**: Existen pero son aceptables para clases 1 a 1

**Próximos pasos**: Implementar JWT si se requiere seguridad máxima

---

**Documentoantiguo**: Marzo 2026  
**Actualizar cuando**: Se implemente JWT o se cambien requisitos de seguridad
