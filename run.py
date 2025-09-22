#!/usr/bin/env python3
"""
Script de inicio para Admin Skypass
Sistema de Administración de ISPs
"""

import os
import sys
from app import app, db

def main():
    """Función principal para iniciar la aplicación"""
    
    print("🌐 Admin Skypass - Sistema de Administración de ISPs")
    print("=" * 50)
    
    # Verificar dependencias
    try:
        import flask
        import flask_sqlalchemy
        import requests
        print("✅ Dependencias verificadas correctamente")
    except ImportError as e:
        print(f"❌ Error: Falta dependencia - {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        sys.exit(1)
    
    # Crear base de datos si no existe
    with app.app_context():
        try:
            db.create_all()
            print("✅ Base de datos inicializada")
        except Exception as e:
            print(f"❌ Error al inicializar base de datos: {e}")
            sys.exit(1)
    
    # Verificar configuración
    print("\n🔧 Configuración del sistema:")
    print(f"   - Base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"   - Modo debug: {app.config.get('DEBUG', False)}")
    print(f"   - Email configurado: {'Sí' if app.config.get('GMAIL_USER') else 'No'}")
    
    # Mostrar información de acceso
    print("\n🚀 Iniciando servidor...")
    print("   - URL: http://localhost:5000")
    print("   - Usuario: admin")
    print("   - Contraseña: admin123")
    print("\n⚠️  IMPORTANTE: Cambia la contraseña por defecto en producción")
    print("\n📖 Para más información, consulta el README.md")
    print("=" * 50)
    
    # Iniciar aplicación
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
