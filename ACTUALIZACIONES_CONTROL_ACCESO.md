# Actualizaciones del Sistema - Control de Acceso y Disponibilidad Horaria

## Resumen de Cambios

Este documento detalla las mejoras implementadas en el sistema de Aula Virtual para resolver problemas y agregar nuevas funcionalidades.

## 1. Corrección de Error 500 en Perfil de Administrador

### Problema
Cuando un administrador accedía a su perfil, se producía un error 500 debido a una ruta faltante para cambiar contraseña.

### Solución
- Se agregó la ruta `/cambiar-password` en `auth.py`
- La ruta permite cambiar la contraseña del usuario autenticado
- Valida contraseña actual, longitud mínima y coincidencia de nueva contraseña

### Archivos Modificados
- `app/auth.py`: Se agregó función `cambiar_password()`

---

## 2. Sistema de Disponibilidad Horaria para Docentes

### Descripción
Los docentes ahora pueden definir sus horarios disponibles para evitar que se agenden clases en momentos inconvenientes.

### Funcionalidades

#### Disponibilidad Semanal
- Los docentes pueden definir franjas horarias por día de la semana
- Ejemplo: Lunes 09:00-12:00, Martes 14:00-18:00, etc.
- Los estudiantes solo podrán reservar en esos horarios

#### Bloques No Disponibles
- Permite bloquear fechas/horas específicas
- Ideal para vacaciones, eventos personales, compromisos, etc.
- Incluye campo de motivo (opcional)

### Acceso
- **Docentes**: Menú superior → "Disponibilidad"
- **URL**: `/disponibilidad`

### Modelos Creados
1. **DisponibilidadDocente**: Horarios semanales recurrentes
   - `dia_semana`: 0=Lunes, 1=Martes... 6=Domingo
   - `hora_inicio`, `hora_fin`: Rango horario
   - `activo`: Si está activo o no

2. **BloqueNoDisponible**: Fechas específicas bloqueadas
   - `fecha_inicio`, `fecha_fin`: Rango de fechas
   - `motivo`: Razón del bloqueo (opcional)

### Validación Automática
Al reservar una clase, el sistema verifica:
1. No hay clases confirmadas en ese horario
2. El horario está dentro de la disponibilidad semanal del docente
3. No está en un bloque bloqueado

### Archivos Modificados
- `app/models.py`: Nuevos modelos `DisponibilidadDocente` y `BloqueNoDisponible`
- `app/routes.py`: Rutas para gestionar disponibilidad
- `app/templates/docentes/disponibilidad.html`: Nueva plantilla
- `app/templates/base.html`: Agregado enlace en menú

---

## 3. Control de Acceso a Clases

### Problema
Una vez iniciada una clase, tanto docentes como estudiantes podían conectarse ilimitadamente, generando uso indebido de las salas.

### Solución Implementada

#### Cierre Automático de Clases
- Las clases se cierran automáticamente después de su `fecha_fin`
- El método `cerrar_automaticamente()` marca la clase como cerrada
- Se ejecuta al intentar acceder a una clase

#### Acceso Único (Opcional)
- Por defecto, cada persona (docente/estudiante) solo puede conectarse una vez
- El administrador puede desactivar esto al crear clases especiales
- Se registra:
  - Primera conexión de estudiante/docente
  - Número de conexiones de cada uno

#### Validación de Acceso
Nueva ruta `/clase/<id>/unirse` que:
1. Verifica permisos del usuario
2. Comprueba si la clase está cerrada
3. Valida acceso único si está activado
4. Registra la conexión
5. Redirige a Jitsi

### Nuevos Campos en Modelo Clase
```python
clase_cerrada: bool           # Si fue cerrada automáticamente
fecha_cierre: datetime       # Cuándo se cerró
acceso_unico: bool           # Si permite solo un acceso
conexiones_estudiante: int   # Número de conexiones del estudiante
conexiones_docente: int      # Número de conexiones del docente
primera_conexion_estudiante: datetime
primera_conexion_docente: datetime
```

### Archivos Modificados
- `app/models.py`: Campos y métodos en modelo `Clase`
- `app/routes.py`: Nueva ruta `unirse_clase()`
- `app/templates/clases/detalle.html`: Botón actualizado
- `app/templates/clases/mis_clases.html`: Enlaces actualizados
- `app/templates/dashboard/docente.html`: Enlaces actualizados

