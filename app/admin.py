"""
Panel de Administración de Aula Virtual
Gestión de usuarios, docentes, clases y configuración del sistema
"""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from functools import wraps
from .models import Usuario, Docente, Clase, Pago, Resena, Material, Notificacion, Retiro, db
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
    
    # Retiros pendientes
    retiros_pendientes = Retiro.query.filter_by(estado='pendiente').count()
    
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
                         clases_recientes=clases_recientes,
                         retiros_pendientes=retiros_pendientes)


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


@admin_bp.route('/usuarios/<int:usuario_id>/resetear-password', methods=['POST'])
@login_required
@admin_required
def resetear_password_usuario(usuario_id):
    """Resetear contraseña de un usuario (admin)"""
    import secrets
    from .email import send_email
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Generar nueva contraseña temporal
    nueva_password = secrets.token_urlsafe(12)
    
    # Actualizar contraseña
    usuario.set_password(nueva_password)
    db.session.commit()
    
    # Enviar email con nueva contraseña
    try:
        send_email(
            to=usuario.email,
            subject='Restablecimiento de Contraseña - Aula Virtual',
            template='email/reset_password_admin',
            usuario=usuario,
            nueva_password=nueva_password
        )
        flash(f'Contraseña restablecida correctamente. Se ha enviado un correo a {usuario.email} con la nueva contraseña.', 'success')
    except Exception as e:
        current_app.logger.error(f'Error enviando email de reseteo: {e}')
        flash(f'Contraseña restablecida a: {nueva_password} (no se pudo enviar el email)', 'warning')
    
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
        config_type = request.form.get('config_type', 'stripe')
        
        if config_type == 'stripe':
            # Actualizar configuración de Stripe
            stripe_mode = request.form.get('stripe_mode', 'test')
            stripe_publishable_key = request.form.get('stripe_publishable_key', '').strip()
            stripe_secret_key = request.form.get('stripe_secret_key', '').strip()
            stripe_webhook_secret = request.form.get('stripe_webhook_secret', '').strip()
            
            # Validar que las claves tengan el formato correcto
            if stripe_publishable_key and not (stripe_publishable_key.startswith('pk_test_') or stripe_publishable_key.startswith('pk_live_')):
                flash('La clave pública debe comenzar con pk_test_ o pk_live_', 'danger')
                return redirect(url_for('admin.configuracion'))
            
            if stripe_secret_key and not (stripe_secret_key.startswith('sk_test_') or stripe_secret_key.startswith('sk_live_')):
                flash('La clave secreta debe comenzar con sk_test_ o sk_live_', 'danger')
                return redirect(url_for('admin.configuracion'))
            
            # Actualizar variables de entorno
            try:
                env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
                
                # Leer archivo .env actual
                env_vars = {}
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key] = value
                
                # Actualizar valores
                if stripe_publishable_key:
                    env_vars['STRIPE_PUBLISHABLE_KEY'] = stripe_publishable_key
                if stripe_secret_key:
                    env_vars['STRIPE_SECRET_KEY'] = stripe_secret_key
                if stripe_webhook_secret:
                    env_vars['STRIPE_WEBHOOK_SECRET'] = stripe_webhook_secret
                
                # Escribir archivo .env actualizado
                with open(env_file, 'w') as f:
                    for key, value in env_vars.items():
                        f.write(f'{key}={value}\n')
                
                flash('Configuración de Stripe actualizada. Reinicia el servidor para aplicar cambios.', 'success')
                
            except Exception as e:
                flash(f'Error al guardar configuración: {str(e)}', 'danger')
        
        elif config_type == 'jitsi':
            # Configuración de Jitsi (por ahora solo mostrar)
            flash('Configuración de Jitsi actualizada', 'success')
        
        return redirect(url_for('admin.configuracion'))
    
    # Cargar configuración actual
    from flask import current_app
    
    stripe_publishable_key = current_app.config.get('STRIPE_PUBLISHABLE_KEY', '')
    stripe_secret_key = current_app.config.get('STRIPE_SECRET_KEY', '')
    stripe_webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')
    
    # Maskear claves para mostrarlas de forma segura
    stripe_secret_key_masked = ''
    if stripe_secret_key:
        stripe_secret_key_masked = stripe_secret_key[:10] + '*' * (len(stripe_secret_key) - 10)
    
    stripe_webhook_secret_masked = ''
    if stripe_webhook_secret:
        stripe_webhook_secret_masked = stripe_webhook_secret[:10] + '*' * (len(stripe_webhook_secret) - 10)
    
    # Determinar modo (test/live) basado en las claves
    stripe_mode = 'test'
    if stripe_publishable_key and stripe_publishable_key.startswith('pk_live_'):
        stripe_mode = 'live'
    
    stripe_configured = bool(stripe_publishable_key and stripe_secret_key)
    
    return render_template('admin/configuracion.html',
                         stripe_publishable_key=stripe_publishable_key,
                         stripe_secret_key_masked=stripe_secret_key_masked,
                         stripe_webhook_secret_masked=stripe_webhook_secret_masked,
                         stripe_mode=stripe_mode,
                         stripe_configured=stripe_configured,
                         jitsi_server='meet.jit.si')


