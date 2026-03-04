"""
Modelos de la Base de Datos para Aula Virtual
Define todas las entidades y sus relaciones
"""

from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pyotp
import base64
import os


class Usuario(UserMixin, db.Model):
    """Modelo de Usuario - Administradores, Docentes y Clientes/Estudiantes"""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200))
    rol = db.Column(db.String(20), nullable=False)  # admin, cliente, docente
    telefono = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    activo = db.Column(db.Boolean, default=True)
    
    # Campos para 2FA
    totp_secret = db.Column(db.String(32))
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    backup_codes = db.Column(db.Text)
    
    # Relaciones
    docente = db.relationship('Docente', backref='usuario', uselist=False, cascade='all, delete-orphan')
    clases_cliente = db.relationship('Clase', foreign_keys='Clase.cliente_id', backref='cliente', lazy='dynamic')
    
    def set_password(self, password):
        """Establecer contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def generate_totp_secret(self):
        """Generar secreto para 2FA"""
        if not self.totp_secret:
            self.totp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')
        return self.totp_secret
    
    def get_totp_uri(self):
        """Obtener URI para QR code"""
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name="Aula Virtual"
        )
    
    def verify_totp(self, token):
        """Verificar token TOTP"""
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self):
        """Generar códigos de respaldo"""
        import secrets
        codes = []
        for _ in range(10):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        self.backup_codes = ','.join([generate_password_hash(c) for c in codes])
        return codes
    
    def verify_backup_code(self, code):
        """Verificar código de respaldo"""
        if not self.backup_codes:
            return False
        codes = self.backup_codes.split(',')
        for idx, hashed_code in enumerate(codes):
            if check_password_hash(hashed_code, code):
                codes.pop(idx)
                self.backup_codes = ','.join(codes)
                return True
        return False
    
    def __repr__(self):
        return f'<Usuario {self.nombre} - {self.rol}>'


class Docente(db.Model):
    """Modelo de Docente - Información adicional de profesores"""
    
    __tablename__ = 'docentes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    especialidad = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    experiencia = db.Column(db.Text)
    educacion = db.Column(db.Text)
    precio_hora = db.Column(db.Float, nullable=False, default=0.0)
    disponibilidad = db.Column(db.Text)  # JSON con horarios
    calificacion_promedio = db.Column(db.Float, default=0.0)
    total_clases = db.Column(db.Integer, default=0)
    verificado = db.Column(db.Boolean, default=False)
    fecha_aprobacion = db.Column(db.DateTime)
    
    # Relaciones
    clases = db.relationship('Clase', foreign_keys='Clase.docente_id', backref='docente_rel', lazy='dynamic')
    resenas = db.relationship('Resena', backref='docente', lazy='dynamic')
    materiales = db.relationship('Material', backref='docente', lazy='dynamic')
    
    @property
    def promedio_calificacion(self):
        """Calcular promedio de calificaciones"""
        resenas = self.resenas.all()
        if not resenas:
            return 0.0
        return round(sum(r.calificacion for r in resenas) / len(resenas), 1)
    
    @property
    def total_resenas(self):
        """Total de reseñas"""
        return self.resenas.count()
    
    def __repr__(self):
        return f'<Docente {self.usuario.nombre}>'


class Clase(db.Model):
    """Modelo de Clase - Sesiones educativas"""
    
    __tablename__ = 'clases'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    titulo = db.Column(db.String(200))
    descripcion = db.Column(db.Text)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime)
    duracion_minutos = db.Column(db.Integer, default=60)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, confirmada, cancelada, completada
    estado_pago = db.Column(db.Boolean, default=False)
    monto = db.Column(db.Float, nullable=False)
    link_jitsi = db.Column(db.String(255))
    notas_cliente = db.Column(db.Text)
    notas_docente = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    pago = db.relationship('Pago', backref='clase', uselist=False)
    resena = db.relationship('Resena', backref='clase', uselist=False)
    materiales = db.relationship('Material', backref='clase', lazy='dynamic')
    asistencias = db.relationship('Asistencia', backref='clase', lazy='dynamic')
    
    def __repr__(self):
        return f'<Clase {self.id} - {self.titulo}>'


class Pago(db.Model):
    """Modelo de Pago - Transacciones"""
    
    __tablename__ = 'pagos'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))  # stripe, paypal, etc.
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, completado, fallido, reembolsado
    transaction_id = db.Column(db.String(100), unique=True)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    stripe_payment_intent_id = db.Column(db.String(100))
    
    # Relación
    usuario = db.relationship('Usuario', backref='pagos')
    
    def __repr__(self):
        return f'<Pago {self.id} - ${self.monto}>'


class Resena(db.Model):
    """Modelo de Reseña - Calificaciones y comentarios"""
    
    __tablename__ = 'resenas'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    calificacion = db.Column(db.Integer, nullable=False)  # 1-5 estrellas
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    visible = db.Column(db.Boolean, default=True)
    
    # Relación
    cliente = db.relationship('Usuario', foreign_keys=[cliente_id], backref='resenas')
    
    def __repr__(self):
        return f'<Resena {self.id} - {self.calificacion} estrellas>'


class Material(db.Model):
    """Modelo de Material - Recursos educativos"""
    
    __tablename__ = 'materiales'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'))
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # pdf, video, presentacion, etc.
    url = db.Column(db.String(500))
    archivo_path = db.Column(db.String(500))
    tamanio_kb = db.Column(db.Integer)
    publico = db.Column(db.Boolean, default=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    descargas = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Material {self.titulo}>'


class Asistencia(db.Model):
    """Modelo de Asistencia - Control de asistencia"""
    
    __tablename__ = 'asistencias'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    presente = db.Column(db.Boolean, default=False)
    hora_entrada = db.Column(db.DateTime)
    hora_salida = db.Column(db.DateTime)
    notas = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    usuario = db.relationship('Usuario', backref='asistencias')
    
    def __repr__(self):
        return f'<Asistencia {self.id} - Clase {self.clase_id}>'


class Calificacion(db.Model):
    """Modelo de Calificación - Notas de estudiantes"""
    
    __tablename__ = 'calificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    tipo = db.Column(db.String(50))  # tarea, examen, participacion, etc.
    titulo = db.Column(db.String(200))
    nota = db.Column(db.Float)
    nota_maxima = db.Column(db.Float, default=100.0)
    comentarios = db.Column(db.Text)
    fecha_evaluacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    estudiante = db.relationship('Usuario', foreign_keys=[estudiante_id], backref='calificaciones')
    docente = db.relationship('Docente', foreign_keys=[docente_id], backref='calificaciones_dadas')
    clase_rel = db.relationship('Clase', backref='calificaciones')
    
    @property
    def porcentaje(self):
        """Calcular porcentaje"""
        if self.nota_maxima == 0:
            return 0
        return round((self.nota / self.nota_maxima) * 100, 2)
    
    def __repr__(self):
        return f'<Calificacion {self.id} - {self.nota}/{self.nota_maxima}>'


class Notificacion(db.Model):
    """Modelo de Notificación - Alertas para usuarios"""
    
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50))  # clase, pago, mensaje, sistema
    titulo = db.Column(db.String(200))
    mensaje = db.Column(db.Text)
    leida = db.Column(db.Boolean, default=False)
    url = db.Column(db.String(500))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_leida = db.Column(db.DateTime)
    
    # Relación
    usuario = db.relationship('Usuario', backref='notificaciones')
    
    def __repr__(self):
        return f'<Notificacion {self.id} - {self.titulo}>'
