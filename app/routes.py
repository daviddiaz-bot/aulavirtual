"""
Rutas Principales de Aula Virtual
Maneja las vistas principales de la aplicación
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_file
from flask_login import login_required, current_user
from .models import Usuario, Docente, Clase, Pago, Resena, Material, Calificacion, Notificacion, Retiro, db
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename
import uuid
import stripe
import os

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Página de inicio"""
    # Obtener top docentes
    top_docentes = Docente.query.filter_by(verificado=True).order_by(Docente.calificacion_promedio.desc()).limit(6).all()
    
    # Estadísticas generales
    total_docentes = Docente.query.filter_by(verificado=True).count()
    total_clases = Clase.query.filter_by(estado='completada').count()
    
    return render_template('index.html', 
                         top_docentes=top_docentes,
                         total_docentes=total_docentes,
                         total_clases=total_clases)


@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal según el rol del usuario"""
    
    if current_user.rol == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    elif current_user.rol == 'cliente':
        # Dashboard del cliente/estudiante
        docentes = Docente.query.filter_by(verificado=True).order_by(Docente.calificacion_promedio.desc()).all()
        clases_proximas = Clase.query.filter(
            Clase.cliente_id == current_user.id,
            Clase.fecha_inicio > datetime.utcnow(),
            Clase.estado.in_(['confirmada', 'pendiente'])
        ).order_by(Clase.fecha_inicio).limit(5).all()
        
        clases_completadas = Clase.query.filter_by(
            cliente_id=current_user.id,
            estado='completada'
        ).count()
        
        return render_template('dashboard/cliente.html',
                             docentes=docentes,
                             clases_proximas=clases_proximas,
                             clases_completadas=clases_completadas)
    
    elif current_user.rol == 'docente':
        # Dashboard del docente
        docente = Docente.query.filter_by(usuario_id=current_user.id).first()
        
        if not docente:
            flash('Tu perfil de docente está pendiente de configuración', 'warning')
            return redirect(url_for('main.completar_perfil_docente'))
        
        clases_proximas = Clase.query.filter(
            Clase.docente_id == docente.id,
            Clase.fecha_inicio > datetime.utcnow(),
            Clase.estado.in_(['confirmada', 'pendiente'])
        ).order_by(Clase.fecha_inicio).limit(10).all()
        
        # Estadísticas
        total_clases = Clase.query.filter_by(docente_id=docente.id, estado='completada').count()
        ingresos_mes = db.session.query(func.sum(Pago.monto)).join(Clase).filter(
            Clase.docente_id == docente.id,
            Pago.estado == 'completado',
            Pago.fecha_pago >= datetime.utcnow().replace(day=1)
        ).scalar() or 0
        
        return render_template('dashboard/docente.html',
                             docente=docente,
                             clases_proximas=clases_proximas,
                             total_clases=total_clases,
                             ingresos_mes=round(ingresos_mes, 2))
    
    return redirect(url_for('main.index'))


@main.route('/docentes')
def docentes():
    """Listado de docentes"""
    page = request.args.get('page', 1, type=int)
    especialidad = request.args.get('especialidad', '')
    buscar = request.args.get('buscar', '')
    
    query = Docente.query.filter_by(verificado=True)
    
    if especialidad:
        query = query.filter(Docente.especialidad.ilike(f'%{especialidad}%'))
    
    if buscar:
        query = query.join(Usuario).filter(
            or_(
                Usuario.nombre.ilike(f'%{buscar}%'),
                Docente.descripcion.ilike(f'%{buscar}%'),
                Docente.especialidad.ilike(f'%{buscar}%')
            )
        )
    
    docentes = query.order_by(Docente.calificacion_promedio.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Obtener especialidades únicas para el filtro
    especialidades = db.session.query(Docente.especialidad).distinct().all()
    especialidades = [e[0] for e in especialidades if e[0]]
    
    return render_template('docentes/listado.html',
                         docentes=docentes,
                         especialidades=especialidades)


@main.route('/docente/<int:docente_id>')
def perfil_docente(docente_id):
    """Perfil público del docente"""
    docente = Docente.query.get_or_404(docente_id)
    
    if not docente.verificado:
        flash('Este docente no está disponible', 'warning')
        return redirect(url_for('main.docentes'))
    
    # Obtener reseñas
    resenas = Resena.query.filter_by(docente_id=docente_id, visible=True).order_by(Resena.fecha.desc()).limit(10).all()
    
    # Materiales públicos
    materiales = Material.query.filter_by(docente_id=docente_id, publico=True).order_by(Material.fecha_subida.desc()).limit(5).all()
    
    return render_template('docentes/perfil.html',
                         docente=docente,
                         resenas=resenas,
                         materiales=materiales)


@main.route('/reservar-clase/<int:docente_id>', methods=['GET', 'POST'])
@login_required
def reservar_clase(docente_id):
    """Reservar una clase con un docente"""
    if current_user.rol != 'cliente':
        flash('Solo los estudiantes pueden reservar clases', 'warning')
        return redirect(url_for('main.dashboard'))
    
    docente = Docente.query.get_or_404(docente_id)
    
    if not docente.verificado:
        flash('Este docente no está disponible para reservas', 'warning')
        return redirect(url_for('main.docentes'))
    
    if request.method == 'POST':
        fecha_str = request.form.get('fecha')
        hora_str = request.form.get('hora')
        duracion = int(request.form.get('duracion', 60))
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        # Validar fecha y hora
        try:
            fecha_inicio = datetime.strptime(f'{fecha_str} {hora_str}', '%Y-%m-%d %H:%M')
            
            if fecha_inicio < datetime.utcnow():
                flash('No puedes reservar clases en el pasado', 'danger')
                return render_template('clases/reservar.html', docente=docente)
            
            fecha_fin = fecha_inicio + timedelta(minutes=duracion)
            
            # Calcular monto
            monto = (duracion / 60) * docente.precio_hora
            
            # Crear clase pendiente de pago
            clase = Clase(
                cliente_id=current_user.id,
                docente_id=docente.id,
                titulo=titulo or f'Clase de {docente.especialidad}',
                descripcion=descripcion,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                duracion_minutos=duracion,
                monto=monto,
                estado='pendiente',
                link_jitsi=f"https://{current_app.config.get('JITSI_SERVER', 'meet.jit.si')}/clase-{uuid.uuid4().hex[:10]}"
            )
            
            db.session.add(clase)
            db.session.commit()
            
            # Redirigir a pago
            return redirect(url_for('main.pagar_clase', clase_id=clase.id))
            
        except ValueError:
            flash('Fecha u hora inválida', 'danger')
            return render_template('clases/reservar.html', docente=docente)
    
    return render_template('clases/reservar.html', docente=docente)


@main.route('/pagar-clase/<int:clase_id>')
@login_required
def pagar_clase(clase_id):
    """Página de pago de una clase"""
    clase = Clase.query.get_or_404(clase_id)
    
    if clase.cliente_id != current_user.id:
        flash('No tienes permiso para pagar esta clase', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if clase.estado_pago:
        flash('Esta clase ya ha sido pagada', 'info')
        return redirect(url_for('main.mis_clases'))
    
    # Configurar Stripe
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    try:
        # Crear intento de pago con Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(clase.monto * 100),  # Convertir a centavos
            currency='usd',
            metadata={
                'clase_id': clase.id,
                'cliente_id': current_user.id,
                'docente_id': clase.docente_id
            },
            description=f'Clase: {clase.titulo}'
        )
        
        return render_template('clases/pagar.html',
                             clase=clase,
                             client_secret=intent.client_secret,
                             publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY'))
    
    except Exception as e:
        current_app.logger.error(f'Error creando Payment Intent: {e}')
        flash('Error al procesar el pago. Por favor intenta nuevamente.', 'danger')
        return redirect(url_for('main.dashboard'))


@main.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook de Stripe para confirmar pagos"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Manejar evento de pago exitoso
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        clase_id = payment_intent['metadata']['clase_id']
        
        clase = Clase.query.get(clase_id)
        if clase:
            # Actualizar estado de pago
            clase.estado_pago = True
            clase.estado = 'confirmada'
            
            # Registrar pago
            pago = Pago(
                clase_id=clase.id,
                usuario_id=clase.cliente_id,
                monto=payment_intent['amount'] / 100,
                metodo_pago='stripe',
                estado='completado',
                transaction_id=payment_intent['id'],
                stripe_payment_intent_id=payment_intent['id']
            )
            
            db.session.add(pago)
            
            # Actualizar total de clases del docente
            docente = Docente.query.get(clase.docente_id)
            docente.total_clases += 1
            
            db.session.commit()
            
            # Enviar notificaciones
            from .tasks import enviar_confirmacion_clase
            enviar_confirmacion_clase.delay(clase.id)
    
    return '', 200


@main.route('/mis-clases')
@login_required
def mis_clases():
    """Listado de clases del usuario"""
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    
    if current_user.rol == 'cliente':
        query = Clase.query.filter_by(cliente_id=current_user.id)
    elif current_user.rol == 'docente':
        docente = Docente.query.filter_by(usuario_id=current_user.id).first()
        if not docente:
            flash('Perfil de docente no configurado', 'warning')
            return redirect(url_for('main.dashboard'))
        query = Clase.query.filter_by(docente_id=docente.id)
    else:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if estado:
        query = query.filter_by(estado=estado)
    
    clases = query.order_by(Clase.fecha_inicio.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('clases/mis_clases.html', clases=clases)


@main.route('/clase/<int:clase_id>')
@login_required
def detalle_clase(clase_id):
    """Detalle de una clase"""
    clase = Clase.query.get_or_404(clase_id)
    
    # Verificar permisos
    if current_user.rol == 'cliente' and clase.cliente_id != current_user.id:
        flash('No tienes permiso para ver esta clase', 'danger')
        return redirect(url_for('main.dashboard'))
    elif current_user.rol == 'docente':
        docente = Docente.query.filter_by(usuario_id=current_user.id).first()
        if not docente or clase.docente_id != docente.id:
            flash('No tienes permiso para ver esta clase', 'danger')
            return redirect(url_for('main.dashboard'))
    
    # Materiales de la clase
    materiales = Material.query.filter_by(clase_id=clase_id).all()
    
    # Calificaciones (si es estudiante)
    calificaciones = []
    if current_user.rol == 'cliente':
        calificaciones = Calificacion.query.filter_by(
            clase_id=clase_id,
            estudiante_id=current_user.id
        ).all()
    
    return render_template('clases/detalle.html',
                         clase=clase,
                         materiales=materiales,
                         calificaciones=calificaciones)


@main.route('/perfil')
@login_required
def perfil():
    """Perfil del usuario"""
    return render_template('perfil/perfil.html')


@main.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """Editar perfil del usuario"""
    if request.method == 'POST':
        current_user.nombre = request.form.get('nombre', '').strip()
        current_user.telefono = request.form.get('telefono', '').strip()
        
        # Si es docente, actualizar información adicional
        if current_user.rol == 'docente':
            docente = Docente.query.filter_by(usuario_id=current_user.id).first()
            if docente:
                docente.especialidad = request.form.get('especialidad', '').strip()
                docente.descripcion = request.form.get('descripcion', '').strip()
                docente.experiencia = request.form.get('experiencia', '').strip()
                docente.educacion = request.form.get('educacion', '').strip()
                docente.precio_hora = float(request.form.get('precio_hora', docente.precio_hora))
        
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('main.perfil'))
    
    return render_template('perfil/editar.html')


@main.route('/completar-perfil-docente', methods=['GET', 'POST'])
@login_required
def completar_perfil_docente():
    """Completar perfil de docente"""
    if current_user.rol != 'docente':
        flash('Esta página es solo para docentes', 'danger')
        return redirect(url_for('main.dashboard'))
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    
    if request.method == 'POST':
        especialidad = request.form.get('especialidad', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        experiencia = request.form.get('experiencia', '').strip()
        educacion = request.form.get('educacion', '').strip()
        plan_estudio = request.form.get('plan_estudio', '').strip()
        precio_hora = float(request.form.get('precio_hora', 0))
        
        # Métodos de pago
        paypal_email = request.form.get('paypal_email', '').strip()
        banco_nombre = request.form.get('banco_nombre', '').strip()
        banco_tipo = request.form.get('banco_tipo', '').strip()
        banco_cuenta = request.form.get('banco_cuenta', '').strip()
        banco_titular = request.form.get('banco_titular', '').strip()
        metodo_pago_preferido = request.form.get('metodo_pago_preferido', 'manual')
        
        if not all([especialidad, descripcion, precio_hora]):
            flash('Por favor completa todos los campos obligatorios', 'danger')
            return render_template('perfil/completar_docente.html', docente=docente)
        
        if not docente:
            docente = Docente(usuario_id=current_user.id)
            db.session.add(docente)
        
        docente.especialidad = especialidad
        docente.descripcion = descripcion
        docente.experiencia = experiencia
        docente.educacion = educacion
        docente.plan_estudio = plan_estudio
        docente.precio_hora = precio_hora
        
        # Guardar métodos de pago
        docente.paypal_email = paypal_email if paypal_email else None
        docente.banco_nombre = banco_nombre if banco_nombre else None
        docente.banco_tipo = banco_tipo if banco_tipo else None
        docente.banco_cuenta = banco_cuenta if banco_cuenta else None
        docente.banco_titular = banco_titular if banco_titular else None
        docente.metodo_pago_preferido = metodo_pago_preferido
        
        db.session.commit()
        flash('✅ Perfil de docente actualizado. Pendiente de verificación por el administrador.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('perfil/completar_docente.html', docente=docente)


# ==================== RUTAS ADICIONALES ====================

@main.route('/buscar-docentes')
def buscar_docentes():
    """Búsqueda de docentes con filtros"""
    # Manejar diferentes parámetros de búsqueda
    q = request.args.get('q', '').strip()  # Búsqueda general desde dashboard
    especialidad = request.args.get('especialidad', '').strip()
    buscar = request.args.get('buscar', '').strip()  # Búsqueda desde listado
    precio_min = request.args.get('precio_min', type=float)
    precio_max = request.args.get('precio_max', type=float)
    calificacion = request.args.get('calificacion', type=float)
    
    query = Docente.query.filter_by(verificado=True)
    
    # Búsqueda general (q) - busca en nombre y especialidad
    if q:
        query = query.join(Usuario).filter(
            or_(
                Usuario.nombre.ilike(f'%{q}%'),
                Docente.descripcion.ilike(f'%{q}%'),
                Docente.especialidad.ilike(f'%{q}%')
            )
        )
    
    # Búsqueda por especialidad específica
    if especialidad:
        query = query.filter(Docente.especialidad.ilike(f'%{especialidad}%'))
    
    # Búsqueda desde listado
    if buscar:
        query = query.join(Usuario).filter(
            or_(
                Usuario.nombre.ilike(f'%{buscar}%'),
                Docente.descripcion.ilike(f'%{buscar}%'),
                Docente.especialidad.ilike(f'%{buscar}%')
            )
        )
    
    # Filtros de precio
    if precio_min:
        query = query.filter(Docente.precio_hora >= precio_min)
    if precio_max:
        query = query.filter(Docente.precio_hora <= precio_max)
    
    # Obtener todos los docentes que cumplen con los filtros básicos
    docentes = query.all()
    
    # Filtrar por calificación promedio (es una propiedad, no campo de DB)
    if calificacion:
        docentes = [d for d in docentes if d.promedio_calificacion >= calificacion]
    
    # Ordenar por calificación promedio
    docentes = sorted(docentes, key=lambda d: d.promedio_calificacion, reverse=True)
    
    return render_template('docentes/buscar.html', docentes=docentes)


@main.route('/calendario')
@login_required
def calendario():
    """Calendario de clases del usuario"""
    if current_user.rol == 'docente':
        docente = Docente.query.filter_by(usuario_id=current_user.id).first()
        if docente:
            clases = Clase.query.filter_by(docente_id=docente.id).all()
        else:
            clases = []
    else:
        clases = Clase.query.filter_by(cliente_id=current_user.id).all()
    
    return render_template('calendario.html', clases=clases)


@main.route('/configuracion')
@login_required
def configuracion():
    """Configuración de cuenta"""
    return render_template('configuracion.html')


@main.route('/finanzas')
@login_required
def finanzas():
    """Panel financiero para docentes"""
    if current_user.rol != 'docente':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('main.dashboard'))
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    if not docente:
        flash('Completa tu perfil de docente primero', 'warning')
        return redirect(url_for('main.completar_perfil_docente'))
    
    # Calcular estadísticas financieras
    clases_completadas = Clase.query.filter_by(
        docente_id=docente.id,
        estado='completada',
        estado_pago=True
    ).all()
    
    # Todas las clases (para mostrar en transacciones)
    clases = Clase.query.filter_by(docente_id=docente.id).order_by(Clase.fecha_inicio.desc()).all()
    
    # Historial de retiros
    retiros = Retiro.query.filter_by(docente_id=docente.id).order_by(Retiro.fecha_solicitud.desc()).all()
    retiros_pendientes = Retiro.query.filter_by(docente_id=docente.id, estado='pendiente').count()
    
    total_ingresos = sum(clase.monto for clase in clases_completadas if clase.monto)
    ingresos_mes_actual = sum(
        clase.monto for clase in clases_completadas 
        if clase.fecha_inicio and clase.fecha_inicio.month == datetime.utcnow().month and clase.monto
    )
    
    return render_template('finanzas.html', 
                         docente=docente,
                         total_ingresos=total_ingresos,
                         ingresos_mes_actual=ingresos_mes_actual,
                         clases_completadas=len(clases_completadas),
                         clases=clases,
                         retiros=retiros,
                         retiros_pendientes=retiros_pendientes)


@main.route('/solicitar-retiro', methods=['POST'])
@login_required
def solicitar_retiro():
    """Procesar solicitud de retiro de un docente"""
    if current_user.rol != 'docente':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('main.dashboard'))
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    if not docente:
        flash('Completa tu perfil de docente primero', 'warning')
        return redirect(url_for('main.completar_perfil_docente'))
    
    try:
        monto = float(request.form.get('monto', 0))
        metodo_pago = request.form.get('metodo_pago')
        notas_docente = request.form.get('notas_docente', '')
        
        # Validaciones
        if monto < 50:
            flash('El monto mínimo para retiro es $50.00', 'danger')
            return redirect(url_for('main.finanzas'))
        
        if monto > docente.saldo_disponible:
            flash(f'No tienes suficiente saldo disponible. Máximo: ${docente.saldo_disponible:.2f}', 'danger')
            return redirect(url_for('main.finanzas'))
        
        if metodo_pago not in ['paypal', 'banco', 'stripe', 'manual']:
            flash('Método de pago inválido', 'danger')
            return redirect(url_for('main.finanzas'))
        
        # Verificar que tiene el método configurado
        if metodo_pago == 'paypal' and not docente.paypal_email:
            flash('No tienes una cuenta PayPal configurada', 'danger')
            return redirect(url_for('main.finanzas'))
        
        if metodo_pago == 'banco' and not docente.banco_nombre:
            flash('No tienes una cuenta bancaria configurada', 'danger')
            return redirect(url_for('main.finanzas'))
        
        # Verificar que no tiene retiros pendientes
        retiro_pendiente = Retiro.query.filter_by(
            docente_id=docente.id,
            estado='pendiente'
        ).first()
        
        if retiro_pendiente:
            flash('Ya tienes un retiro pendiente. Espera a que sea procesado.', 'warning')
            return redirect(url_for('main.finanzas'))
        
        # Preparar datos de pago
        datos_pago = {}
        if metodo_pago == 'paypal':
            datos_pago = {'email': docente.paypal_email}
        elif metodo_pago == 'banco':
            datos_pago = {
                'banco': docente.banco_nombre,
                'cuenta': docente.banco_cuenta,
                'titular': docente.banco_titular,
                'tipo': docente.banco_tipo
            }
        
        # Crear el retiro
        retiro = Retiro(
            docente_id=docente.id,
            monto=monto,
            metodo_pago=metodo_pago,
            datos_pago=str(datos_pago),
            notas_docente=notas_docente
        )
        
        db.session.add(retiro)
        db.session.commit()
        
        flash(f'✅ Solicitud de retiro de ${monto:.2f} enviada correctamente. ID: #{retiro.id}', 'success')
        
        # TODO: Enviar email al admin notificando
        
    except ValueError:
        flash('Error: Monto inválido', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar la solicitud: {str(e)}', 'danger')
        logger.error(f"Error al solicitar retiro: {e}")
    
    return redirect(url_for('main.finanzas'))


# ==================== PÁGINAS INFORMATIVAS ====================

@main.route('/sobre-nosotros')
def sobre_nosotros():
    """Página Sobre Nosotros"""
    return render_template('info/sobre_nosotros.html')


@main.route('/como-funciona')
def como_funciona():
    """Página Cómo Funciona"""
    return render_template('info/como_funciona.html')


@main.route('/contacto')
def contacto():
    """Página de Contacto"""
    return render_template('info/contacto.html')


@main.route('/terminos')
def terminos():
    """Términos y Condiciones"""
    return render_template('info/terminos.html')


@main.route('/privacidad')
def privacidad():
    """Política de Privacidad"""
    return render_template('info/privacidad.html')


@main.route('/manual-retiros')
def manual_retiros():
    """Manual completo del sistema de retiros"""
    return render_template('manual_retiros.html')


@main.route('/documentacion-tecnica-retiros')
def documentacion_tecnica_retiros():
    """Documentación técnica de implementación del sistema de retiros"""
    return render_template('documentacion_tecnica_retiros.html')        


# ============================================================================
# RUTAS PARA GESTIÓN DE MATERIALES PDF (DOCENTES)
# ============================================================================

# Configuración de archivos permitidos
MAX_FILE_SIZE_MB = 3
MAX_FILES_PER_DOCENTE = 5
ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = 'uploads/materiales'

def allowed_file(filename):
    """Verificar si el archivo tiene extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/docente/materiales')
