#!/usr/bin/env python3
"""
Aula Virtual - Punto de Entrada de la Aplicación
Inicializa y ejecuta la aplicación Flask
"""

import os
from app import create_app, db
from app.models import Usuario, Docente, Clase, Pago, Resena, Material, Calificacion

# Crear la aplicación
app = create_app()

# Contexto de shell para Flask CLI
@app.shell_context_processor
def make_shell_context():
    """Hace disponibles las variables en el shell de Flask"""
    return {
        'db': db,
        'Usuario': Usuario,
        'Docente': Docente,
        'Clase': Clase,
        'Pago': Pago,
        'Resena': Resena,
        'Material': Material,
        'Calificacion': Calificacion
    }

# Comando CLI para crear usuario administrador
@app.cli.command()
def create_admin():
    """Crea un usuario administrador"""
    from getpass import getpass
    
    print("=== Crear Usuario Administrador ===")
    nombre = input("Nombre completo: ")
    email = input("Email: ")
    password = getpass("Contraseña: ")
    password_confirm = getpass("Confirmar contraseña: ")
    
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden")
        return
    
    # Verificar si el usuario ya existe
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        print(f"❌ Ya existe un usuario con el email {email}")
        return
    
    # Crear usuario administrador
    admin = Usuario(nombre=nombre, email=email, rol='admin')
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"✅ Usuario administrador creado exitosamente: {email}")

# Comando CLI para inicializar la base de datos
@app.cli.command()
def init_db():
    """Inicializa la base de datos con datos de ejemplo"""
    print("=== Inicializando Base de Datos ===")
    
    # Crear tablas
    db.create_all()
    print("✅ Tablas creadas")
    
    # Crear usuario administrador por defecto
    admin_email = "admin@aulavirtual.com"
    if not Usuario.query.filter_by(email=admin_email).first():
        admin = Usuario(
            nombre="Administrador",
            email=admin_email,
            rol='admin'
        )
        admin.set_password("Admin123!")
        db.session.add(admin)
        print(f"✅ Usuario admin creado: {admin_email} / Admin123!")
    
    # Crear docente de ejemplo
    docente_email = "docente@aulavirtual.com"
    if not Usuario.query.filter_by(email=docente_email).first():
        user_docente = Usuario(
            nombre="Profesor Juan Pérez",
            email=docente_email,
            rol='docente'
        )
        user_docente.set_password("Docente123!")
        db.session.add(user_docente)
        db.session.flush()
        
        docente = Docente(
            usuario_id=user_docente.id,
            especialidad="Matemáticas y Física",
            descripcion="Profesor con 10 años de experiencia en educación secundaria y universitaria",
            precio_hora=25.00
        )
        db.session.add(docente)
        print(f"✅ Usuario docente creado: {docente_email} / Docente123!")
    
    # Crear cliente de ejemplo
    cliente_email = "estudiante@aulavirtual.com"
    if not Usuario.query.filter_by(email=cliente_email).first():
        cliente = Usuario(
            nombre="María González",
            email=cliente_email,
            rol='cliente'
        )
        cliente.set_password("Cliente123!")
        db.session.add(cliente)
        print(f"✅ Usuario cliente creado: {cliente_email} / Cliente123!")
    
    db.session.commit()
    print("\n✅ Base de datos inicializada correctamente")
    print("\n=== Credenciales de Acceso ===")
    print("Admin: admin@aulavirtual.com / Admin123!")
    print("Docente: docente@aulavirtual.com / Docente123!")
    print("Cliente: estudiante@aulavirtual.com / Cliente123!")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 50)
    print("🎓 Aula Virtual - Sistema de Gestión Educativa")
    print("=" * 50)
    print(f"🌐 Servidor: http://0.0.0.0:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🗄️  Base de datos: {app.config.get('SQLALCHEMY_DATABASE_URI', '').split('@')[-1] if '@' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'SQLite'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
