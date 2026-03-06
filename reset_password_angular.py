#!/usr/bin/env python
"""Script para restablecer contraseña de angelapsuarezm@gmail.com"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Importar dentro del contexto
if __name__ == '__main__':
    from app import create_app, db
    from app.models import Usuario
    
    app = create_app()
    
    with app.app_context():
        usuario = Usuario.query.filter_by(email='angelapsuarezm@gmail.com').first()
        
        if not usuario:
            print("Usuario no encontrado")
            sys.exit(1)
        
        # Nueva contraseña simple
        new_password = "Admin123456"
        usuario.set_password(new_password)
        usuario.activo = True
        
        db.session.commit()
        
        print(f"✓ Contraseña restablecida correctamente")
        print(f"Email: angelapsuarezm@gmail.com")
        print(f"Nueva contraseña: {new_password}")
        print(f"Usuario activo: {usuario.activo}")
