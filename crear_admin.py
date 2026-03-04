#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear un usuario administrador en Aula Virtual
"""
from app import create_app, db
from app.models import Usuario
import sys

def crear_admin():
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existe un admin
        admin_existe = Usuario.query.filter_by(email='admin@aulavirtual.com').first()
        
        if admin_existe:
            print("❌ Ya existe un usuario con email admin@aulavirtual.com")
            print(f"   Nombre: {admin_existe.nombre}")
            print(f"   Rol: {admin_existe.rol}")
            respuesta = input("\n¿Deseas eliminarlo y crear uno nuevo? (s/n): ")
            
            if respuesta.lower() == 's':
                db.session.delete(admin_existe)
                db.session.commit()
                print("✅ Usuario anterior eliminado")
            else:
                print("⚠️  Operación cancelada")
                return
        
        # Solicitar datos del administrador
        print("\n" + "="*50)
        print("CREAR USUARIO ADMINISTRADOR")
        print("="*50)
        
        nombre = input("Nombre completo [Admin]: ").strip() or "Admin"
        email = input("Email [admin@aulavirtual.com]: ").strip() or "admin@aulavirtual.com"
        password = input("Contraseña [Admin123!]: ").strip() or "Admin123!"
        
        # Crear el usuario
        admin = Usuario(
            nombre=nombre,
            email=email,
            rol='admin'
        )
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            print("\n" + "="*50)
            print("✅ USUARIO ADMINISTRADOR CREADO EXITOSAMENTE")
            print("="*50)
            print(f"Nombre: {nombre}")
            print(f"Email: {email}")
            print(f"Contraseña: {password}")
            print("\n⚠️  IMPORTANTE: Guarda estas credenciales en un lugar seguro")
            print("="*50)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al crear el administrador: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    crear_admin()
