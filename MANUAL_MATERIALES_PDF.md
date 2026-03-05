# 📚 Manual del Sistema de Materiales PDF

## 🎯 Funcionalidad Implementada

El sistema permite a los docentes:
- ✅ Subir archivos PDF (máximo 3 MB por archivo)
- ✅ Límite de 5 archivos por docente
- ✅ Compartir PDFs con estudiantes específicos
- ✅ Gestionar sus materiales (eliminar, descargar)

Los estudiantes pueden:
- ✅ Ver materiales compartidos con ellos
- ✅ Descargar PDFs compartidos

Los administradores pueden:
- ✅ Ver todos los materiales del sistema
- ✅ Filtrar por docente o buscar por título
- ✅ Depurar (eliminar) cualquier material
- ✅ Ver estadísticas de uso

---

## 📦 Archivos Creados/Modificados

### Modelos (app/models.py)
- ✅ Tabla `material_estudiante` para relación many-to-many
- ✅ Campo `estudiantes_compartidos` en modelo Material

### Rutas Principales (app/routes.py)
- ✅ `/docente/materiales` - Vista de materiales del docente
- ✅ `/docente/materiales/subir` - Subir PDF (POST)
- ✅ `/docente/materiales/<id>/compartir` - Compartir con estudiantes (POST)
- ✅ `/docente/materiales/<id>/eliminar` - Eliminar material (POST)
- ✅ `/materiales/<id>/descargar` - Descargar PDF
- ✅ `/estudiante/materiales` - Vista de materiales del estudiante

### Rutas Admin (app/admin.py)
- ✅ `/admin/materiales` - Vista de gestión de materiales
- ✅ `/admin/materiales/<id>/eliminar` - Depurar material (POST)
- ✅ `/admin/materiales/<id>/detalles` - Ver detalles completos

### Plantillas Creadas
- ✅ `app/templates/docentes/materiales.html` - Panel del docente
- ✅ `app/templates/clases/materiales_estudiante.html` - Vista estudiante
- ✅ `app/templates/admin/materiales.html` - Panel admin
- ✅ `app/templates/admin/detalle_material.html` - Detalles material

### Plantillas Modificadas
- ✅ `app/templates/dashboard/docente.html` - Enlace a materiales
- ✅ `app/templates/dashboard/cliente.html` - Enlace a materiales
- ✅ `app/templates/admin/dashboard.html` - Enlace a gestión

### Scripts
- ✅ `migrar_materiales.py` - Script de migración DB

### Directorios
- ✅ `app/static/uploads/materiales/` - Almacenamiento de PDFs

---

## 🚀 Despliegue por SSH

### 1. Conectarse al Servidor

```bash
ssh tu-usuario@tu-servidor.com
```

### 2. Navegar al Proyecto

```bash
cd /ruta/a/AulaVirtual
```

### 3. Actualizar Código desde Google Drive

Si usas sincronización automática (rclone o similar):
```bash
# Verificar que los archivos están actualizados
ls -la app/templates/docentes/materiales.html
ls -la app/admin.py
```

O si usas Git:
```bash
git pull origin main
```

### 4. Ejecutar Migración de Base de Datos

```bash
# Opción A: Con Docker (Recomendado)
docker-compose exec web python migrar_materiales.py

# Opción B: Sin Docker  
python migrar_materiales.py
```

Deberías ver:
```
============================================================
MIGRACIÓN: Sistema de Materiales PDF
============================================================

✓ Tabla 'material_estudiante' verificada/creada correctamente
✓ Todas las tablas del sistema están actualizadas
✓ Migración completada

============================================================
Migración finalizada
============================================================
```

### 5. Crear Directorio de Uploads

```bash
# Con Docker
docker-compose exec web mkdir -p app/static/uploads/materiales

# Sin Docker
mkdir -p app/static/uploads/materiales
chmod 755 app/static/uploads/materiales
```

### 6. Reiniciar el Servidor