# ==================== GESTIÓN DE RETIROS ====================

@admin_bp.route('/retiros')
@login_required
@admin_required
def retiros():
    """Panel de gestión de retiros de docentes"""
    # Filtros
    estado_filter = request.args.get('estado', '')
    metodo_filter = request.args.get('metodo', '')
    docente_filter = request.args.get('docente', '')
    
    # Query base
    query = Retiro.query
    
    # Aplicar filtros
    if estado_filter:
        query = query.filter_by(estado=estado_filter)
    if metodo_filter:
        query = query.filter_by(metodo_pago=metodo_filter)
    if docente_filter:
        query = query.join(Docente).join(Usuario).filter(
            Usuario.nombre.ilike(f'%{docente_filter}%')
        )
    
    # Obtener retiros ordenados
    retiros = query.order_by(Retiro.fecha_solicitud.desc()).all()
    
    # Estadísticas
    retiros_pendientes = Retiro.query.filter_by(estado='pendiente').all()
    retiros_aprobados = Retiro.query.filter_by(estado='aprobado').all()
    
    # Retiros pagados este mes
    primer_dia_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    retiros_pagados_mes = Retiro.query.filter(
        Retiro.estado == 'pagado',
        Retiro.fecha_pago >= primer_dia_mes
    ).all()
    
    # Retiros rechazados este mes
    retiros_rechazados = Retiro.query.filter(
        Retiro.estado == 'rechazado',
        Retiro.fecha_solicitud >= primer_dia_mes
    ).all()
    
    # Calcular sumas
    sum_pendientes = sum(r.monto for r in retiros_pendientes)
    sum_aprobados = sum(r.monto for r in retiros_aprobados)
    sum_pagados_mes = sum(r.monto for r in retiros_pagados_mes)
    
    return render_template('admin/retiros.html',
                         retiros=retiros,
                         retiros_pendientes=retiros_pendientes,
                         retiros_aprobados=retiros_aprobados,
                         retiros_pagados_mes=retiros_pagados_mes,
                         retiros_rechazados=retiros_rechazados,
                         sum_pendientes=sum_pendientes,
                         sum_aprobados=sum_aprobados,
                         sum_pagados_mes=sum_pagados_mes)


