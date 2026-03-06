"""
Script para Verificar y Corregir Enlaces de Jitsi en Clases Existentes
Regenera enlaces para clases activas y marca como usados los que corresponda
"""

from app import create_app, db
from app.models import Clase
from datetime import datetime

def verificar_y_corregir_enlaces():
    """Verifica y corrige enlaces de clases existentes"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("VERIFICACIÓN Y CORRECCIÓN DE ENLACES JITSI")
        print("=" * 70)
        
        # Obtener todas las clases activas (no completadas ni canceladas)
        clases_activas = Clase.query.filter(
            Clase.estado.in_(['pendiente', 'confirmada']),
            Clase.fecha_fin >= datetime.utcnow()
        ).all()
        
        print(f"\nClases activas encontradas: {len(clases_activas)}")
        
        if not clases_activas:
            print("No hay clases activas para procesar.")
            return
        
        print("\nProcesando clases...")
        actualizadas = 0
        
        for clase in clases_activas:
            try:
                # Regenerar link para clases confirmadas
                if clase.estado == 'confirmada':
                    if not clase.link_jitsi or 'clase-' in clase.link_jitsi:
                        # Link antiguo o sin formato seguro, regenerar
                        clase.generar_nuevo_link_jitsi(commit=False)
                        actualizadas += 1
                        print(f"  ✓ Clase {clase.id}: Link regenerado")
                    else:
                        print(f"  - Clase {clase.id}: Link OK")
                else:
                    print(f"  - Clase {clase.id}: Pendiente de pago, no requiere acción")
                    
            except Exception as e:
                print(f"  ✗ Error en clase {clase.id}: {e}")
        
        if actualizadas > 0:
            db.session.commit()
            print(f"\n✓ {actualizadas} clases actualizadas correctamente")
        else:
            print(f"\nNo se requirieron actualizaciones")
        
        print("\n" + "=" * 70)
        print("PROCESO COMPLETADO")
        print("=" * 70)


if __name__ == '__main__':
    import sys
    
    print("\nEste script regenerará los enlaces de Jitsi para clases activas")
    print("con formato antiguo o inseguro.\n")
    
    if '--auto' in sys.argv or '-y' in sys.argv:
        confirmacion = 'si'
        print("Modo automático activado. Ejecutando...")
    else:
        confirmacion = input("¿Deseas continuar? (si/no): ")
    
    if confirmacion.lower() in ['si', 's', 'yes', 'y']:
        verificar_y_corregir_enlaces()
    else:
        print("\nOperación cancelada.")