```bash
# Opción A: Docker Compose (Recomendado)
docker-compose restart web

# Opción B: Rebuild si hay cambios en dependencias
docker-compose build web && docker-compose up -d web

# Opción C: Systemd
sudo systemctl restart aulavirtual
```

### 7. Verificar Funcionamiento

```bash
# Ver logs
docker-compose logs -f web

# O últimas 50 líneas
docker-compose logs --tail=50 web
```

---

## 🧪 Probar la Funcionalidad

### Como Docente:
1. Inicia sesión con cuenta de docente
2. Ve al Dashboard → **Mis Materiales PDF**
3. Sube un PDF (máx 3 MB)
4. Haz clic en el botón de compartir (verde)
5. Selecciona estudiantes
6. Guarda

### Como Estudiante:
1. Inicia sesión con cuenta de estudiante
2. Ve al Dashboard → **Mis Materiales PDF**
3. Verás los PDFs compartidos contigo
4. Descarga cualquier PDF

### Como Administrador:
1. Inicia sesión como admin
2. Ve al Panel Admin → **Gestionar Materiales**
3. Filtra por docente o busca
4. Puedes ver detalles o eliminar materiales

---

## 📝 Actualizar Git y Google Drive

### Actualizar Git:

```bash
# Añadir archivos nuevos
git add app/models.py
git add app/routes.py
git add app/admin.py
git add app/templates/docentes/materiales.html
git add app/templates/clases/materiales_estudiante.html
git add app/templates/admin/materiales.html
git add app/templates/admin/detalle_material.html
git add app/templates/dashboard/docente.html
git add app/templates/dashboard/cliente.html
git add app/templates/admin/dashboard.html
git add migrar_materiales.py
git add app/static/uploads/materiales/.gitkeep
git add MANUAL_MATERIALES_PDF.md

# Commit
git commit -m "Feat: Sistema de materiales PDF para docentes

- Permite a docentes subir PDFs (max 3MB, 5 archivos)
- Compartir PDFs con estudiantes específicos
- Panel de gestión para administradores
- Límites configurables
- Tabla material_estudiante para relación many-to-many"

# Push
git push origin main
```

### Sincronizar con Google Drive:

Los archivos ya están en Google Drive ("Mi unidad"). Para asegurar sincronización:

1. **Verificar estado de sincronización:**
   - Revisa el ícono de Google Drive en el explorador
   - Asegúrate que los archivos modificados tengan el check verde

2. **Forzar sincronización si es necesario:**
   - Click derecho en la carpeta "AulaVirtual"
   - Selecciona "Disponible sin conexión" o "Sincronizar ahora"

3. **Desde SSH (si usas rclone):**
   ```bash
   # Sincronizar desde Drive al servidor
   rclone sync drive:AulaVirtual /ruta/servidor/AulaVirtual
   ```

---

## 🔐 Seguridad

✅ **Validaciones implementadas:**
- Solo archivos PDF permitidos
- Tamaño máximo de 3 MB por archivo
- Límite de 5 archivos por docente
- Verificación de permisos antes de descargar
- Solo docentes pueden subir
- Solo estudiantes compartidos pueden descargar
- Admin puede gestionar todo

---

## ✅ Checklist de Despliegue

- [ ] Conectar por SSH al servidor
- [ ] Actualizar código (git pull o sincronización Google Drive)
- [ ] Ejecutar migración: `python migrar_materiales.py`
- [ ] Crear directorio uploads: `mkdir -p app/static/uploads/materiales`
- [ ] Reiniciar servidor: `docker-compose restart web`
- [ ] Verificar logs: `docker-compose logs -f web`
- [ ] Probar como docente: subir PDF
- [ ] Probar como estudiante: ver materiales
- [ ] Probar como admin: gestionar materiales
- [ ] Commit a Git
- [ ] Verificar sincronización Google Drive

---

**¡Sistema de Materiales PDF implementado con éxito! 🎉**