@login_required
def mis_materiales():
    """Vista de materiales del docente"""
    if current_user.rol != 'docente':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('main.dashboard'))
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    if not docente:
        flash('Perfil de docente no encontrado', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Obtener materiales del docente
    materiales = Material.query.filter_by(docente_id=docente.id, tipo='pdf').order_by(Material.fecha_subida.desc()).all()
    
    # Obtener estudiantes (clientes con clases con este docente)
    estudiantes = Usuario.query.join(Clase, Usuario.id == Clase.cliente_id).filter(
        Clase.docente_id == docente.id,
        Usuario.rol == 'cliente'
    ).distinct().all()
    
    return render_template('docentes/materiales.html', 
                         materiales=materiales, 
                         estudiantes=estudiantes,
                         max_archivos=MAX_FILES_PER_DOCENTE,
                         docente=docente)


@main.route('/docente/materiales/subir', methods=['POST'])
@login_required
def subir_material():
    """Subir un archivo PDF"""
    if current_user.rol != 'docente':
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    if not docente:
        return jsonify({'error': 'Perfil de docente no encontrado'}), 404
    
    # Verificar límite de archivos
    count_materiales = Material.query.filter_by(docente_id=docente.id, tipo='pdf').count()
    if count_materiales >= MAX_FILES_PER_DOCENTE:
        return jsonify({'error': f'Has alcanzado el límite de {MAX_FILES_PER_DOCENTE} archivos. Elimina alguno antes de subir más.'}), 400
    
    # Verificar que se envió un archivo
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['archivo']
    titulo = request.form.get('titulo', '')
    descripcion = request.form.get('descripcion', '')
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    
    # Verificar tamaño del archivo (convertir MB a bytes)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        return jsonify({'error': f'El archivo excede el tamaño máximo de {MAX_FILE_SIZE_MB} MB'}), 400
    
    # Guardar archivo
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Crear directorio si no existe
    upload_path = os.path.join('app', 'static', UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)
    
    filepath = os.path.join(upload_path, unique_filename)
    file.save(filepath)
    
    # Crear registro en la base de datos
    material = Material(
        docente_id=docente.id,
        titulo=titulo or filename,
        descripcion=descripcion,
        tipo='pdf',
        archivo_path=os.path.join(UPLOAD_FOLDER, unique_filename),
        tamanio_kb=int(file_size / 1024),
        publico=False
    )
    
    db.session.add(material)
    db.session.commit()
    
    flash('Archivo PDF subido correctamente', 'success')
    return jsonify({'success': True, 'material_id': material.id})


@main.route('/docente/materiales/<int:material_id>/compartir', methods=['POST'])
@login_required
def compartir_material():
    """Compartir un material con uno o más estudiantes"""
    if current_user.rol != 'docente':
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    if not docente:
        return jsonify({'error': 'Perfil de docente no encontrado'}), 404
    
    material = Material.query.get_or_404(material_id)
    
    # Verificar que el material pertenece al docente
    if material.docente_id != docente.id:
        return jsonify({'error': 'No tienes permiso para compartir este material'}), 403
    
    # Obtener lista de estudiantes
    estudiante_ids = request.json.get('estudiante_ids', [])
    
    if not estudiante_ids:
        return jsonify({'error': 'Debes seleccionar al menos un estudiante'}), 400
    
    # Compartir con cada estudiante
    for estudiante_id in estudiante_ids:
        estudiante = Usuario.query.get(estudiante_id)
        if estudiante and estudiante.rol == 'cliente':
            # Verificar que el estudiante no tenga ya acceso
            if estudiante not in material.estudiantes_compartidos:
                material.estudiantes_compartidos.append(estudiante)
    
    db.session.commit()
    
    flash(f'Material compartido con {len(estudiante_ids)} estudiante(s)', 'success')
    return jsonify({'success': True})


@main.route('/docente/materiales/<int:material_id>/eliminar', methods=['POST'])
@login_required
def eliminar_material():
    """Eliminar un material (docente)"""
    if current_user.rol != 'docente':
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    docente = Docente.query.filter_by(usuario_id=current_user.id).first()
    if not docente:
        return jsonify({'error': 'Perfil de docente no encontrado'}), 404
    
    material = Material.query.get_or_404(material_id)
    
    # Verificar que el material pertenece al docente
    if material.docente_id != docente.id:
        return jsonify({'error': 'No tienes permiso para eliminar este material'}), 403
    
    # Eliminar archivo físico si existe
    if material.archivo_path:
        filepath = os.path.join('app', 'static', material.archivo_path)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error al eliminar archivo: {e}")
    
    # Eliminar registro de la base de datos
    db.session.delete(material)
    db.session.commit()
    
    flash('Material eliminado correctamente', 'success')
    return jsonify({'success': True})


@main.route('/materiales/<int:material_id>/descargar')
@login_required
def descargar_material(material_id):
    """Descargar un material PDF"""
    material = Material.query.get_or_404(material_id)
    
    # Verificar permisos
    tiene_acceso = False
    
    if current_user.rol == 'admin':
        tiene_acceso = True
    elif current_user.rol == 'docente':
        docente = Docente.query.filter_by(usuario_id=current_user.id).first()
        if docente and material.docente_id == docente.id:
            tiene_acceso = True
    elif current_user.rol == 'cliente':
        # El estudiante debe estar en la lista de compartidos
        if current_user in material.estudiantes_compartidos:
            tiene_acceso = True
    
    if not tiene_acceso:
        flash('No tienes permiso para descargar este material', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Incrementar contador de descargas
    material.descargas += 1
    db.session.commit()
    
    # Enviar archivo
    filepath = os.path.join('app', 'static', material.archivo_path)
    if not os.path.exists(filepath):
        flash('El archivo no existe', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return send_file(filepath, as_attachment=True, download_name=f"{material.titulo}.pdf")


@main.route('/estudiante/materiales')
@login_required
def mis_materiales_estudiante():
    """Vista de materiales compartidos con el estudiante"""
    if current_user.rol != 'cliente':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Obtener materiales compartidos con este estudiante
    materiales = current_user.materiales_compartidos.filter(Material.tipo == 'pdf').order_by(Material.fecha_subida.desc()).all()
    
    return render_template('clases/materiales_estudiante.html', materiales=materiales)
