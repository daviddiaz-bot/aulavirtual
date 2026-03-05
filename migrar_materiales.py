"""
Script de migración para agregar tabla material_estudiante
Ejecutar este script para crear la tabla de relación entre materiales y estudiantes
"""

from app import create_app, db

def migrar_materiales():
    """Crear tabla de relación material_estudiante si no existe"""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Importar modelos para que SQLAlchemy los reconozca
            from app.models import Material, Usuario
            
            # Crear todas las tablas (incluyendo material_estudiante)
            db.create_all()
            
            print("✓ Tabla 'material_estudiante' verificada/creada correctamente")
            print("✓ Todas las tablas del sistema están actualizadas")
            print("✓ Migración completada")
            
        except Exception as e:
            print(f"✗ Error durante la migración: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRACIÓN: Sistema de Materiales PDF")
    print("=" * 60)
    print()
    
    migrar_materiales()
    
    print()
    print("=" * 60)
    print("Migración finalizada")
    print("=" * 60)
