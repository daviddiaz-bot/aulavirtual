"""
Módulo de Autenticación de Aula Virtual
Maneja registro, login, logout y autenticación de dos factores (2FA)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import Usuario, db
from .email import send_email
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        rol = request.form.get('rol', 'cliente')
        telefono = request.form.get('telefono', '').strip()
        
        # Validaciones
        if not all([nombre, email, password, password_confirm]):
            flash('Todos los campos son obligatorios', 'danger')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return render_template('auth/register.html')
        
        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado', 'danger')
            return render_template('auth/register.html')
        
        # Crear nuevo usuario
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=rol,
            telefono=telefono
        )
        usuario.set_password(password)
        
        try:
            db.session.add(usuario)
            db.session.commit()
            
            # Enviar email de bienvenida
            try:
                send_email(
                    to=usuario.email,
                    subject=f'¡Bienvenido a {current_app.config["APP_NAME"]}!',
                    template='email/bienvenida',
                    usuario=usuario
                )
            except Exception as e:
                current_app.logger.error(f'Error enviando email de bienvenida: {e}')
            
            flash('¡Registro exitoso! Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error en registro: {e}')
            flash('Error al crear la cuenta. Por favor intenta nuevamente.', 'danger')
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.activo and usuario.check_password(password):
            # Actualizar último acceso
            usuario.ultimo_acceso = datetime.utcnow()
            
            # Verificar si tiene 2FA habilitado
            if usuario.is_2fa_enabled:
                session['user_id_2fa'] = usuario.id
                session['remember_me'] = remember_me
                return redirect(url_for('auth.verify_2fa'))
            else:
                # Login normal sin 2FA
                login_user(usuario, remember=remember_me)
                db.session.commit()
                
                flash(f'¡Bienvenido, {usuario.nombre}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Verificación de autenticación de dos factores"""
    if 'user_id_2fa' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id_2fa']
    usuario = Usuario.query.get(user_id)
    
    if not usuario:
        session.pop('user_id_2fa', None)
        flash('Sesión expirada. Por favor inicia sesión nuevamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        use_backup = request.form.get('use_backup') == '1'
        
        if not token:
            flash('Por favor ingresa un código de verificación', 'danger')
            return render_template('auth/verify_2fa.html', usuario=usuario)
        
        if use_backup:
            # Verificar código de respaldo
            if usuario.verify_backup_code(token):
                session.pop('user_id_2fa', None)
                remember_me = session.pop('remember_me', False)
                login_user(usuario, remember=remember_me)
                usuario.ultimo_acceso = datetime.utcnow()
                db.session.commit()
                flash('Autenticado correctamente con código de respaldo', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Código de respaldo inválido', 'danger')
        else:
            # Verificar token TOTP
            if usuario.verify_totp(token):
                session.pop('user_id_2fa', None)
                remember_me = session.pop('remember_me', False)
                login_user(usuario, remember=remember_me)
                usuario.ultimo_acceso = datetime.utcnow()
                db.session.commit()
                flash('Autenticado correctamente', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Código de verificación inválido', 'danger')
    
    return render_template('auth/verify_2fa.html', usuario=usuario)


@auth_bp.route('/setup-2fa')
@login_required
def setup_2fa():
    """Configurar autenticación de dos factores"""
    usuario = current_user
    
    # Generar secreto si no existe
    if not usuario.totp_secret:
        usuario.generate_totp_secret()
        db.session.commit()
    
    # Generar URI para QR
    totp_uri = usuario.get_totp_uri()
    secret_key = usuario.totp_secret
    
    # Generar QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64 para mostrar en HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('auth/setup_2fa.html', 
                         qr_code=img_str, 
                         secret_key=secret_key)


@auth_bp.route('/enable-2fa', methods=['POST'])
@login_required
def enable_2fa():
    """Activar autenticación de dos factores"""
    usuario = current_user
    token = request.form.get('token', '').strip()
    
    if not token:
        flash('Por favor ingresa el código de verificación', 'danger')
        return redirect(url_for('auth.setup_2fa'))
    
    # Verificar token
    if usuario.verify_totp(token):
        usuario.is_2fa_enabled = True
        # Generar códigos de respaldo
        backup_codes = usuario.generate_backup_codes()
        db.session.commit()
        
        flash('Autenticación de dos factores activada correctamente', 'success')
        return render_template('auth/backup_codes.html', backup_codes=backup_codes)
    else:
        flash('Código inválido. No se pudo activar 2FA', 'danger')
        return redirect(url_for('auth.setup_2fa'))


@auth_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    """Desactivar autenticación de dos factores"""
    usuario = current_user
    password = request.form.get('password', '')
    
    # Verificar contraseña antes de desactivar
    if not usuario.check_password(password):
        flash('Contraseña incorrecta', 'danger')
        return redirect(url_for('main.perfil'))
    
    usuario.is_2fa_enabled = False
    usuario.totp_secret = None
    usuario.backup_codes = None
    db.session.commit()
    
    flash('Autenticación de dos factores desactivada', 'info')
    return redirect(url_for('main.perfil'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/recuperar-password', methods=['GET', 'POST'])
def recuperar_password():
    """Recuperación de contraseña"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Generar token de recuperación
            from .utils import generate_reset_token
            token = generate_reset_token(usuario)
            
            # Enviar email
            try:
                send_email(
                    to=usuario.email,
                    subject='Recuperación de Contraseña - Aula Virtual',
                    template='email/reset_password',
                    usuario=usuario,
                    token=token
                )
                flash('Se ha enviado un correo con instrucciones para recuperar tu contraseña', 'info')
            except Exception as e:
                current_app.logger.error(f'Error enviando email de recuperación: {e}')
                flash('Error al enviar el correo. Por favor intenta más tarde.', 'danger')
        else:
            # Por seguridad, no revelar si el email existe
            flash('Si el correo existe, recibirás instrucciones para recuperar tu contraseña', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/recuperar_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resetear contraseña con token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    from .utils import verify_reset_token
    usuario = verify_reset_token(token)
    
    if not usuario:
        flash('El enlace de recuperación es inválido o ha expirado', 'danger')
        return redirect(url_for('auth.recuperar_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if not password or len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if password != password_confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        usuario.set_password(password)
        db.session.commit()
        
        flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)


# Alias para ruta de recuperación de contraseña
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Alias para recuperar_password"""
    return recuperar_password()
