#!/usr/bin/env python3
"""
Script de configuración inicial para Admin Skypass
"""

import os
import sys
import getpass
from app import app, db, Admin
from werkzeug.security import generate_password_hash

def configurar_admin():
    """Configurar usuario administrador"""
    print("🔐 Configuración del usuario administrador")
    print("-" * 40)
    
    # Verificar si ya existe un admin
    with app.app_context():
        admin_existente = Admin.query.first()
        if admin_existente:
            print(f"✅ Usuario administrador ya existe: {admin_existente.username}")
            cambiar = input("¿Deseas cambiar la contraseña? (s/n): ").lower().strip()
            if cambiar != 's':
                return
    
    # Solicitar datos del administrador
    print("\nIngresa los datos del administrador:")
    username = input("Usuario: ").strip()
    if not username:
        username = "admin"
        print(f"Usando usuario por defecto: {username}")
    
    while True:
        password = getpass.getpass("Contraseña: ")
        if len(password) < 6:
            print("❌ La contraseña debe tener al menos 6 caracteres")
            continue
        
        confirm_password = getpass.getpass("Confirmar contraseña: ")
        if password != confirm_password:
            print("❌ Las contraseñas no coinciden")
            continue
        
        break
    
    # Crear o actualizar administrador
    with app.app_context():
        if admin_existente:
            admin_existente.username = username
            admin_existente.password_hash = generate_password_hash(password)
            db.session.commit()
            print(f"✅ Usuario administrador actualizado: {username}")
        else:
            admin = Admin(
                username=username,
                password_hash=generate_password_hash(password)
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Usuario administrador creado: {username}")

def configurar_email():
    """Configurar credenciales de email"""
    print("\n📧 Configuración de email para alertas")
    print("-" * 40)
    
    print("Para configurar las alertas por email, necesitas:")
    print("1. Una cuenta de Gmail")
    print("2. Activar verificación en 2 pasos")
    print("3. Generar una App Password")
    print("\n¿Deseas configurar el email ahora? (s/n): ", end="")
    
    if input().lower().strip() != 's':
        print("⚠️  Puedes configurar el email más tarde editando app.py")
        return
    
    email = input("Email de Gmail: ").strip()
    if not email or '@gmail.com' not in email:
        print("❌ Debe ser una cuenta de Gmail válida")
        return
    
    print("\nPara obtener la App Password:")
    print("1. Ve a https://myaccount.google.com/security")
    print("2. Busca 'Contraseñas de aplicaciones'")
    print("3. Genera una nueva para 'Admin Skypass'")
    print("4. Copia la contraseña de 16 caracteres")
    
    app_password = getpass.getpass("App Password (16 caracteres): ").strip()
    if len(app_password) != 16:
        print("❌ La App Password debe tener 16 caracteres")
        return
    
    # Actualizar configuración
    print(f"\n✅ Email configurado: {email}")
    print("⚠️  Recuerda actualizar las variables GMAIL_USER y GMAIL_PASSWORD en app.py")

def verificar_dependencias():
    """Verificar que todas las dependencias estén instaladas"""
    print("📦 Verificando dependencias...")
    
    dependencias = [
        'flask',
        'flask_sqlalchemy', 
        'werkzeug',
        'requests'
    ]
    
    faltantes = []
    for dep in dependencias:
        try:
            __import__(dep)
        except ImportError:
            faltantes.append(dep)
    
    if faltantes:
        print(f"❌ Faltan dependencias: {', '.join(faltantes)}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def main():
    """Función principal de configuración"""
    print("🌐 Admin Skypass - Configuración Inicial")
    print("=" * 50)
    
    # Verificar dependencias
    if not verificar_dependencias():
        sys.exit(1)
    
    # Crear base de datos
    print("\n🗄️  Inicializando base de datos...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ Base de datos creada correctamente")
        except Exception as e:
            print(f"❌ Error al crear base de datos: {e}")
            sys.exit(1)
    
    # Configurar administrador
    configurar_admin()
    
    # Configurar email
    configurar_email()
    
    # Mostrar resumen
    print("\n🎉 Configuración completada!")
    print("=" * 50)
    print("Para iniciar la aplicación:")
    print("  python run.py")
    print("\nO directamente:")
    print("  python app.py")
    print("\nLa aplicación estará disponible en: http://localhost:5000")

if __name__ == '__main__':
    main()
