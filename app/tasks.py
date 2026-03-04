"""
Tareas Asíncronas de Celery para Aula Virtual
Gestiona tareas en segundo plano como envío de emails y notificaciones
"""

from celery import Celery
from flask import current_app
import os

celery = Celery(
    __name__,
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)


@celery.task
def enviar_confirmacion_clase(clase_id):
    """Enviar confirmación de clase por email"""
    from app import create_app, db
    from app.models import Clase
    from app.email import send_email
    
    app = create_app()
    with app.app_context():
        clase = Clase.query.get(clase_id)
        if not clase:
            return
        
        # Email al cliente
        send_email(
            to=clase.cliente.email,
            subject='Confirmación de Clase',
            template='email/confirmacion_clase',
            clase=clase,
            usuario=clase.cliente
        )
        
        # Email al docente
        send_email(
            to=clase.docente_rel.usuario.email,
            subject='Nueva Clase Reservada',
            template='email/nueva_clase_docente',
            clase=clase,
            usuario=clase.docente_rel.usuario
        )


@celery.task
def enviar_recordatorio_clase(clase_id):
    """Enviar recordatorio de clase 24 horas antes"""
    from app import create_app
    from app.models import Clase
    from app.email import send_email
    
    app = create_app()
    with app.app_context():
        clase = Clase.query.get(clase_id)
        if not clase or clase.estado != 'confirmada':
            return
        
        # Recordatorio al cliente
        send_email(
            to=clase.cliente.email,
            subject='Recordatorio: Clase Mañana',
            template='email/recordatorio_clase',
            clase=clase,
            usuario=clase.cliente
        )
        
        # Recordatorio al docente
        send_email(
            to=clase.docente_rel.usuario.email,
            subject='Recordatorio: Clase Mañana',
            template='email/recordatorio_clase',
            clase=clase,
            usuario=clase.docente_rel.usuario
        )


@celery.task
def enviar_aprobacion_docente(docente_id):
    """Enviar email de aprobación a un docente"""
    from app import create_app
    from app.models import Docente
    from app.email import send_email
    
    app = create_app()
    with app.app_context():
        docente = Docente.query.get(docente_id)
        if not docente:
            return
        
        send_email(
            to=docente.usuario.email,
            subject='¡Tu perfil ha sido aprobado!',
            template='email/aprobacion_docente',
            docente=docente,
            usuario=docente.usuario
        )


@celery.task
def procesar_pagos_pendientes():
    """Procesar pagos pendientes y actualizar estados"""
    from app import create_app, db
    from app.models import Pago
    from datetime import datetime, timedelta
    
    app = create_app()
    with app.app_context():
        # Buscar pagos pendientes de más de 24 horas
        tiempo_limite = datetime.utcnow() - timedelta(hours=24)
        pagos_pendientes = Pago.query.filter(
            Pago.estado == 'pendiente',
            Pago.fecha_pago < tiempo_limite
        ).all()
        
        for pago in pagos_pendientes:
            pago.estado = 'fallido'
            if pago.clase:
                pago.clase.estado = 'cancelada'
        
        db.session.commit()


@celery.task
def generar_reporte_diario():
    """Generar reporte diario de actividad"""
    from app import create_app
    from app.models import Clase, Usuario, Pago
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    app = create_app()
    with app.app_context():
        hoy = datetime.utcnow().date()
        ayer = hoy - timedelta(days=1)
        
        # Estadísticas del día
        clases_dia = Clase.query.filter(
            func.date(Clase.fecha_inicio) == ayer
        ).count()
        
        nuevos_usuarios = Usuario.query.filter(
            func.date(Usuario.fecha_registro) == ayer
        ).count()
        
        ingresos_dia = db.session.query(func.sum(Pago.monto)).filter(
            func.date(Pago.fecha_pago) == ayer,
            Pago.estado == 'completado'
        ).scalar() or 0
        
        # Enviar reporte a administradores
        admins = Usuario.query.filter_by(rol='admin', activo=True).all()
        
        for admin in admins:
            from app.email import send_email
            send_email(
                to=admin.email,
                subject='Reporte Diario de Actividad',
                template='email/reporte_diario',
                clases=clases_dia,
                usuarios=nuevos_usuarios,
                ingresos=round(ingresos_dia, 2),
                fecha=ayer
            )


# Configurar tareas periódicas
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configurar tareas periódicas"""
    
    # Procesar pagos pendientes cada hora
    sender.add_periodic_task(3600.0, procesar_pagos_pendientes.s(), name='procesar_pagos')
    
    # Generar reporte diario a las 8 AM
    sender.add_periodic_task(
        86400.0,  # 24 horas
        generar_reporte_diario.s(),
        name='reporte_diario'
    )
