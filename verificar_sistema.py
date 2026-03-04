#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificación del sistema Aula Virtual
Verifica que todos los componentes estén correctamente configurados
"""
import sys
import os
from app import create_app, db
from app.models import Usuario, Docente, Clase
from sqlalchemy import text

def verificar_sistema():
    """Ejecuta todas las verificaciones del sistema"""
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DEL SISTEMA AULA VIRTUAL")
    print("="*60 + "\n")
    
    errores = []
    warnings = []
    
    # 1. Verificar aplicación Flask
    print("1️⃣  Verificando aplicación Flask...")
    try:
        app = create_app()
        print("   ✅ Aplicación Flask inicializada correctamente")
    except Exception as e:
        print(f"   ❌ Error al inicializar Flask: {str(e)}")
        errores.append("Flask initialization failed")
        return False
    
    with app.app_context():
        # 2. Verificar conexión a base de datos
        print("\n2️⃣  Verificando conexión a PostgreSQL...")
        try:
            db.session.execute(text('SELECT 1'))
            print("   ✅ Conexión a PostgreSQL exitosa")
        except Exception as e:
            print(f"   ❌ Error de conexión a BD: {str(e)}")
            errores.append("Database connection failed")
        
        # 3. Verificar tablas
        print("\n3️⃣  Verificando tablas de la base de datos...")
        tablas_esperadas = ['usuario', 'docente', 'clase', 'pago', 'resena', 'material']
        try:
            inspector = db.inspect(db.engine)
            tablas_existentes = inspector.get_table_names()
            
            for tabla in tablas_esperadas:
                if tabla in tablas_existentes:
                    print(f"   ✅ Tabla '{tabla}' existe")
                else:
                    print(f"   ❌ Tabla '{tabla}' NO existe")
                    errores.append(f"Missing table: {tabla}")
        except Exception as e:
            print(f"   ❌ Error al verificar tablas: {str(e)}")
            errores.append("Table verification failed")
        
        # 4. Verificar usuarios
        print("\n4️⃣  Verificando usuarios en el sistema...")
        try:
            total_usuarios = Usuario.query.count()
            admins = Usuario.query.filter_by(rol='admin').count()
            docentes = Usuario.query.filter_by(rol='docente').count()
            estudiantes = Usuario.query.filter_by(rol='estudiante').count()
            
            print(f"   📊 Total de usuarios: {total_usuarios}")
            print(f"   👑 Administradores: {admins}")
            print(f"   👨‍🏫 Docentes: {docentes}")
            print(f"   👨‍🎓 Estudiantes: {estudiantes}")
            
            if admins == 0:
                print("   ⚠️  No hay administradores creados")
                warnings.append("No admin users found")
        except Exception as e:
            print(f"   ❌ Error al verificar usuarios: {str(e)}")
            errores.append("User verification failed")
        
        # 5. Verificar variables de entorno críticas
        print("\n5️⃣  Verificando variables de entorno...")
        env_vars = {
            'SECRET_KEY': os.getenv('SECRET_KEY'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY'),
            'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
            'REDIS_URL': os.getenv('REDIS_URL')
        }
        
        for var, valor in env_vars.items():
            if valor:
                # Ocultar valores sensibles
                valor_mostrar = valor[:10] + "..." if len(valor) > 10 else "***"
                print(f"   ✅ {var}: {valor_mostrar}")
            else:
                print(f"   ⚠️  {var}: NO CONFIGURADO")
                warnings.append(f"Environment variable {var} not set")
        
        # 6. Verificar Redis
        print("\n6️⃣  Verificando conexión a Redis...")
        try:
            from redis import Redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = Redis.from_url(redis_url)
            redis_client.ping()
            print("   ✅ Conexión a Redis exitosa")
        except Exception as e:
            print(f"   ⚠️  Redis no disponible: {str(e)}")
            warnings.append("Redis connection failed (non-critical)")
        
        # 7. Verificar estructura de directorios
        print("\n7️⃣  Verificando estructura de carpetas...")
        directorios = [
            'app/templates',
            'app/static/css',
            'app/static/js',
            'app/static/uploads'
        ]
        
        for directorio in directorios:
            if os.path.exists(directorio):
                print(f"   ✅ {directorio}")
            else:
                print(f"   ❌ {directorio} NO EXISTE")
                errores.append(f"Missing directory: {directorio}")
    
    # Resumen final
    print("\n" + "="*60)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    if not errores and not warnings:
        print("\n✅✅✅ TODOS LOS CHECKS PASARON EXITOSAMENTE ✅✅✅")
        print("\n🚀 El sistema está listo para usar!")
        return True
    else:
        if errores:
            print(f"\n❌ ERRORES CRÍTICOS ({len(errores)}):")
            for error in errores:
                print(f"   - {error}")
        
        if warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
            for warning in warnings:
                print(f"   - {warning}")
        
        if errores:
            print("\n❌ El sistema tiene errores críticos. Por favor corrígelos antes de continuar.")
            return False
        else:
            print("\n⚠️  El sistema tiene algunas advertencias pero debería funcionar.")
            print("   Se recomienda revisar las advertencias cuando sea posible.")
            return True

if __name__ == '__main__':
    success = verificar_sistema()
    print("\n" + "="*60 + "\n")
    sys.exit(0 if success else 1)