@admin_bp.route('/retiros/<int:retiro_id>/detalle')
@login_required
@admin_required
def retiro_detalle(retiro_id):
    """Obtener detalles de un retiro en formato JSON"""
    retiro = Retiro.query.get_or_404(retiro_id)
    docente = retiro.docente_rel
    
    # Calcular clases completadas del docente
    clases_completadas = Clase.query.filter_by(
        docente_id=docente.id,
        estado='completada',
        estado_pago=True
    ).count()
    
    # Preparar badges
    estado_badges = {
        'pendiente': '<span class="badge bg-warning text-dark"><i class="fas fa-clock me-1"></i> Pendiente</span>',
        'aprobado': '<span class="badge bg-info"><i class="fas fa-check me-1"></i> Aprobado</span>',
        'pagado': '<span class="badge bg-success"><i class="fas fa-check-double me-1"></i> Pagado</span>',
        'rechazado': '<span class="badge bg-danger"><i class="fas fa-times me-1"></i> Rechazado</span>'
    }
    
    metodo_badges = {
        'paypal': '<span class="badge bg-primary"><i class="fab fa-paypal me-1"></i> PayPal</span>',
        'banco': '<span class="badge bg-success"><i class="fas fa-university me-1"></i> Transferencia</span>',
        'stripe': '<span class="badge bg-info"><i class="fab fa-stripe me-1"></i> Stripe Connect</span>',
        'manual': '<span class="badge bg-secondary"><i class="fas fa-hand-holding-usd me-1"></i> Manual</span>'
    }
    
    # Datos de pago HTML
    datos_pago_html = '<div class="alert alert-light"><h6 class="text-muted text-uppercase mb-2">Datos de Pago</h6>'
    
    try:
        import json
        datos_pago = json.loads(retiro.datos_pago) if retiro.datos_pago else {}
        
        if retiro.metodo_pago == 'paypal':
            datos_pago_html += f'<p><strong>Email PayPal:</strong> {datos_pago.get("email", "N/A")}</p>'
        elif retiro.metodo_pago == 'banco':
            datos_pago_html += f'''
                <p><strong>Banco:</strong> {datos_pago.get("banco", "N/A")}</p>
                <p><strong>Tipo:</strong> {datos_pago.get("tipo", "N/A")}</p>
                <p><strong>Cuenta:</strong> {datos_pago.get("cuenta", "N/A")}</p>
                <p><strong>Titular:</strong> {datos_pago.get("titular", "N/A")}</p>
            '''
    except:
        datos_pago_html += '<p class="text-muted">No hay datos de pago especificados</p>'
    
    datos_pago_html += '</div>'
    
    return jsonify({
        'id': retiro.id,
        'monto': retiro.monto,
        'estado': retiro.estado,
        'estado_badge': estado_badges.get(retiro.estado, ''),
        'metodo_pago': retiro.metodo_pago,
        'metodo_badge': metodo_badges.get(retiro.metodo_pago, ''),
        'docente_nombre': docente.usuario_rel.nombre,
        'docente_email': docente.usuario_rel.email,
        'saldo_actual': docente.saldo_disponible,
        'clases_completadas': clases_completadas,
        'datos_pago_html': datos_pago_html,
        'fecha_solicitud': retiro.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
        'fecha_aprobacion': retiro.fecha_aprobacion.strftime('%d/%m/%Y %H:%M') if retiro.fecha_aprobacion else None,
        'fecha_pago': retiro.fecha_pago.strftime('%d/%m/%Y %H:%M') if retiro.fecha_pago else None,
        'notas_docente': retiro.notas_docente,
        'notas_admin': retiro.notas_admin,
        'transaction_id': retiro.transaction_id
    })


@admin_bp.route('/retiros/<int:retiro_id>/aprobar', methods=['POST'])
@login_required
@admin_required
def aprobar_retiro(retiro_id):
    """Aprobar una solicitud de retiro"""
    retiro = Retiro.query.get_or_404(retiro_id)
    
    if retiro.estado != 'pendiente':
        return jsonify({
            'success': False,
            'message': f'El retiro ya está en estado: {retiro.estado}'
        }), 400
    
    retiro.estado = 'aprobado'
    retiro.fecha_aprobacion = datetime.utcnow()
    retiro.aprobado_por_id = current_user.id
    
    db.session.commit()
    
    # TODO: Enviar email al docente notificando aprobación
    
    return jsonify({
        'success': True,
        'message': f'Retiro #{retiro.id} aprobado correctamente'
    })


@admin_bp.route('/retiros/<int:retiro_id>/rechazar', methods=['POST'])
@login_required
@admin_required
def rechazar_retiro(retiro_id):
    """Rechazar una solicitud de retiro"""
    retiro = Retiro.query.get_or_404(retiro_id)
    
    if retiro.estado not in ['pendiente', 'aprobado']:
        flash('No se puede rechazar un retiro en este estado', 'danger')
        return redirect(url_for('admin.retiros'))
    
    notas_admin = request.form.get('notas_admin', '').strip()
    
    if not notas_admin:
        flash('Debes proporcionar un motivo para el rechazo', 'danger')
        return redirect(url_for('admin.retiros'))
    
    retiro.estado = 'rechazado'
    retiro.notas_admin = notas_admin
    retiro.fecha_aprobacion = datetime.utcnow() if not retiro.fecha_aprobacion else retiro.fecha_aprobacion
    
    db.session.commit()
    
    # TODO: Enviar email al docente con el motivo del rechazo
    
    flash(f'✅ Retiro #{retiro.id} rechazado correctamente', 'success')
    return redirect(url_for('admin.retiros'))