---

## 4. Clases Especiales Sin Costo (Administrador)

### Descripción
Los administradores pueden crear clases directamente sin que el estudiante tenga que pagar, útil para:
- Clases de cortesía
- Clases de recuperación
- Sesiones especiales
- Pruebas o demostraciones

### Funcionalidades

#### Crear Clase Especial
- **Acceso**: Panel Admin → Clases → "Crear Clase Especial"
- Permite seleccionar:
  - Estudiante y docente
  - Fecha, hora y duración
  - Si es gratuita o tiene costo
  - Si tiene acceso único o múltiple
  - Notas internas del administrador

#### Características
- Se crea en estado "Confirmada" automáticamente
- Notifica a estudiante y docente
- Si es gratuita, se marca como pagada
- El administrador puede ver notas privadas sobre la clase

### Nuevos Campos en Modelo Clase
```python
es_gratuita: bool          # Si es clase sin costo
creada_por_admin: bool     # Si fue creada por admin
notas_admin: text          # Notas privadas del admin
```

### Archivos Modificados
- `app/admin.py`: Nueva ruta `crear_clase_especial()`
- `app/templates/admin/crear_clase.html`: Nueva plantilla
- `app/templates/admin/clases.html`: Botón agregado

---

## Instalación y Migración

### Pasos para Aplicar los Cambios

1. **Activar entorno virtual**
   ```bash
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Ejecutar migración de base de datos**
   ```bash
   python migrar_db_control_acceso.py
   ```
   
   Este script:
   - Crea las nuevas tablas
   - Agrega columnas faltantes a la tabla `clases`
   - No elimina datos existentes

3. **Verificar cambios**
   - Acceder como administrador y verificar perfil
   - Acceder como docente y configurar disponibilidad
   - Crear una clase especial desde el panel de admin

### Importante
- **Backup**: Se recomienda hacer respaldo de la base de datos antes de migrar
- **Testing**: Probar en ambiente de desarrollo primero
- **Compatibilidad**: Los cambios son retrocompatibles con clases existentes

---

## Guías de Uso

### Para Docentes: Configurar Disponibilidad

1. Ir a **Disponibilidad** en el menú superior
2. **Agregar horarios semanales**:
   - Clic en "Agregar Horario"
   - Seleccionar día de la semana
   - Definir hora inicio y fin
   - Guardar
3. **Bloquear fechas específicas**:
   - Clic en "Bloquear Fechas"
   - Seleccionar rango de fecha/hora
   - Agregar motivo (opcional)
   - Guardar

### Para Administradores: Crear Clase Especial

1. Ir a **Admin → Clases**
2. Clic en **"Crear Clase Especial"**
3. Completar formulario:
   - Seleccionar estudiante y docente
   - Definir fecha, hora y duración
   - Marcar si es gratuita
   - Configurar acceso único si lo deseas
   - Agregar notas internas (opcional)
4. Guardar

La clase se creará automáticamente como confirmada y se notificará a ambas partes.

### Para Estudiantes: Reservar Clases

El proceso sigue igual, pero ahora:
- Solo verás horarios disponibles del docente
- No podrás reservar en horarios bloqueados
- Recibirás notificación si el docente no está disponible

---

## Beneficios de las Mejoras

✅ **Control de acceso**: Evita uso indebido de salas de videoconferencia  
✅ **Disponibilidad clara**: Docentes definen cuándo están disponibles  
✅ **Flexibilidad admin**: Puede crear clases especiales sin pago  
✅ **Mejor experiencia**: Estudiantes ven solo horarios disponibles  
✅ **Registro de conexiones**: Se sabe cuándo y cuántas veces se conectaron  
✅ **Cierre automático**: Las clases finalizan correctamente  

---

## Soporte Técnico

Si encuentras algún problema:
1. Revisa los logs de la aplicación
2. Verifica que la migración se ejecutó correctamente
3. Contacta al equipo técnico con detalles del error

## Próximas Mejoras Sugeridas

- Dashboard de disponibilidad visual (calendario)
- Notificaciones automáticas antes de clases
- Estadísticas de conexiones
- Exportar horarios de disponibilidad
- Integración con Google Calendar

---

**Fecha de Implementación**: Marzo 2026  
**Versión**: 2.1.0
