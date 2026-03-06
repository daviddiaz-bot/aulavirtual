"""
Script de Migración - Seguridad de Enlaces Jitsi
Añade campos para controlar regeneración de enlaces y prevenir reutilización

Ejecutar: python migrar_seguridad_jitsi.py --auto
"""

from app import create_app, db

def migrar_base_datos():
    """Ejecutar migración de base de datos"""
    app = create_app()
    
    with app.app_context():
        print("Iniciando migración de seguridad de enlaces Jitsi...")
        
        try:
            # Agregar columnas nuevas a tabla 'clases' si no existen
            print("\nVerificando y agregando columnas necesarias...")
            
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            # Verificar columnas existentes
            columnas_clase = [col['name'] for col in inspector.get_columns('clases')]
            
            nuevas_columnas = {
                'regenerar_link': 'BOOLEAN DEFAULT 1',
                'link_jitsi_usado': 'BOOLEAN DEFAULT 0'
            }
            
            # Agregar columnas faltantes
            for columna, tipo in nuevas_columnas.items():
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
            
            # Actualizar clases existentes con valores por defecto
            print("\nActualizando clases existentes...")
            try:
                with db.engine.connect() as conn:
                    # Establecer regenerar_link = True para todas las clases existentes
                    conn.execute(text("UPDATE clases SET regenerar_link = 1 WHERE regenerar_link IS NULL"))
                    # Establecer link_jitsi_usado = False para clases que aún no han empezado
                    conn.execute(text("UPDATE clases SET link_jitsi_usado = 0 WHERE link_jitsi_usado IS NULL"))
                    conn.commit()
                print("  ✓ Clases existentes actualizadas")
            except Exception as e:
                print(f"  ✗ Error actualizando clases: {e}")
            
            print("\n" + "="*60)
            print("MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("="*60)
            print("\nResumen de cambios:")
            print("  • regenerar_link: Control de regeneración de enlaces")
            print("  • link_jitsi_usado: Marca si el enlace actual fue usado")
            print("\nFuncionalidad:")
            print("  ✓ Los enlaces se regeneran después del primer acceso de ambos")
            print("  ✓ Previene reutilización de enlaces guardados")
            print("  ✓ Mantiene seguridad de las sesiones")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error durante la migración: {e}")
            db.session.rollback()
            return False


if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("MIGRACIÓN - SEGURIDAD DE ENLACES JITSI")
    print("=" * 60)
    print("\nEsta migración agrega:")
    print("  • Campo 'regenerar_link' - Controla si se regenera el enlace")
    print("  • Campo 'link_jitsi_usado' - Marca enlaces usados")
    print("\n¡IMPORTANTE! Esto mejora la seguridad evitando que se")
    print("reutilicen enlaces de Jitsi después del primer acceso.")
    print("=" * 60)
    
    # Auto-confirmar si se pasa --auto como argumento
    if '--auto' in sys.argv or '-y' in sys.argv:
        confirmacion = 'si'
        print("\nModo automático activado. Ejecutando migración...")
    else:
        confirmacion = input("\n¿Deseas continuar con la migración? (si/no): ")
    
    if confirmacion.lower() in ['si', 's', 'yes', 'y']:
        exito = migrar_base_datos()
        
        if not exito:
            print("\n" + "=" * 60)
            print("✗ LA MIGRACIÓN FALLÓ")
            print("=" * 60)
            sys.exit(1)
    else:
        print("\nMigración cancelada por el usuario.")
        sys.exit(0)
