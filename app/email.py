"""
Sistema de Envío de Emails de Aula Virtual
Gestiona el envío de correos electrónicos usando Flask-Mail
"""

from flask import render_template, current_app
from flask_mail import Message
from . import mail
from threading import Thread


def send_async_email(app, msg):
    """Enviar email de forma asíncrona"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f'Error enviando email: {e}')


def send_email(to, subject, template, **kwargs):
    """
    Enviar email usando template
    
    Args:
        to: Dirección de correo destinatario
        subject: Asunto del correo
        template: Nombre del template (sin extensión)
        **kwargs: Variables para el template
    """
    app = current_app._get_current_object()
    
    msg = Message(
        subject=f"{app.config.get('APP_NAME', 'Aula Virtual')} - {subject}",
        sender=app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[to] if isinstance(to, str) else to
    )
    
    try:
        msg.body = render_template(f'{template}.txt', **kwargs)
        msg.html = render_template(f'{template}.html', **kwargs)
    except Exception as e:
        app.logger.error(f'Error renderizando template de email: {e}')
        return None
    
    # Enviar de forma asíncrona
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    
    return thr
