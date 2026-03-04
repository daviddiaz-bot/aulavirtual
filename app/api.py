"""
API REST de Aula Virtual
Endpoints para integraciones externas
"""

from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from .models import Usuario, Docente, Clase, Resena, Material, db
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)


def require_api_key(f):
    """Decorador para requerir API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key or api_key != current_app.config.get('API_KEY'):
            return jsonify({'error': 'API key inválida o faltante'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@api_bp.route('/docentes', methods=['GET'])
@require_api_key
def get_docentes():
    """Obtener lista de docentes"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    especialidad = request.args.get('especialidad', '')
    
    query = Docente.query.filter_by(verificado=True)
    
    if especialidad:
        query = query.filter(Docente.especialidad.ilike(f'%{especialidad}%'))
    
    docentes = query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'docentes': [],
        'total': docentes.total,
        'page': page,
        'per_page': per_page,
        'pages': docentes.pages
    }
    
    for docente in docentes.items:
        result['docentes'].append({
            'id': docente.id,
            'nombre': docente.usuario.nombre,
            'email': docente.usuario.email,
            'especialidad': docente.especialidad,
            'descripcion': docente.descripcion,
            'precio_hora': docente.precio_hora,
            'calificacion_promedio': docente.promedio_calificacion,
            'total_resenas': docente.total_resenas,
            'total_clases': docente.total_clases
        })
    
    return jsonify(result)


@api_bp.route('/docentes/<int:docente_id>', methods=['GET'])
@require_api_key
def get_docente(docente_id):
    """Obtener detalles de un docente"""
    docente = Docente.query.get_or_404(docente_id)
    
    if not docente.verificado:
        return jsonify({'error': 'Docente no disponible'}), 404
    
    return jsonify({
        'id': docente.id,
        'nombre': docente.usuario.nombre,
        'email': docente.usuario.email,
        'telefono': docente.usuario.telefono,
        'especialidad': docente.especialidad,
        'descripcion': docente.descripcion,
        'experiencia': docente.experiencia,
        'educacion': docente.educacion,
        'precio_hora': docente.precio_hora,
        'calificacion_promedio': docente.promedio_calificacion,
        'total_resenas': docente.total_resenas,
        'total_clases': docente.total_clases,
        'fecha_registro': docente.usuario.fecha_registro.isoformat()
    })


@api_bp.route('/docentes/<int:docente_id>/resenas', methods=['GET'])
@require_api_key
def get_docente_resenas(docente_id):
    """Obtener reseñas de un docente"""
    docente = Docente.query.get_or_404(docente_id)
    
    resenas = Resena.query.filter_by(docente_id=docente_id, visible=True).order_by(Resena.fecha.desc()).limit(50).all()
    
    result = {
        'docente_id': docente_id,
        'docente_nombre': docente.usuario.nombre,
        'total_resenas': len(resenas),
        'resenas': []
    }
    
    for resena in resenas:
        result['resenas'].append({
            'id': resena.id,
            'calificacion': resena.calificacion,
            'comentario': resena.comentario,
            'cliente_nombre': resena.cliente.nombre,
            'fecha': resena.fecha.isoformat()
        })
    
    return jsonify(result)


@api_bp.route('/clases', methods=['GET'])
@require_api_key
def get_clases():
    """Obtener lista de clases"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    estado = request.args.get('estado', '')
    fecha_desde = request.args.get('fecha_desde', '')
    
    query = Clase.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    if fecha_desde:
        try:
            fecha = datetime.fromisoformat(fecha_desde)
            query = query.filter(Clase.fecha_inicio >= fecha)
        except ValueError:
            pass
    
    clases = query.order_by(Clase.fecha_inicio.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    result = {
        'clases': [],
        'total': clases.total,
        'page': page,
        'per_page': per_page,
        'pages': clases.pages
    }
    
    for clase in clases.items:
        result['clases'].append({
            'id': clase.id,
            'titulo': clase.titulo,
            'fecha_inicio': clase.fecha_inicio.isoformat(),
            'duracion_minutos': clase.duracion_minutos,
            'estado': clase.estado,
            'monto': clase.monto,
            'docente': {
                'id': clase.docente_rel.id,
                'nombre': clase.docente_rel.usuario.nombre,
                'especialidad': clase.docente_rel.especialidad
            },
            'cliente': {
                'id': clase.cliente.id,
                'nombre': clase.cliente.nombre
            }
        })
    
    return jsonify(result)


@api_bp.route('/clases/<int:clase_id>', methods=['GET'])
@require_api_key
def get_clase(clase_id):
    """Obtener detalles de una clase"""
    clase = Clase.query.get_or_404(clase_id)
    
    return jsonify({
        'id': clase.id,
        'titulo': clase.titulo,
        'descripcion': clase.descripcion,
        'fecha_inicio': clase.fecha_inicio.isoformat(),
        'fecha_fin': clase.fecha_fin.isoformat() if clase.fecha_fin else None,
        'duracion_minutos': clase.duracion_minutos,
        'estado': clase.estado,
        'estado_pago': clase.estado_pago,
        'monto': clase.monto,
        'link_jitsi': clase.link_jitsi if clase.estado_pago else None,
        'docente': {
            'id': clase.docente_rel.id,
            'nombre': clase.docente_rel.usuario.nombre,
            'especialidad': clase.docente_rel.especialidad
        },
        'cliente': {
            'id': clase.cliente.id,
            'nombre': clase.cliente.nombre,
            'email': clase.cliente.email
        },
        'fecha_creacion': clase.fecha_creacion.isoformat()
    })


@api_bp.route('/materiales', methods=['GET'])
@require_api_key
def get_materiales():
    """Obtener materiales públicos"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    docente_id = request.args.get('docente_id', type=int)
    
    query = Material.query.filter_by(publico=True)
    
    if docente_id:
        query = query.filter_by(docente_id=docente_id)
    
    materiales = query.order_by(Material.fecha_subida.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    result = {
        'materiales': [],
        'total': materiales.total,
        'page': page,
        'per_page': per_page,
        'pages': materiales.pages
    }
    
    for material in materiales.items:
        result['materiales'].append({
            'id': material.id,
            'titulo': material.titulo,
            'descripcion': material.descripcion,
            'tipo': material.tipo,
            'url': material.url,
            'tamanio_kb': material.tamanio_kb,
            'descargas': material.descargas,
            'fecha_subida': material.fecha_subida.isoformat(),
            'docente': {
                'id': material.docente.id,
                'nombre': material.docente.usuario.nombre,
                'especialidad': material.docente.especialidad
            }
        })
    
    return jsonify(result)


@api_bp.route('/estadisticas', methods=['GET'])
@require_api_key
def get_estadisticas():
    """Obtener estadísticas generales"""
    from sqlalchemy import func
    
    total_usuarios = Usuario.query.filter_by(activo=True).count()
    total_docentes = Docente.query.filter_by(verificado=True).count()
    total_clientes = Usuario.query.filter_by(rol='cliente', activo=True).count()
    total_clases = Clase.query.filter_by(estado='completada').count()
    
    # Clases del mes actual
    primer_dia_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    clases_mes = Clase.query.filter(
        Clase.fecha_inicio >= primer_dia_mes,
        Clase.estado.in_(['confirmada', 'completada'])
    ).count()
    
    return jsonify({
        'usuarios': {
            'total': total_usuarios,
            'docentes': total_docentes,
            'clientes': total_clientes
        },
        'clases': {
            'total_historico': total_clases,
            'total_mes_actual': clases_mes
        },
        'timestamp': datetime.utcnow().isoformat()
    })
