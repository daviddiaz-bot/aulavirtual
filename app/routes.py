"""
Rutas Principales de Aula Virtual
Maneja las vistas principales de la aplicación
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from .models import Usuario, Docente, Clase, Pago, Resena, Material, Calificacion, Notificacion, db
from datetime import datetime, timedelta
from sqlalchemy import func, or_
import uuid
import stripe

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
        precio_hora = float(request.form.get('precio_hora', 0))
        
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
        docente.precio_hora = precio_hora
        
        db.session.commit()
        flash('Perfil de docente actualizado. Pendiente de verificación por el administrador.', 'info')
        return redirect(url_for('main.dashboard'))
    
    return render_template('perfil/completar_docente.html', docente=docente)


# ==================== RUTAS ADICIONALES ====================

@main.route('/buscar-docentes')
def buscar_docentes():
    """Búsqueda de docentes con filtros"""
    especialidad = request.args.get('especialidad', '')
    precio_min = request.args.get('precio_min', type=float)
    precio_max = request.args.get('precio_max', type=float)
    calificacion = request.args.get('calificacion', type=float)
    
    query = Docente.query.filter_by(verificado=True)
    
    if especialidad:
        query = query.filter(Docente.especialidad.ilike(f'%{especialidad}%'))
    if precio_min:
        query = query.filter(Docente.precio_hora >= precio_min)
    if precio_max:
        query = query.filter(Docente.precio_hora <= precio_max)
    if calificacion:
        query = query.filter(Docente.calificacion_promedio >= calificacion)
    
    docentes = query.order_by(Docente.calificacion_promedio.desc()).all()
    
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
        estado='completada'
    ).all()
    
    total_ingresos = sum(clase.precio for clase in clases_completadas if clase.precio)
    ingresos_mes_actual = sum(
        clase.precio for clase in clases_completadas 
        if clase.fecha_inicio and clase.fecha_inicio.month == datetime.utcnow().month and clase.precio
    )
    
    return render_template('finanzas.html', 
                         docente=docente,
                         total_ingresos=total_ingresos,
                         ingresos_mes_actual=ingresos_mes_actual,
                         clases_completadas=len(clases_completadas))


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
