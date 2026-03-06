"""
Modelos de la Base de Datos para Aula Virtual
Define todas las entidades y sus relaciones
"""

from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
import pyotp
import base64
import os

# Tabla de asociación para materiales compartidos con estudiantes
material_estudiante = db.Table('material_estudiante',
    db.Column('material_id', db.Integer, db.ForeignKey('materiales.id'), primary_key=True),
    db.Column('estudiante_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('fecha_compartido', db.DateTime, default=datetime.utcnow)
)


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
    plan_estudio = db.Column(db.Text)  # Plan de estudio / Hoja de ruta
    precio_hora = db.Column(db.Float, nullable=False, default=0.0)
    disponibilidad = db.Column(db.Text)  # JSON con horarios
    calificacion_promedio = db.Column(db.Float, default=0.0)
    total_clases = db.Column(db.Integer, default=0)
    verificado = db.Column(db.Boolean, default=False)
    fecha_aprobacion = db.Column(db.DateTime)
    
    # Métodos de pago del docente
    paypal_email = db.Column(db.String(100))  # Email de PayPal
    stripe_account_id = db.Column(db.String(100))  # ID de Stripe Connect
    banco_nombre = db.Column(db.String(100))  # Nombre del banco
    banco_cuenta = db.Column(db.String(100))  # Número de cuenta (encriptado)
    banco_titular = db.Column(db.String(200))  # Nombre del titular
    banco_tipo = db.Column(db.String(50))  # Tipo: CLABE, CBU, IBAN, etc.
    metodo_pago_preferido = db.Column(db.String(20), default='manual')  # manual, paypal, stripe, banco
    
    # Relaciones
    clases = db.relationship('Clase', foreign_keys='Clase.docente_id', backref='docente_rel', lazy='dynamic')
    resenas = db.relationship('Resena', backref='docente', lazy='dynamic')
    materiales = db.relationship('Material', backref='docente', lazy='dynamic')
    retiros = db.relationship('Retiro', backref='docente', lazy='dynamic')
    
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
    
    @property
    def saldo_disponible(self):
        """Calcular saldo disponible para retiro"""
        # Ingresos de clases completadas
        ingresos = db.session.query(func.sum(Clase.monto)).filter(
            Clase.docente_id == self.id,
            Clase.estado == 'completada',
            Clase.estado_pago == True
        ).scalar() or 0.0
        
        # Aplicar comisión del sistema (85% para el docente)
        ingresos_netos = ingresos * 0.85
        
        # Restar retiros ya pagados
        retiros = db.session.query(func.sum(Retiro.monto)).filter(
            Retiro.docente_id == self.id,
            Retiro.estado.in_(['aprobado', 'pagado'])
        ).scalar() or 0.0
        
        return round(ingresos_netos - retiros, 2)
    
    @property
    def saldo_pendiente(self):
        """Saldo de clases confirmadas pero no completadas"""
        pendiente = db.session.query(func.sum(Clase.monto)).filter(
            Clase.docente_id == self.id,
            Clase.estado == 'confirmada',
            Clase.estado_pago == True
        ).scalar() or 0.0
        
        return round(pendiente * 0.85, 2)
    
    def esta_disponible(self, fecha_inicio, fecha_fin):
        """Verifica si el docente está disponible en un rango de fecha/hora"""
        # Verificar si hay una clase confirmada que se solape
        clases_solapadas = Clase.query.filter(
            Clase.docente_id == self.id,
            Clase.estado.in_(['pendiente', 'confirmada']),
            db.or_(
                db.and_(Clase.fecha_inicio <= fecha_inicio, Clase.fecha_fin > fecha_inicio),
                db.and_(Clase.fecha_inicio < fecha_fin, Clase.fecha_fin >= fecha_fin),
                db.and_(Clase.fecha_inicio >= fecha_inicio, Clase.fecha_fin <= fecha_fin)
            )
        ).first()
        
        if clases_solapadas:
            return False, 'Ya tienes una clase programada en ese horario'
        
        # Verificar disponibilidad semanal
        disponibilidades = DisponibilidadDocente.query.filter_by(
            docente_id=self.id,
            activo=True
        ).all()
        
        # Si no tiene disponibilidades definidas, asumimos que está disponible
        if disponibilidades:
            tiene_disponibilidad = False
            for disp in disponibilidades:
                if disp.esta_disponible_en(fecha_inicio):
                    tiene_disponibilidad = True
                    break
            
            if not tiene_disponibilidad:
                return False, 'Este horario no está en tu disponibilidad configurada'
        
        # Verificar bloques no disponibles
        bloques = BloqueNoDisponible.query.filter_by(docente_id=self.id).all()
        for bloque in bloques:
            if bloque.incluye_fecha(fecha_inicio):
                motivo = f'No disponible: {bloque.motivo}' if bloque.motivo else 'No disponible en esa fecha'
                return False, motivo
        
        return True, 'Disponible'
    
    def __repr__(self):
        return f'<Docente {self.usuario.nombre}>'


class DisponibilidadDocente(db.Model):
    """Modelo de Disponibilidad Horaria del Docente"""
    
    __tablename__ = 'disponibilidad_docente'
    
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Lunes, 1=Martes... 6=Domingo
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    docente_rel = db.relationship('Docente', backref='disponibilidades')
    
    def esta_disponible_en(self, fecha_hora):
        """Verifica si el docente está disponible en una fecha/hora específica"""
        if not self.activo:
            return False
        
        # Verificar día de la semana (Python usa 0=Lunes)
        if fecha_hora.weekday() != self.dia_semana:
            return False
        
        # Verificar hora
        hora = fecha_hora.time()
        return self.hora_inicio <= hora <= self.hora_fin
    
    def __repr__(self):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return f'<Disponibilidad {dias[self.dia_semana]} {self.hora_inicio}-{self.hora_fin}>'


class BloqueNoDisponible(db.Model):
    """Modelo para bloquear fechas/horas específicas (vacaciones, eventos personales, etc.)"""
    
    __tablename__ = 'bloques_no_disponibles'
    
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    docente_rel = db.relationship('Docente', backref='bloques_no_disponibles')
    
    def incluye_fecha(self, fecha_hora):
        """Verifica si una fecha/hora está bloqueada"""
        return self.fecha_inicio <= fecha_hora <= self.fecha_fin
    
    def __repr__(self):
        return f'<BloqueNoDisponible {self.fecha_inicio} - {self.fecha_fin}>'


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
    
    # Control de acceso y sesión
    clase_cerrada = db.Column(db.Boolean, default=False)  # Si la clase fue cerrada automáticamente
    fecha_cierre = db.Column(db.DateTime)  # Fecha de cierre de la clase
    acceso_unico = db.Column(db.Boolean, default=True)  # Si solo se permite una conexión por persona
    conexiones_estudiante = db.Column(db.Integer, default=0)  # Número de veces que el estudiante se conectó
    conexiones_docente = db.Column(db.Integer, default=0)  # Número de veces que el docente se conectó
    primera_conexion_estudiante = db.Column(db.DateTime)  # Primera conexión del estudiante
    primera_conexion_docente = db.Column(db.DateTime)  # Primera conexión del docente
    
    # Clases especiales
    es_gratuita = db.Column(db.Boolean, default=False)  # Si es una clase sin costo (cortesía del admin)
    creada_por_admin = db.Column(db.Boolean, default=False)  # Si fue creada directamente por administrador
    notas_admin = db.Column(db.Text)  # Notas del administrador sobre la clase
    
    # Seguridad de enlaces
    regenerar_link = db.Column(db.Boolean, default=True)  # Si se debe regenerar el link en cada acceso
    link_jitsi_usado = db.Column(db.Boolean, default=False)  # Si el link actual ya fue usado
    
    # Relaciones
    pago = db.relationship('Pago', backref='clase', uselist=False)
    resena = db.relationship('Resena', backref='clase', uselist=False)
    materiales = db.relationship('Material', backref='clase', lazy='dynamic')
    asistencias = db.relationship('Asistencia', backref='clase', lazy='dynamic')
    
    def puede_acceder(self, usuario_id, es_docente=False):
        """Verifica si un usuario puede acceder a la clase"""
        # Si la clase está cerrada, no se puede acceder
        if self.clase_cerrada:
            return False, 'La clase ha sido cerrada'
        
        # Verificar si la clase ha pasado su tiempo límite
        ahora = datetime.utcnow()
        if self.fecha_fin and ahora > self.fecha_fin:
            return False, 'La clase ha finalizado'
        
        # Verificar si ya se usó el acceso único
        if self.acceso_unico:
            if es_docente and self.conexiones_docente > 0:
                return False, 'Ya has utilizado tu acceso único a esta clase'
            elif not es_docente and self.conexiones_estudiante > 0:
                return False, 'Ya has utilizado tu acceso único a esta clase'
        
        # Verificar que la clase esté confirmada
        if self.estado not in ['confirmada', 'completada']:
            return False, 'La clase no está confirmada'
        
        return True, 'Acceso permitido'
    
    def generar_nuevo_link_jitsi(self, commit=True):
        """Genera un nuevo enlace de Jitsi Meet para la clase"""
        import uuid
        from flask import current_app
        
        jitsi_server = current_app.config.get('JITSI_SERVER', 'meet.jit.si')
        # Generar ID único con timestamp para evitar colisiones
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = f"{self.id}-{timestamp}-{uuid.uuid4().hex[:8]}"
        self.link_jitsi = f"https://{jitsi_server}/aulavirtual-{unique_id}"
        self.link_jitsi_usado = False
        
        if commit:
            db.session.commit()
        
        return self.link_jitsi
    
    def registrar_acceso(self, usuario_id, es_docente=False, regenerar=None):
        """Registra un acceso del usuario a la clase"""
        ahora = datetime.utcnow()
        
        if es_docente:
            if not self.primera_conexion_docente:
                self.primera_conexion_docente = ahora
            self.conexiones_docente += 1
        else:
            if not self.primera_conexion_estudiante:
                self.primera_conexion_estudiante = ahora
            self.conexiones_estudiante += 1
        
        # Determinar si debe regenerar
        if regenerar is None:
            regenerar = self.regenerar_link
        
        # Regenerar link si está configurado Y ambos ya se conectaron al menos una vez
        if regenerar and self.conexiones_docente > 0 and self.conexiones_estudiante > 0:
            # El link actual fue usado, generar uno nuevo
            self.generar_nuevo_link_jitsi(commit=False)
        else:
            # Solo marcar el link actual como usado
            self.link_jitsi_usado = True
        
        db.session.commit()
    
    def cerrar_automaticamente(self):
        """Cierra automáticamente la clase después del tiempo establecido"""
        if not self.clase_cerrada and self.fecha_fin and datetime.utcnow() > self.fecha_fin:
            self.clase_cerrada = True
            self.fecha_cierre = datetime.utcnow()
            if self.estado == 'confirmada':
                self.estado = 'completada'
            db.session.commit()
            return True
        return False
    
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
    
    # Relación many-to-many con estudiantes
    estudiantes_compartidos = db.relationship('Usuario', 
                                             secondary=material_estudiante,
                                             backref=db.backref('materiales_compartidos', lazy='dynamic'))
    
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


class Retiro(db.Model):
    """Modelo de Retiro - Solicitudes de pago a docentes"""
    
    __tablename__ = 'retiros'
    
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(20))  # paypal, stripe, banco, manual
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, aprobado, rechazado, pagado
    
    # Datos del método de pago (copia al momento de la solicitud)
    datos_pago = db.Column(db.Text)  # JSON con detalles del método de pago
    
    # Notas y seguimiento
    notas_docente = db.Column(db.Text)  # Notas del docente al solicitar
    notas_admin = db.Column(db.Text)  # Notas del admin
    
    # Comprobante
    comprobante_url = db.Column(db.String(500))  # URL del comprobante de pago
    transaction_id = db.Column(db.String(200))  # ID de transacción (PayPal, Stripe, etc.)
    
    # Fechas
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_aprobacion = db.Column(db.DateTime)
    fecha_pago = db.Column(db.DateTime)
    
    # Usuario que aprobó/procesó
    aprobado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    aprobado_por = db.relationship('Usuario', foreign_keys=[aprobado_por_id], backref='retiros_aprobados')
    
    def __repr__(self):
        return f'<Retiro {self.id} - ${self.monto} - {self.estado}>'
