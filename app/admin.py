"""
Panel de Administración de Aula Virtual
Gestión de usuarios, docentes, clases y configuración del sistema
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from functools import wraps
from .models import Usuario, Docente, Clase, Pago, Resena, Material, Notificacion, db
from sqlalchemy import func, extract
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso no autorizado. Se requieren privilegios de administrador.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del administrador"""
    
    # Estadísticas generales
    total_usuarios = Usuario.query.filter_by(activo=True).count()
    total_docentes = Docente.query.filter_by(verificado=True).count()
    total_clientes = Usuario.query.filter_by(rol='cliente', activo=True).count()
    docentes_pendientes = Docente.query.filter_by(verificado=False).count()
    
    # Ingresos totales y del mes actual
    ingresos_totales = db.session.query(func.sum(Pago.monto)).filter_by(estado='completado').scalar() or 0
    
    primer_dia_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ingresos_mes = db.session.query(func.sum(Pago.monto)).filter(
        Pago.estado == 'completado',
        Pago.fecha_pago >= primer_dia_mes
    ).scalar() or 0
    
    # Clases del mes
    clases_mes = Clase.query.filter(
        Clase.fecha_inicio >= primer_dia_mes,
        Clase.estado.in_(['confirmada', 'completada'])
    ).count()
    
    # Top docentes por calificación
    top_docentes = Docente.query.filter_by(verificado=True).order_by(
        Docente.calificacion_promedio.desc()
    ).limit(5).all()
    
    # Ingresos por mes (últimos 6 meses)
    hoy = datetime.utcnow()
    meses_labels = []
    meses_valores = []
    
    for i in range(5, -1, -1):
        mes_inicio = (hoy.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        if i > 0:
            mes_fin = (hoy.replace(day=1) - timedelta(days=30*(i-1))).replace(day=1)
        else:
            mes_fin = hoy
        
        ingresos_mes_i = db.session.query(func.sum(Pago.monto)).filter(
            Pago.estado == 'completado',
            Pago.fecha_pago >= mes_inicio,
            Pago.fecha_pago < mes_fin
        ).scalar() or 0
        
        meses_labels.append(mes_inicio.strftime('%b %Y'))
        meses_valores.append(float(ingresos_mes_i))
    
    # Actividad reciente
    usuarios_recientes = Usuario.query.order_by(Usuario.fecha_registro.desc()).limit(5).all()
    clases_recientes = Clase.query.order_by(Clase.fecha_creacion.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         total_docentes=total_docentes,
                         total_clientes=total_clientes,
                         docentes_pendientes=docentes_pendientes,
                         ingresos_totales=round(ingresos_totales, 2),
                         ingresos_mes=round(ingresos_mes, 2),
                         clases_mes=clases_mes,
                         top_docentes=top_docentes,
                         meses_labels=meses_labels,
                         meses_valores=meses_valores,
                         usuarios_recientes=usuarios_recientes,
                         clases_recientes=clases_recientes)


@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    """Listado de usuarios"""
    page = request.args.get('page', 1, type=int)
    rol = request.args.get('rol', '')
    buscar = request.args.get('buscar', '')
    
    query = Usuario.query
    
    if rol:
        query = query.filter_by(rol=rol)
    
    if buscar:
        query = query.filter(
            (Usuario.nombre.ilike(f'%{buscar}%')) |
            (Usuario.email.ilike(f'%{buscar}%'))
        )
    
    usuarios = query.order_by(Usuario.fecha_registro.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin_bp.route('/usuarios/<int:usuario_id>')
@login_required
@admin_required
def detalle_usuario(usuario_id):
    """Detalle de un usuario"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Obtener estadísticas del usuario
    if usuario.rol == 'cliente':
        total_clases = Clase.query.filter_by(cliente_id=usuario_id).count()
        total_gastado = db.session.query(func.sum(Pago.monto)).join(Clase).filter(
            Clase.cliente_id == usuario_id,
            Pago.estado == 'completado'
        ).scalar() or 0
        
        stats = {
            'total_clases': total_clases,
            'total_gastado': round(total_gastado, 2)
        }
    elif usuario.rol == 'docente':
        docente = Docente.query.filter_by(usuario_id=usuario_id).first()
        if docente:
            total_clases = Clase.query.filter_by(docente_id=docente.id).count()
            total_ingresos = db.session.query(func.sum(Pago.monto)).join(Clase).filter(
                Clase.docente_id == docente.id,
                Pago.estado == 'completado'
            ).scalar() or 0
            
            stats = {
                'total_clases': total_clases,
                'total_ingresos': round(total_ingresos, 2),
                'calificacion': docente.calificacion_promedio
            }
        else:
            stats = {}
    else:
        stats = {}
    
    return render_template('admin/detalle_usuario.html', usuario=usuario, stats=stats)


@admin_bp.route('/usuarios/<int:usuario_id>/activar', methods=['POST'])
@login_required
@admin_required
def activar_usuario(usuario_id):
    """Activar o desactivar usuario"""
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.activo = not usuario.activo
    db.session.commit()
    
    estado = 'activado' if usuario.activo else 'desactivado'
    flash(f'Usuario {estado} correctamente', 'success')
    return redirect(url_for('admin.detalle_usuario', usuario_id=usuario_id))


@admin_bp.route('/docentes')
@login_required
@admin_required
def docentes():
    """Listado de docentes"""
    page = request.args.get('page', 1, type=int)
    verificado = request.args.get('verificado', '')
    
    query = Docente.query.join(Usuario)
    
    if verificado == 'si':
        query = query.filter(Docente.verificado == True)
    elif verificado == 'no':
        query = query.filter(Docente.verificado == False)
    
    docentes = query.order_by(Docente.fecha_aprobacion.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/docentes.html', docentes=docentes)


@admin_bp.route('/docentes/<int:docente_id>/verificar', methods=['POST'])
@login_required
@admin_required
def verificar_docente(docente_id):
    """Verificar o rechazar un docente"""
    docente = Docente.query.get_or_404(docente_id)
    accion = request.form.get('accion')
    
    if accion == 'aprobar':
        docente.verificado = True
        docente.fecha_aprobacion = datetime.utcnow()
        flash(f'Docente {docente.usuario.nombre} aprobado correctamente', 'success')
        
        # Enviar notificación al docente
        from .tasks import enviar_aprobacion_docente
        enviar_aprobacion_docente.delay(docente.id)
        
    elif accion == 'rechazar':
        docente.verificado = False
        docente.fecha_aprobacion = None
        flash(f'Docente {docente.usuario.nombre} rechazado', 'info')
    
    db.session.commit()
    return redirect(url_for('admin.docentes'))


@admin_bp.route('/clases')
@login_required
@admin_required
def clases():
    """Listado de clases"""
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    query = Clase.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    clases = query.order_by(Clase.fecha_inicio.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/clases.html', clases=clases)


@admin_bp.route('/pagos')
@login_required
@admin_required
def pagos():
    """Listado de pagos"""
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    query = Pago.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    pagos = query.order_by(Pago.fecha_pago.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/pagos.html', pagos=pagos)


@admin_bp.route('/reportes')
@login_required
@admin_required
def reportes():
    """Reportes y estadísticas"""
    
    # Rango de fechas
    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
    else:
        fecha_desde = datetime.utcnow().replace(day=1)
    
    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
    else:
        fecha_hasta = datetime.utcnow()
    
    # Ingresos en el rango
    ingresos = db.session.query(func.sum(Pago.monto)).filter(
        Pago.estado == 'completado',
        Pago.fecha_pago >= fecha_desde,
        Pago.fecha_pago <= fecha_hasta
    ).scalar() or 0
    
    # Clases en el rango
    total_clases = Clase.query.filter(
        Clase.fecha_inicio >= fecha_desde,
        Clase.fecha_inicio <= fecha_hasta
    ).count()
    
    # Nuevos usuarios
    nuevos_usuarios = Usuario.query.filter(
        Usuario.fecha_registro >= fecha_desde,
        Usuario.fecha_registro <= fecha_hasta
    ).count()
    
    # Top docentes por ingresos
    top_docentes = db.session.query(
        Docente,
        func.sum(Pago.monto).label('total_ingresos'),
        func.count(Clase.id).label('total_clases')
    ).join(Clase, Clase.docente_id == Docente.id)\
     .join(Pago, Pago.clase_id == Clase.id)\
     .filter(
         Pago.estado == 'completado',
         Pago.fecha_pago >= fecha_desde,
         Pago.fecha_pago <= fecha_hasta
     ).group_by(Docente.id)\
      .order_by(func.sum(Pago.monto).desc())\
      .limit(10).all()
    
    return render_template('admin/reportes.html',
                         ingresos=round(ingresos, 2),
                         total_clases=total_clases,
                         nuevos_usuarios=nuevos_usuarios,
                         top_docentes=top_docentes,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)


@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    """Configuración del sistema"""
    
    if request.method == 'POST':
        # Aquí se pueden guardar configuraciones en la base de datos
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('admin.configuracion'))
    
    return render_template('admin/configuracion.html')