@admin_bp.route('/retiros/<int:retiro_id>/pagar', methods=['POST'])
@login_required
@admin_required
def marcar_pagado(retiro_id):
    """Marcar un retiro como pagado"""
    retiro = Retiro.query.get_or_404(retiro_id)
    
    if retiro.estado != 'aprobado':
        flash('El retiro debe estar aprobado para marcarlo como pagado', 'danger')
        return redirect(url_for('admin.retiros'))
    
    transaction_id = request.form.get('transaction_id', '').strip()
    notas_admin = request.form.get('notas_admin', '').strip()
    
    if not transaction_id:
        flash('Debes proporcionar un ID de transacción o referencia', 'danger')
        return redirect(url_for('admin.retiros'))
    
    retiro.estado = 'pagado'
    retiro.transaction_id = transaction_id
    retiro.fecha_pago = datetime.utcnow()
    
    if notas_admin:
        retiro.notas_admin = (retiro.notas_admin or '') + '\n' + notas_admin
    
    # Manejar archivo de comprobante
    if 'comprobante' in request.files:
        file = request.files['comprobante']
        if file and file.filename:
            # TODO: Guardar archivo en servidor/cloud
            # Por ahora solo guardamos el nombre
            retiro.comprobante_url = file.filename
    
    db.session.commit()
    
    # TODO: Enviar email al docente confirmando el pago
    
    flash(f'✅ Retiro #{retiro.id} marcado como pagado correctamente', 'success')
    return redirect(url_for('admin.retiros'))


@admin_bp.route('/retiros/exportar')
@login_required
@admin_required
def exportar_retiros():
    """Exportar retiros a Excel"""
    # TODO: Implementar exportación real a Excel
    flash('Funcionalidad de exportación en desarrollo', 'info')
    return redirect(url_for('admin.retiros'))


# ============================================================================
# GESTIÓN DE MATERIALES (DEPURACIÓN)
# ============================================================================

@admin_bp.route('/materiales')
@login_required
@admin_required
def materiales():
    """Vista de todos los materiales PDF del sistema"""
    # Obtener filtros
    docente_id = request.args.get('docente_id', type=int)
    buscar = request.args.get('buscar', '').strip()
    
    # Query base
    query = Material.query.filter_by(tipo='pdf')
    
    # Aplicar filtros
    if docente_id:
        query = query.filter_by(docente_id=docente_id)
    
    if buscar:
        query = query.filter(
            (Material.titulo.ilike(f'%{buscar}%')) |
            (Material.descripcion.ilike(f'%{buscar}%'))
        )
    
    # Ordenar y obtener resultados
    materiales = query.order_by(Material.fecha_subida.desc()).all()
    
    # Obtener lista de docentes para el filtro
    docentes = Docente.query.join(Usuario).filter(Docente.verificado == True).all()
    
    # Estadísticas
    total_materiales = Material.query.filter_by(tipo='pdf').count()
    total_descargas = db.session.query(func.sum(Material.descargas)).filter_by(tipo='pdf').scalar() or 0
    tamanio_total_kb = db.session.query(func.sum(Material.tamanio_kb)).filter_by(tipo='pdf').scalar() or 0
    tamanio_total_mb = round(tamanio_total_kb / 1024, 2) if tamanio_total_kb else 0
    
    return render_template('admin/materiales.html',
                         materiales=materiales,
                         docentes=docentes,
                         total_materiales=total_materiales,
                         total_descargas=total_descargas,
                         tamanio_total_mb=tamanio_total_mb,
                         docente_filtro=docente_id,
                         buscar=buscar)


@admin_bp.route('/materiales/<int:material_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_material_admin(material_id):
    """Eliminar (depurar) un material como administrador"""
    material = Material.query.get_or_404(material_id)
    
    # Eliminar archivo físico si existe
    if material.archivo_path:
        filepath = os.path.join('app', 'static', material.archivo_path)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error al eliminar archivo: {e}")
                flash(f'Error al eliminar archivo físico: {str(e)}', 'warning')
    
    # Eliminar registro de la base de datos
    db.session.delete(material)
    db.session.commit()
    
    flash('Material eliminado correctamente por el administrador', 'success')
    return redirect(url_for('admin.materiales'))


@admin_bp.route('/materiales/<int:material_id>/detalles')
@login_required
@admin_required
def detalle_material(material_id):
    """Ver detalles completos de un material"""
    material = Material.query.get_or_404(material_id)
    
    return render_template('admin/detalle_material.html', material=material)
