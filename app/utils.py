"""
Utilidades y funciones auxiliares de Aula Virtual
"""

from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import secrets
import string


def generate_reset_token(usuario):
    """Generar token para resetear contraseña"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(usuario.email, salt='password-reset-salt')


def verify_reset_token(token, expiration=3600):
    """Verificar token de reset de contraseña"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    
    from .models import Usuario
    return Usuario.query.filter_by(email=email).first()


def generate_random_password(length=12):
    """Generar contraseña aleatoria"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def format_currency(amount):
    """Formatear cantidad como moneda"""
    return f"${amount:,.2f}"


def format_datetime(dt, format='%d/%m/%Y %H:%M'):
    """Formatear fecha y hora"""
    if not dt:
        return ''
    return dt.strftime(format)


def allowed_file(filename, allowed_extensions=None):
    """Verificar si el archivo tiene extensión permitida"""
    if not allowed_extensions:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_extension(filename):
    """Obtener extensión del archivo"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def create_notification(usuario_id, tipo, titulo, mensaje, url=None):
    """Crear una notificación para un usuario"""
    from .models import Notificacion, db
    
    notificacion = Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        url=url
    )
    
    db.session.add(notificacion)
    db.session.commit()
    
    return notificacion


def calcular_edad(fecha_nacimiento):
    """Calcular edad a partir de fecha de nacimiento"""
    if not fecha_nacimiento:
        return None
    
    hoy = datetime.today()
    edad = hoy.year - fecha_nacimiento.year
    
    if hoy.month < fecha_nacimiento.month or \
       (hoy.month == fecha_nacimiento.month and hoy.day < fecha_nacimiento.day):
        edad -= 1
    
    return edad


def generar_slug(texto):
    """Generar slug a partir de un texto"""
    import unicodedata
    import re
    
    # Normalizar y remover acentos
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    
    # Convertir a minúsculas y reemplazar espacios
    texto = texto.lower()
    texto = re.sub(r'[^\w\s-]', '', texto)
    texto = re.sub(r'[-\s]+', '-', texto)
    
    return texto.strip('-')
