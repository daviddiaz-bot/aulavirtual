# 🔧 TROUBLESHOOTING Y PROBLEMAS RESUELTOS - AULA VIRTUAL

**Versión**: 2.1.0  
**Última actualización**: 6 de Marzo 2026  
**Commits incluidos**: ee11efc hasta d5e9f89 (7 commits)

---

## 📋 ÍNDICE

1. [Error 500: Templates Admin Faltantes](#error-500-templates-admin-faltantes)
2. [Error: Atributos de Modelo Incorrectos](#error-atributos-de-modelo-incorrectos)
3. [Error: Endpoints Incorrectos](#error-endpoints-incorrectos)
4. [Error: Material Upload - Formulario No Aparece](#error-material-upload---formulario-no-aparece)
5. [Error 500: Vista Detalle Material](#error-500-vista-detalle-material)
6. [BuildError: Parámetro Incorrecto en URL](#builderror-parámetro-incorrecto-en-url)
7. [Error 500: Descarga de Materiales](#error-500-descarga-de-materiales)
8. [Login Requiere Checkbox "Recordar"](#login-requiere-checkbox-recordar)
9. [Limpieza de Cache Python](#limpieza-de-cache-python)

---

## Error 500: Templates Admin Faltantes

### 🔴 Síntoma
- Acceder a panel admin → Error 500
- Páginas afectadas: docentes, clases, pagos, reportes, configuración, retiros
- Logs muestran: `TemplateNotFound`

### 🔍 Diagnóstico
```bash
# Verificar templates existentes
ls -la app/templates/admin/

# Revisar logs
docker-compose logs web | grep TemplateNotFound
```

### 💡 Causa Raíz
Templates eliminados accidentalmente por `git clean -fd` en servidor de producción. El comando borró archivos no trackeados que no habían sido commiteados.

### ✅ Solución

**Paso 1: Crear templates faltantes**

```bash
cd app/templates/admin/
```

Crear los 6 archivos necesarios:

**docentes.html**:
```html
{% extends "base.html" %}
{% block title %}Gestión de Docentes - Admin{% endblock %}
{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-12">
            <h2><i class="fas fa-chalkboard-teacher"></i> Gestión de Docentes</h2>
            <!-- Tabs para diferentes vistas -->
            <ul class="nav nav-tabs mb-4">
                <li class="nav-item">
                    <a class="nav-link {% if not filtro or filtro == 'todos' %}active{% endif %}" 
                       href="{{ url_for('admin.docentes') }}">
                        Todos ({{ total }})
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if filtro == 'verificados' %}active{% endif %}" 
                       href="{{ url_for('admin.docentes', filtro='verificados') }}">
                        Verificados ({{ verificados }})
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if filtro == 'pendientes' %}active{% endif %}" 
                       href="{{ url_for('admin.docentes', filtro='pendientes') }}">
                        Pendientes Verificación ({{ pendientes }})
                    </a>
                </li>
            </ul>

            <!-- Tabla de docentes -->
            <div class="card">
                <div class="card-body">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Email</th>
                                <th>Especialidad</th>
                                <th>Precio/Hora</th>
                                <th>Verificado</th>
                                <th>Fecha Registro</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for docente in docentes.items %}
                            <tr>
                                <td>{{ docente.id }}</td>
                                <td>{{ docente.usuario.nombre }} {{ docente.usuario.apellido }}</td>
                                <td>{{ docente.usuario.email }}</td>
                                <td>{{ docente.especialidad or 'No especificada' }}</td>
                                <td>${{ docente.precio_hora or '0.00' }}</td>
                                <td>
                                    {% if docente.verificado %}
                                        <span class="badge bg-success">Verificado</span>
                                    {% else %}
                                        <span class="badge bg-warning">Pendiente</span>
                                    {% endif %}
                                </td>
                                <td>{{ docente.usuario.fecha_registro.strftime('%d/%m/%Y') }}</td>
                                <td>
                                    <a href="{{ url_for('main.perfil_docente', usuario_id=docente.usuario_id) }}" 
                                       class="btn btn-sm btn-info">
                                        <i class="fas fa-eye"></i> Ver
                                    </a>
                                    {% if not docente.verificado %}
                                    <button onclick="verificarDocente({{ docente.id }})" 
                                            class="btn btn-sm btn-success">
                                        <i class="fas fa-check"></i> Verificar
                                    </button>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>

                    <!-- Paginación -->
                    {% if docentes.pages > 1 %}
                    <nav>
                        <ul class="pagination justify-content-center">
                            {% if docentes.has_prev %}
                            <li class="page-item">
                                <a class="page-link" href="{{ url_for('admin.docentes', page=docentes.prev_num, filtro=filtro) }}">
                                    Anterior
                                </a>
                            </li>
                            {% endif %}
                            
                            {% for num in docentes.iter_pages(left_edge=1, right_edge=1, left_current=2, right_current=2) %}
                                {% if num %}
                                <li class="page-item {% if num == docentes.page %}active{% endif %}">
                                    <a class="page-link" href="{{ url_for('admin.docentes', page=num, filtro=filtro) }}">
                                        {{ num }}
                                    </a>
                                </li>
                                {% else %}
                                <li class="page-item disabled"><span class="page-link">...</span></li>
                                {% endif %}
                            {% endfor %}
                            
                            {% if docentes.has_next %}
                            <li class="page-item">
                                <a class="page-link" href="{{ url_for('admin.docentes', page=docentes.next_num, filtro=filtro) }}">
                                    Siguiente
                                </a>
                            </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function verificarDocente(id) {
    if(confirm('¿Verificar este docente?')) {
        fetch(`/admin/docentes/${id}/verificar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                location.reload();
            } else {
                alert('Error al verificar docente');
            }
        });
    }
}
</script>
{% endblock %}
```

**IMPORTANTE**: Crear también:
- `clases.html`
- `pagos.html`
- `reportes.html`
- `configuracion.html`
- `retiros.html`

Seguir la estructura similar al ejemplo de docentes.html.

**Paso 2: Commit y deploy**

```bash
# Agregar los archivos
git add app/templates/admin/*.html

# Commit
git commit -m "Fix: crear templates admin faltantes"

# Push
git push origin main

# En el servidor
cd /root/aulavirtual
git pull origin main
docker-compose restart web
```

### 📝 Prevención
- Nunca ejecutar `git clean -fd` en producción
- Mantener todos los templates en git (commit temprano y frecuente)
- Usar `.gitignore` adecuadamente para no ignorar templates

### 🔗 Commit Relacionado
`ee11efc` - "Create admin templates"

---

## Error: Atributos de Modelo Incorrectos

### 🔴 Síntoma
- Template de docentes muestra error: `AttributeError: 'Docente' object has no attribute 'tarifa_hora'`
- También error con `materias`

### 🔍 Diagnóstico
```python
# Verificar modelo en Python shell
docker-compose exec web python

>>> from app.models import Docente
>>> Docente.__table__.columns.keys()
['id', 'usuario_id', 'especialidad', 'descripcion', 'precio_hora', 'experiencia', 'calificacion_promedio', 'verificado', ...]
```

### 💡 Causa Raíz
El template usaba nombres de atributos antiguos que no coincidían con el modelo actual:
- `docente.tarifa_hora` → Campo correcto: `precio_hora`
- `docente.materias` → Campo correcto: `especialidad`

### ✅ Solución

**Actualizar template con nombres correctos**:

En `app/templates/admin/docentes.html`:

```html
<!-- ANTES (❌ INCORRECTO) -->
<td>${{ docente.tarifa_hora or '0.00' }}</td>
<td>{{ docente.materias }}</td>

<!-- DESPUÉS (✅ CORRECTO) -->
<td>${{ docente.precio_hora or '0.00' }}</td>
<td>{{ docente.especialidad or 'No especificada' }}</td>
```

### 📝 Prevención
- Siempre verificar el esquema del modelo antes de usar atributos
- Usar IDE con autocompletado para detectar errores temprano
- Agregar tests que validen templates con datos reales

### 🔗 Commit Relacionado
`c01c4a8` - "Fix: cambiar tarifa_hora por precio_hora y materias por especialidad"

---

## Error: Endpoints Incorrectos

### 🔴 Síntoma
- Click en "Ver perfil docente" → Error 500
- `BuildError: Could not build url for endpoint 'docentes.perfil'`

### 🔍 Diagnóstico
```bash
# Ver rutas registradas
docker-compose exec web python -c "from app import create_app; app = create_app(); print([str(rule) for rule in app.url_map.iter_rules() if 'perfil' in str(rule)])"
```

### 💡 Causa Raíz
El template intentaba usar `url_for('docentes.perfil', ...)` pero:
1. No existe blueprint llamado `docentes`
2. La ruta correcta está en el blueprint `main`
3. El endpoint real es `perfil_docente`

### ✅ Solución

**Actualizar url_for con blueprint y endpoint correctos**:

```html
<!-- ANTES (❌ INCORRECTO) -->
<a href="{{ url_for('docentes.perfil', id=docente.id) }}">Ver Perfil</a>

<!-- DESPUÉS (✅ CORRECTO) -->
<a href="{{ url_for('main.perfil_docente', usuario_id=docente.usuario_id) }}">Ver Perfil</a>
```

**Nota los 3 cambios**:
1. Blueprint: `docentes` → `main`
2. Endpoint: `perfil` → `perfil_docente`
3. Parámetro: `id` → `usuario_id`

### 📝 Cómo encontrar el endpoint correcto

```python
# Python shell
from app import create_app
app = create_app()

# Ver todas las rutas
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint} -> {rule.rule}")

# Buscar ruta específica
[rule for rule in app.url_map.iter_rules() if 'docente' in rule.endpoint]
```

O revisar el código en `app/routes.py`:

```python
@main.route('/docentes/<int:usuario_id>')
def perfil_docente(usuario_id):
    # Esta es la ruta correcta
    pass
```

### 🔗 Commit Relacionado
`1a3f241` - "Fix: endpoint docentes.perfil → main.perfil_docente"

---

## Error: Material Upload - Formulario No Aparece

### 🔴 Síntoma
- Docente accede a "Mis Materiales"
- No aparece formulario de subida
- Muestra mensaje: "Has alcanzado el límite de 10 materiales"
- Pero el docente no tiene 10 materiales

### 🔍 Diagnóstico
```python
# Verificar materiales del docente en DB
docker-compose exec web python

>>> from app.models import Material, Docente
>>> from app import db
>>> docente_id = 1  # Cambiar por ID real
>>> Material.query.filter_by(docente_id=docente_id).count()
3  # Tiene solo 3 materiales, no 10
```

**Revisar código en routes.py**:
```bash
grep -n "mis_materiales" app/routes.py
```

### 💡 Causa Raíz
Función `mis_materiales()` estaba **duplicada** en el archivo `routes.py`:
- Primera función: líneas ~400-500 (correcta)
- Segunda función: líneas ~712-899 (duplicada, con lógica errónea)

Python ejecutaba la segunda definición (la última carga). Esta función duplicada:
1. No calculaba correctamente `total_materiales`
2. No pasaba la variable `puede_subir` al template
3. El template sin estas variables asumía límite alcanzado

### ✅ Solución

**Paso 1: Identificar y eliminar código duplicado**

```bash
# Encontrar líneas duplicadas
grep -n "def mis_materiales" app/routes.py
# Output: 450:def mis_materiales_docente():
#         713:def mis_materiales_docente():  # DUPLICADO!
```

**Paso 2: Eliminar función duplicada**

Eliminar líneas 712-899 (aproximadamente 187 líneas):

```python
# ELIMINAR ESTA SECCIÓN COMPLETA (líneas 712-899)
@main.route('/mis-materiales')
@login_required
def mis_materiales_docente():
    # ... código duplicado ...
    return render_template('docentes/materiales.html', materiales=materiales)
    # ❌ NO pasa total_materiales ni puede_subir
```

**Paso 3: Verificar función correcta**

Asegurar que la función original esté completa:

```python
@main.route('/mis-materiales')
@login_required
def mis_materiales_docente():
    if not current_user.es_docente:
        flash('Solo los docentes pueden acceder a esta secc ión.', 'warning')
        return redirect(url_for('main.index'))
    
    docente = current_user.docente
    materiales = Material.query.filter_by(docente_id=docente.id).order_by(Material.fecha_subida.desc()).all()
    
    # ✅ IMPORTANTE: Calcular estas variables
    total_materiales = len(materiales)
    puede_subir = total_materiales < 10
    
    # ✅ IMPORTANTE: Pasar todas las variables al template
    return render_template('docentes/materiales.html', 
                         materiales=materiales,
                         total_materiales=total_materiales,
                         puede_subir=puede_subir)
```

**Paso 4: Verificar template**

El template debe usar estas variables:

```html
<!-- docentes/materiales.html -->
{% if puede_subir %}
    <div class="card">
        <div class="card-header">Subir Nuevo Material</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('main.subir_material') }}" enctype="multipart/form-data">
                <!-- Formulario de subida -->
            </form>
        </div>
    </div>
{% else %}
    <div class="alert alert-warning">
        Has alcanzado el límite de {{ total_materiales }} materiales.
    </div>
{% endif %}
```

**Paso 5: Deploy**

```bash
git add app/routes.py
git commit -m "Fix: eliminar función duplicada mis_materiales_docente"
git push origin main

# En servidor
cd /root/aulavirtual
git pull origin main
docker-compose restart web
```

### 📝 Prevención
- Usar IDE con detección de funciones duplicadas
- Code review antes de merge
- Linter configurado: `flake8` o `pylint` detectan funciones duplicadas

```bash
# Instalar y ejecutar flake8
pip install flake8
flake8 app/routes.py | grep "redefinition"
```

### 🔗 Commit Relacionado
`1c0d5dd` - "Fix: eliminar funciones duplicadas de materiales"

---

## Error 500: Vista Detalle Material

### 🔴 Síntoma
- Admin accede a detalle de un material → Error 500
- `AttributeError: 'NoneType' object has no attribute 'usuario'`

### 🔍 Diagnóstico
```python
# Verificar material sin docente
docker-compose exec web python

>>> from app.models import Material
>>> material = Material.query.filter(Material.docente_id.is_(None)).first()
>>> material.docente  # None
>>> material.docente.usuario  # ❌ Error: 'NoneType' object has no attribute 'usuario'
```

### 💡 Causa Raíz
El template `detalle_material.html` asume que todo material tiene un docente asociado y que ese docente tiene un usuario. Pero pueden existir:
1. Materiales sin `docente` (docente_id = NULL)
2. Docentes sin `usuario` (datos huérfanos)

El template accedía directo a `material.docente.usuario.nombre` sin validar si existían.

### ✅ Solución

**Opción A: Validación en Template (Recomendado)**

```html
<!-- ANTES (❌ SIN VALIDACIÓN) -->
<h3>Docente: {{ material.docente.usuario.nombre }}</h3>
<p>Email: {{ material.docente.usuario.email }}</p>

<!-- DESPUÉS (✅ CON VALIDACIÓN) -->
{% if material.docente %}
    {% if material.docente.usuario %}
        <h3>Docente: {{ material.docente.usuario.nombre }} {{ material.docente.usuario.apellido }}</h3>
        <p>Email: {{ material.docente.usuario.email }}</p>
    {% else %}
        <div class="alert alert-warning">
            Usuario del docente no disponible
        </div>
    {% endif %}
{% else %}
    <div class="alert alert-info">
        Este material no tiene docente asociado
    </div>
{% endif %}
```

**Opción B: Validación en Vista**

Agregar validación en `app/admin.py`:

```python
@admin.route('/materiales/<int:material_id>')
@login_required
@admin_required
def detalle_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # ✅ Validación adicional
    if not material.docente:
        flash('Este material no tiene un docente asociado. Por favor, asigna un docente primero.', 'warning')
        return redirect(url_for('admin.materiales'))
    
    if not material.docente.usuario:
        flash('El docente asociado no tiene usuario. Datos inconsistentes.', 'danger')
        return redirect(url_for('admin.materiales'))
    
    return render_template('admin/detalle_material.html', material=material)
```

**Opción C: Ambas (Máxima Robustez)**

Combinar validaciones en vista Y en template para máxima seguridad.

### 📝 Prevención
- Siempre validar relaciones opcionales en templates
- Usar `{% if objeto %}` antes de acceder a atributos
- Considerar agregar constraints NOT NULL en base de datos si la relación es obligatoria

```sql
-- Si TODO material DEBE tener docente:
ALTER TABLE material ALTER COLUMN docente_id SET NOT NULL;
```

### 🔗 Commits Relacionados
- `c221ed6` - "Fix: agregar validación en template detalle_material"
- `5883643` - "Fix: agregar validación adicional en vista admin"

---

## BuildError: Parámetro Incorrecto en URL

### 🔴 Síntoma
- Click en link "Ver usuario" → Error 500
- `werkzeug.routing.BuildError: Could not build url for endpoint 'main.perfil_docente'. Did you mean 'main.perfil'? Did you forget to specify values ['usuario_id']?`

### 🔍 Diagnóstico
El error indica que:
1. El endpoint `main.perfil_docente` requiere parámetro `usuario_id`
2. El template está pasando un parámetro con nombre diferente

**Verificar firma de la ruta**:
```python
# En app/routes.py
@main.route('/docentes/<int:usuario_id>')
def perfil_docente(usuario_id):  # ✅ Espera 'usuario_id'
    pass
```

**Verificar uso en template**:
```html
<!-- Template está usando: -->
{{ url_for('main.perfil_docente', user_id=material.docente.usuario_id) }}
<!-- ❌ Pasa 'user_id' pero la ruta espera 'usuario_id' -->
```

### 💡 Causa Raíz
Mismatch entre el nombre del parámetro en:
- **Definición de ruta**: `usuario_id`
- **Template url_for**: `user_id`

Flask no puede hacer match y lanza BuildError.

### ✅ Solución

**Actualizar template para usar el nombre correcto**:

```html
<!-- ANTES (❌ INCORRECTO) -->
<a href="{{ url_for('main.perfil_docente', user_id=material.docente.usuario_id) }}">
    Ver Usuario
</a>

<!-- DESPUÉS (✅ CORRECTO) -->
<a href="{{ url_for('main.perfil_docente', usuario_id=material.docente.usuario_id) }}">
    Ver Usuario
</a>
```

**Cambio**: `user_id=` → `usuario_id=`

### 📝 Debugging BuildError

Cuando ocurre un BuildError:

**1. Verificar firma de la ruta**:
```python
# Buscar la definición
grep -n "def perfil_docente" app/routes.py
# Verificar parámetros entre <...>
```

**2. Ver todas las rutas con sus parámetros**:
```python
from app import create_app
app = create_app()
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint} {rule.arguments} -> {rule.rule}")
# Output: main.perfil_docente {'usuario_id'} -> /docentes/<int:usuario_id>
```

**3. Comparar con el url_for en template**:
```html
{{ url_for('main.perfil_docente', ???=valor) }}
                                  ^^^
           Este nombre debe estar en rule.arguments
```

### 📝 Prevención
- Usar nombres consistentes en toda la aplicación
- Preferir nombres descriptivos: `usuario_id` en lugar de `user_id` o `id`
- Configurar Jinja2 para modo strict (detecta variables indefinidas)

```python
# En app/__init__.py
app.jinja_env.auto_reload = True
app.jinja_env.autoescape = True
# app.jinja_env.undefined = StrictUndefined  # Detecta errores temprano
```

### 🔗 Commit Relacionado
`5883643` - "Fix: cambiar user_id por usuario_id en url_for"

---

## Error 500: Descarga de Materiales

### 🔴 Síntoma
- Click en "Descargar PDF" → Error 500
- `FileNotFoundError: [Errno 2] No such file or directory: 'static/uploads/materiales/documento.pdf'`

### 🔍 Diagnóstico
```bash
# Verificar estructura de paths
docker-compose exec web python

>>> import os
>>> from flask import current_app
>>> print(os.getcwd())  # /app
>>> print(current_app.root_path)  # /app/app
```

**Problema**: El path relativo `static/uploads/...` se resuelve desde el CWD (Current Working Directory), no desde la raíz de la aplicación Flask.

```python
# ANTES (código problemático)
filepath = os.path.join('static', material.archivo_path)
# Si CWD es /app, busca en: /app/static/...
# Pero los archivos están en: /app/app/static/...
```

### 💡 Causa Raíz
1. **Path relativo incorrecto**: Usaba path relativo al CWD en lugar del root de la app
2. **Parámetro deprecado**: Flask 2.x cambió `attachment_filename` por `download_name`
3. **Sin manejo de errores**: No había try/except para capturar FileNotFoundError

### ✅ Solución

**Actualizar función en `app/routes.py`**:

```python
from flask import send_file, current_app
import os

@main.route('/material/<int:material_id>/descargar')
@login_required
def descargar_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # ✅ SOLUCIÓN 1: Usar current_app.root_path para path absoluto
    filepath = os.path.join(current_app.root_path, 'static', material.archivo_path)
    
    # ✅ SOLUCIÓN 2: Verificar que el archivo existe
    if not os.path.exists(filepath):
        current_app.logger.error(f'Archivo no encontrado: {filepath}')
        flash('El archivo no está disponible.', 'danger')
        return redirect(url_for('main.mis_materiales_docente'))
    
    # Preparar nombre de descarga
    filename = os.path.basename(filepath)
    
    # ✅ SOLUCIÓN 3: Compatibilidad Flask 2.x vs Flask < 2.0
    try:
        # Flask 2.x usa 'download_name'
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except TypeError:
        # Flask < 2.0 usa 'attachment_filename'
        return send_file(
            filepath,
            as_attachment=True,
            attachment_filename=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.error(f'Error al enviar archivo: {str(e)}')
        flash('Error al descargar el archivo.', 'danger')
        return redirect(url_for('main.mis_materiales_docente'))
```

**Explicación de las mejoras**:

1. **Path absoluto con `current_app.root_path`**:
```python
# ANTES
filepath = os.path.join('static', material.archivo_path)
# Busca en: /app/static/... (❌ Incorrecto)

# DESPUÉS
filepath = os.path.join(current_app.root_path, 'static', material.archivo_path)
# Busca en: /app/app/static/... (✅ Correcto)
```

2. **Verificación de existencia**:
```python
if not os.path.exists(filepath):
    # Manejo graceful del error
```

3. **Compatibilidad Flask 2.x**:
```python
try:
    return send_file(..., download_name=filename)  # Flask 2.x
except TypeError:
    return send_file(..., attachment_filename=filename)  # Flask < 2.0
```

### 📝 Testing

```python
# Test en Python shell
docker-compose exec web python

>>> from app import create_app
>>> from app.models import Material
>>> app = create_app()
>>> with app.app_context():
...     material = Material.query.first()
...     filepath = os.path.join(app.root_path, 'static', material.archivo_path)
...     print(f"Path: {filepath}")
...     print(f"Existe: {os.path.exists(filepath)}")
```

### 📝 Prevención
- Siempre usar `current_app.root_path` para paths relativos a la app
- Verificar existencia de archivos antes de send_file
- Agregar logging para debugging
- Tests end-to-end para descarga de archivos

### 🔗 Commit Relacionado
`9d2036d` - "Fix: mejorar descarga de materiales con path absoluto y Flask 2.x compatibility"

---

## Login Requiere Checkbox "Recordar"

### 🔴 Síntoma
- Usuario intenta hacer login SIN marcar checkbox "Recordar"
- Flask redirige de vuelta al login inmediatamente
- No aparece mensaje de error
- Solo funciona si marca "Recordar"

### 🔍 Diagnóstico Completo

**Paso 1: Verificar configuración de sesión**

```bash
docker-compose exec web python -c "from app import create_app; app = create_app(); print('SESSION_COOKIE_SECURE:', app.config.get('SESSION_COOKIE_SECURE'))"
# Output: SESSION_COOKIE_SECURE: True ❌
```

**Paso 2: Verificar protocolo del servidor**

```bash
curl -I http://192.168.1.6
# HTTP/1.1 200 OK
# ❌ Es HTTP, no HTTPS
```

**Paso 3: Entender el problema**

Cuando `SESSION_COOKIE_SECURE = True`:
- Flask setea cookie con flag `Secure`
- Flag `Secure` significa: "Solo enviar en HTTPS"
- Servidor usa HTTP (no HTTPS)
- Navegador rechaza la cookie
- Usuario queda sin sesión
- Flask redirige al login

Cuando usuario marca "Recordar":
- Flask crea cookie persistente diferente
- Esa cookie no tiene el problema del flag Secure
- Por eso funciona

### 💡 Causa Raíz (Multi-layer)

**Layer 1: Valor final en Flask**
```python
# Flask config mostraba:
SESSION_COOKIE_SECURE = True  # ❌ Incorrecto para HTTP
```

**Layer 2: Intentos de fix en .env**
```bash
# .env tenía (correcto):
SESSION_COOKIE_SECURE=False  # ✅

# Pero Flask seguía viendo True ❌
```

**Layer 3: Config.py leía correctamente**
```python
# En config.py
class Config:
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() in ['true', 'on', '1']
    # Con .env = False, esto devuelve False ✅

class ProductionConfig(Config):
    # PROBLEMA: Antes tenía línea hardcoded
    # SESSION_COOKIE_SECURE = True  # ❌ Sobreescribía el valor de Config
```

**Solución Layer 3**: Commit `e26917f` eliminó la línea hardcoded

**Layer 4: Variable no llegaba al container**
```bash
# Verificar env en container
docker-compose exec web printenv | grep SESSION
# ❌ No output - Variable no existe en container!

# Verificar docker-compose.yml
cat docker-compose.yml | grep -A 14 "environment:"
# ❌ SESSION_COOKIE_SECURE no estaba en la lista
```

**ROOT CAUSE**: `docker-compose.yml` no declaraba `SESSION_COOKIE_SECURE` en la sección `environment:`, entonces Docker Compose no la pasaba al contenedor.

### ✅ Solución Completa

**Fix Layer 3: Eliminar override en ProductionConfig**

```python
# ANTES en config.py
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # ❌ ELIMINAR ESTA LÍNEA

# DESPUÉS en config.py
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # SESSION_Cookie_SECURE se hereda de Config ✅
    # que lee correctamente de environ
```

**Fix Layer 4: Agregar variable a docker-compose.yml**

```yaml
# ANTES en docker-compose.yml
services:
  web:
    environment:
      - DATABASE_URL=postgresql://...
      - MAIL_SERVER=${MAIL_SERVER:-smtp.gmail.com}
      - MAIL_PORT=${MAIL_PORT:-587}
      - REDIS_URL=redis://redis:6379/0
      - FLASK_ENV=production
      # ❌ SESSION_COOKIE_SECURE no estaba aquí

# DESPUÉS en docker-compose.yml
services:
  web:
    environment:
      - DATABASE_URL=postgresql://...
      - MAIL_SERVER=${MAIL_SERVER:-smtp.gmail.com}
      - MAIL_PORT=${MAIL_PORT:-587}
      - REDIS_URL=redis://redis:6379/0
      - FLASK_ENV=production
      - SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-False}  # ✅ AGREGADO
```

**Explicación del formato**:
```yaml
- SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-False}
#                         ^                    ^
#                         |                    |
#                Lee de .env            Default si no existe
```

**Deploy completo**:

```bash
# En local
git add config.py docker-compose.yml
git commit -m "Fix: SESSION_COOKIE_SECURE para HTTP environment"
git push origin main

# En servidor
cd /root/aulavirtual
git fetch origin
git reset --hard origin/main  # Cuidado: borra cambios locales

# Reiniciar containers (necesario para nuevas env vars)
docker-compose down
docker-compose up -d
```

**Verificación completa**:

```bash
# 1. Verificar .env tiene la variable
cat /root/aulavirtual/.env | grep SESSION_COOKIE_SECURE
# Output: SESSION_COOKIE_SECURE=False ✅

# 2. Verificar docker-compose.yml la declara
grep "SESSION_COOKIE_SECURE" /root/aulavirtual/docker-compose.yml
# Output: - SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-False} ✅

# 3. Verificar container la recibe
docker-compose exec web printenv | grep SESSION_COOKIE_SECURE
# Output: SESSION_COOKIE_SECURE=False ✅

# 4. Verificar Python la lee
docker-compose exec web python -c "import os; print('ENV:', os.getenv('SESSION_COOKIE_SECURE')); print('Evalúa a:', os.getenv('SESSION_COOKIE_SECURE', 'True').lower() in ['true', 'on', '1'])"
# Output: ENV: False
#         Evalúa a: False ✅

# 5. Verificar Flask la usa (AQUÍ PUEDE FALLAR POR CACHE)
docker-compose exec web python -c "from app import create_app; app = create_app(); print('SESSION_COOKIE_SECURE:', app.config.get('SESSION_COOKIE_SECURE'))"
# Output esperado: SESSION_COOKIE_SECURE: False ✅
# Si output es True: Hay problema de cache __pycache__
```

### 🔴 Si Flask aún muestra True: Problema de Cache

El container puede tener archivos `.pyc` (Python compiled) con la configuración vieja.

**Solución**:

```bash
# Opción 1: Limpiar cache dentro del container
docker-compose exec web find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
docker-compose exec web find /app -type f -name "*.pyc" -delete
docker-compose restart web

# Esperar 10 segundos
sleep 10

# Verificar de nuevo
docker-compose exec web python -c "from app import create_app; app = create_app(); print('SESSION_COOKIE_SECURE:', app.config.get('SESSION_COOKIE_SECURE'))"
```

```bash
# Opción 2: Rebuild completo (más agresivo)
docker-compose down
docker-compose build --no-cache web
docker-compose up -d
```

### 📊 Diagrama de Flujo del Problema

```
┌─────────────────────────────────────────────────────────┐
│ config.py lee .env                                       │
│ SESSION_COOKIE_SECURE = False ✅                        │
└────────────────────────────────────┬────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────┐
│ ProductionConfig(Config)                                │
│ ANTES: SESSION_COOKIE_SECURE = True ❌ (hardcoded)     │
│ DESPUÉS: Heredado de Config ✅                          │
└────────────────────────────────────┬────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────┐
│ docker-compose.yml environment:                         │
│ ANTES: No declaraba SESSION_COOKIE_SECURE ❌            │
│ DESPUÉS: - SESSION_COOKIE_SECURE=${...:-False} ✅      │
└────────────────────────────────────┬────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────┐
│ Container recibe: SESSION_COOKIE_SECURE=False           │
│ Flask usa: SESSION_COOKIE_SECURE=False                  │
│ Cookie sin flag Secure ✅                               │
│ Login funciona en HTTP ✅                               │
└─────────────────────────────────────────────────────────┘
```

### 📝 Prevención

**1. Usar HTTPS en producción**

La solución correcta larga plazo es configurar HTTPS con Let's Encrypt:

```bash
# Instalar Certbot
sudo yum install -y certbot python3-certbot-nginx  # CentOS
sudo apt-get install -y certbot python3-certbot-nginx  # Ubuntu

# Obtener certificado (requiere dominio apuntando al servidor)
sudo certbot --nginx -d aulavirtual.com -d www.aulavirtual.com

# Renovar automáticamente
sudo crontab -e
# Agregar: 0 3 * * * certbot renew --quiet
```

Luego en `.env`:
```
SESSION_COOKIE_SECURE=True  # ✅ Correcto con HTTPS
```

**2. Testing local con HTTPS**

```bash
# Generar certificado self-signed para desarrollo
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Usar en run.py o run local command
app.run(ssl_context=('cert.pem', 'key.pem'))
```

**3. CI/CD Validation**

Agregar test que verifique la configuración:

```python
# tests/test_config.py
def test_session_cookie_secure_matches_protocol():
    """SESSION_COOKIE_SECURE debe ser True solo si hay HTTPS"""
    from app import create_app
    app = create_app('production')
    
    preferred_scheme = app.config.get('PREFERRED_URL_SCHEME', 'http')
    session_secure = app.config.get('SESSION_COOKIE_SECURE')
    
    if preferred_scheme == 'https':
        assert session_secure is True, "SESSION_COOKIE_SECURE debe ser True con HTTPS"
    else:
        assert session_secure is False, "SESSION_COOKIE_SECURE debe ser False sin HTTPS"
```

### 🔗 Commits Relacionados
- `e26917f` - "Fix: permitir que SESSION_COOKIE_SECURE se configure desde .env"
- `d5e9f89` - "Fix: agregar SESSION_COOKIE_SECURE a environment del contenedor web"

---

## Limpieza de Cache Python

### 🟡 Síntoma
- Cambios en código no se reflejan en la aplicación
- Variables de configuración muestran valores viejos
- Después de actualizar .env o config.py, nada cambia

### 🔍 Diagnóstico

Python compila archivos `.py` a bytecode `.pyc` para ejecución más rápida. Estos archivos se guardan en carpetas `__pycache__/`.

Cuando cambias código o configuración, Python puede seguir usando los `.pyc` viejos si no detecta el cambio.

**Verificar presencia de cache**:

```bash
# Ver todos los __pycache__
find /root/aulavirtual -type d -name __pycache__

# Contar archivos .pyc
find /root/aulavirtual -name "*.pyc" | wc -l
```

### ✅ Solución

**Método 1: Limpiar cache en host**

```bash
cd /root/aulavirtual

# Eliminar carpetas __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Eliminar archivos .pyc individuales
find . -name "*.pyc" -delete

# Eliminar archivos .pyo (compiled optimized)
find . -name "*.pyo" -delete
```

**Método 2: Limpiar cache en container**

```bash
# Desde host
docker-compose exec web find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
docker-compose exec web find /app -name "*.pyc" -delete

# Reiniciar para aplicar
docker-compose restart web
```

**Método 3: Rebuild del container**

Más agresivo pero garantiza limpieza total:

```bash
docker-compose down
docker-compose build --no-cache web
docker-compose up -d
```

**Método 4: Automático en Dockerfile**

Prevenir creación de `.pyc`:

```dockerfile
# En Dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

### 📝 Prevención

**1. Deshabilitar .pyc en desarrollo**

```bash
# En .env
PYTHONDONTWRITEBYTECODE=1
```

**2. Agregar a .gitignore**

```
# .gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
```

**3. Hook de git**

Crear `.git/hooks/post-merge`:

```bash
#!/bin/bash
echo "Limpiando cache de Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
echo "Cache limpiado"
```

```bash
chmod +x .git/hooks/post-merge
```

### 📝 Cuando limpiar cache

Limpiar cache después de:
- Actualizar variables de entorno (.env)
- Modificar archivos de configuración (config.py)
- Hacer `git pull` de cambios importantes
- Cambiar versión de Python
- Problemas raros que no tienen sentido

No es necesario limpiar para:
- Cambios en templates HTML
- Cambios en archivos estáticos (CSS, JS)
- Cambios en base de datos

---

## 📚 Referencias Adicionales

### Documentos Relacionados
- [INSTALACION_COMPLETA.md](./INSTALACION_COMPLETA.md) - Guía de instalación paso a paso
- [ARQUITECTURA.md](./ARQUITECTURA.md) - Arquitectura del sistema
- [README.md](./README.md) - Información general del proyecto

### Recursos Externos
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation]( https://www.postgresql.org/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

### Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f web

# Ver últimas 100 líneas
docker-compose logs --tail=100 web

# Buscar errores en logs
docker-compose logs web | grep -i error

# Entrar a shell del container
docker-compose exec web bash

# Python shell con contexto Flask
docker-compose exec web python
>>> from app import create_app
>>> app = create_app()
>>> with app.app_context():
...     # Ejecutar código con contexto

# Ver rutas registradas
docker-compose exec web python -c "from app import create_app; app = create_app(); [print(rule) for rule in app.url_map.iter_rules()]"

# Verificar sintaxis Python sin ejecutar
python -m py_compile archivo.py

# Ver espacio en disco
df -h
du -sh /root/aulavirtual

# Backup de base de datos
docker-compose exec db pg_dump -U postgres aulavirtual_db > backup_$(date +%Y%m%d).sql

# Restore de base de datos
docker-compose exec -T db psql -U postgres aulavirtual_db < backup_20260306.sql
```

---

**Fin del documento TROUBLESHOOTING.md**
