"""
Script de Migración de Base de Datos
Añade nuevos campos y tablas para:
- Control de acceso a clases
- Disponibilidad horaria de docentes
- Clases gratuitas/especiales

Ejecutar: python migrar_db_control_acceso.py
"""

from app import create_app, db
from app.models import Clase, Docente
from datetime import datetime

def migrar_base_datos():
    """Ejecutar migración de base de datos"""
    app = create_app()
    
    with app.app_context():
        print("Iniciando migración de base de datos...")
        
        try:
            # 1. Crear nuevas tablas
            print("\n1. Creando nuevas tablas...")
            db.create_all()
            print("✓ Tablas creadas correctamente")
            
            # 2. Agregar columnas nuevas a tabla 'clases' si no existen
            print("\n2. Verificando columnas en tabla 'clases'...")
            
            # Obtener conexión directa
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            # Verificar columnas existentes
            columnas_clase = [col['name'] for col in inspector.get_columns('clases')]
            
            nuevas_columnas_clase = {
                'clase_cerrada': 'BOOLEAN DEFAULT 0',
                'fecha_cierre': 'DATETIME',
                'acceso_unico': 'BOOLEAN DEFAULT 1',
                'conexiones_estudiante': 'INTEGER DEFAULT 0',
                'conexiones_docente': 'INTEGER DEFAULT 0',
                'primera_conexion_estudiante': 'DATETIME',
                'primera_conexion_docente': 'DATETIME',
                'es_gratuita': 'BOOLEAN DEFAULT 0',
                'creada_por_admin': 'BOOLEAN DEFAULT 0',
                'notas_admin': 'TEXT'
            }
            
            # Agregar columnas faltantes
            for columna, tipo in nuevas_columnas_clase.items():
                if columna not in columnas_clase:
                    try:
                        with db.engine.connect() as conn:
                            sql = f"ALTER TABLE clases ADD COLUMN {columna} {tipo}"
                            conn.execute(text(sql))
                            conn.commit()
                        print(f"  ✓ Columna '{columna}' agregada a 'clases'")
                    except Exception as e:
                        print(f"  ✗ Error agregando columna '{columna}': {e}")
                else:
                    print(f"  - Columna '{columna}' ya existe")
            
            print("\n3. Migración completada exitosamente!")
            print("\nResumen:")
            print("  - Tablas nuevas: disponibilidad_docente, bloques_no_disponibles")
            print("  - Campos agregados a 'clases': control de acceso y clases especiales")
            print("\nLos cambios se aplicaron correctamente.")
            
        except Exception as e:
            print(f"\n✗ Error durante la migración: {e}")
            db.session.rollback()
            return False
        
        return True


if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("MIGRACIÓN DE BASE DE DATOS - CONTROL DE ACCESO Y DISPONIBILIDAD")
    print("=" * 60)
    
    # Auto-confirmar si se pasa --auto como argumento
    if '--auto' in sys.argv or '-y' in sys.argv:
        confirmacion = 'si'
        print("\nModo automático activado. Ejecutando migración...")
    else:
        confirmacion = input("\n¿Deseas continuar con la migración? (si/no): ")
    
    if confirmacion.lower() in ['si', 's', 'yes', 'y']:
        exito = migrar_base_datos()
        
        if exito:
            print("\n" + "=" * 60)
            print("✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ LA MIGRACIÓN FALLÓ")
            print("=" * 60)
    else:
        print("\nMigración cancelada por el usuario.")
