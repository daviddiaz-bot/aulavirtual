# Mejora de Seguridad - Prevención de Reutilización de Enlaces Jitsi

## Problema Detectado

Aunque implementamos el control de acceso a través de nuestra plataforma, los enlaces de Jitsi Meet podían ser guardados y reutilizados directamente, saltándose nuestras validaciones de:
- Acceso único
- Cierre automático de clases
- Control de conexiones

## Solución Implementada

### Sistema de Regeneración de Enlaces

El sistema ahora regenera automáticamente los enlaces de Jitsi después del primer acceso, invalidando los enlaces anteriores.

### Cómo Funciona

1. **Creación de Clase**: Se genera un enlace único inicial
2. **Primer Acceso**: Docente y estudiante pueden acceder con el mismo enlace
3. **Regeneración Automática**: Después de que ambos se conecten por primera vez, el enlace se regenera
4. **Enlaces Antiguos Invalidados**: Los enlaces guardados anteriormente ya no funcionan

### Características

#### Campos Nuevos en el Modelo `Clase`
```python
regenerar_link: bool          # Controla si se debe regenerar el enlace
link_jitsi_usado: bool        # Marca si el enlace actual fue usado
```

#### Método `generar_nuevo_link_jitsi()`
- Genera un enlace único con timestamp y UUID
- Formato: `aulavirtual-{id_clase}-{timestamp}-{uuid}`
- Previene colisiones y duplicados
- Marca el enlace anterior como usado

#### Método `registrar_acceso()` Mejorado
- Registra cada conexión (estudiante/docente)
- Marca el enlace como usado
- Regenera automáticamente después del primer acceso de ambos
- Respeta la configuración `regenerar_link` de cada clase

### Configuración por Clase

Los administradores pueden:
- ✅ Activar/desactivar regeneración por clase
- ✅ Crear clases con enlaces permanentes (no se regeneran)
- ✅ Ver si un enlace ya fue usado

### Flujo de Seguridad

```
1. Clase Creada
   └─> Link: aulavirtual-123-1234567890-abc123de
   
2. Estudiante Accede
   └─> Link marcado como "usado"
   └─> Conexiones_estudiante: 1
   
3. Docente Accede
   └─> Conexiones_docente: 1
   └─> REGENERACIÓN AUTOMÁTICA
   └─> Nuevo Link: aulavirtual-123-1234567891-xyz789fg
   
4. Intentos Posteriores
   └─> Link antiguo guardado: ❌ NO FUNCIONA
   └─> Deben acceder desde la plataforma: ✓ Obtienen nuevo link
```

### Beneficios de Seguridad

1. **Previene Compartir Enlaces**: Los enlaces no se pueden compartir fuera de la plataforma
2. **Control Total**: Todo acceso pasa por nuestras validaciones
3. **Auditoría**: Sabemos cuántas veces y cuándo se conectaron
4. **Flexibilidad**: Se puede desactivar para casos especiales

## Archivos Modificados

### Backend
- `app/models.py`: Nuevos campos y métodos
- `app/routes.py`: Uso de `generar_nuevo_link_jitsi()`
- `app/admin.py`: Configuración de regeneración en clases especiales

### Frontend
- `app/templates/admin/crear_clase.html`: Toggle para regeneración de links

### Migración
- `migrar_seguridad_jitsi.py`: Script de migración de BD

## Instalación

```bash
# 1. Activar entorno virtual
.venv\Scripts\activate  # Windows

# 2. Ejecutar migración
python migrar_seguridad_jitsi.py --auto

# 3. Reiniciar servidor
```

## Configuración

### Por Defecto
Todas las clases nuevas tienen `regenerar_link=True`

### Desactivar para Clase Específica

**Como Administrador al crear clase**:
1. Ir a Admin → Clases → Crear Clase Especial
2. Desmarcar "Regenerar Enlace"
3. El enlace será permanente durante toda la clase

### En Código
```python
clase = Clase(
    # ... otros campos ...
    regenerar_link=False  # Mantener enlace permanente
)
```

## Casos de Uso

### Clase Normal (Regenerar Activado)
- ✅ Máxima seguridad
- ✅ Previene compartir enlaces
- ✅ Control total de accesos

### Clase Especial (Regenerar Desactivado)
- ✅ Enlace permanente para múltiples usos
- ✅ Útil para clases recurrentes con mismo grupo
- ⚠️ Menor seguridad

### Clase con Acceso Único
- ✅ Solo una conexión por persona
- ✅ Link se regenera pero ya no sirve para reentrar
- ✅ Combinación más segura

## Comportamiento Detallado

| Escenario | Acceso Único | Regenerar Link | Resultado |
|-----------|--------------|----------------|-----------|
| Primera vez ambos | ✓ | ✓ | Acceso permitido, link regenera después |
| Primera vez ambos | ✓ | ✗ | Acceso permitido, link no cambia |
| Segunda vez estudiante | ✓ | ✓/✗ | Acceso denegado (acceso único) |
| Segunda vez estudiante | ✗ | ✓ | Debe obtener nuevo link desde plataforma |
| Segunda vez estudiante | ✗ | ✗ | Puede usar link guardado |

## Verificación

Para probar que funciona:

1. **Crear clase de prueba** con regeneración activada
2. **Acceder como estudiante** y copiar el enlace Jitsi
3. **Acceder como docente**
4. **Intentar usar el enlace copiado**: ❌ No encontrará la sala o será diferente
5. **Acceder desde la plataforma**: ✓ Obtiene el nuevo enlace

## Próximas Mejoras Sugeridas

- [ ] Historial de enlaces generados (auditoría completa)
- [ ] Notificación cuando se regenera un enlace
- [ ] Configuración global de regeneración por defecto
- [ ] Integración con JWT tokens para Jitsi (servidor propio)
- [ ] Restricción por IP adicional

## Soporte

Si encuentras algún problema:
1. Verifica que la migración se ejecutó correctamente
2. Revisa que `regenerar_link` esté en True/False según desees
3. Comprueba los logs de acceso a la clase
4. Contacta al equipo técnico

---

**Versión**: 2.2.0  
**Fecha**: Marzo 2026  
**Prioridad**: Alta - Mejora de Seguridad
