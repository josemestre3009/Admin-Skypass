#!/bin/bash

# 🚀 SCRIPT DE INSTALACIÓN AUTOMÁTICA - ADMIN-SKYPASS
# Autor: Jose Daniel
# Versión: 1.0

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ADMIN-SKYPASS INSTALLER                   ║"
echo "║              Sistema de Monitoreo de ISPs                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar si es root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecutes este script como root. Usa un usuario normal con sudo."
   exit 1
fi

# Verificar sistema operativo
if [[ ! -f /etc/os-release ]]; then
    print_error "Sistema operativo no soportado"
    exit 1
fi

. /etc/os-release
if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
    print_warning "Este script está optimizado para Ubuntu/Debian. Continuando..."
fi

print_status "Iniciando instalación de Admin-Skypass..."

# Paso 1: Actualizar sistema
print_status "Paso 1/10: Actualizando sistema..."
sudo apt update && sudo apt upgrade -y
print_success "Sistema actualizado"

# Paso 2: Instalar dependencias del sistema
print_status "Paso 2/10: Instalando dependencias del sistema..."
sudo apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib redis-server htop curl wget git
print_success "Dependencias instaladas"

# Paso 3: Configurar PostgreSQL
print_status "Paso 3/10: Configurando PostgreSQL..."
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Crear base de datos y usuario
sudo -u postgres psql -c "CREATE DATABASE admin_skypass;" 2>/dev/null || print_warning "Base de datos ya existe"
sudo -u postgres psql -c "CREATE USER skypass_user WITH PASSWORD 'skypass123';" 2>/dev/null || print_warning "Usuario ya existe"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE admin_skypass TO skypass_user;"
print_success "PostgreSQL configurado"

# Paso 4: Configurar Redis
print_status "Paso 4/10: Configurando Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server
print_success "Redis configurado"

# Paso 5: Crear directorio de la aplicación
print_status "Paso 5/10: Preparando directorio de la aplicación..."
sudo mkdir -p /opt/Admin-Skypass
sudo chown -R $USER:$USER /opt/Admin-Skypass
print_success "Directorio creado"

# Paso 6: Clonar repositorio
print_status "Paso 6/10: Descargando código fuente..."
cd /opt/Admin-Skypass
if [ -d ".git" ]; then
    print_warning "Repositorio ya existe, actualizando..."
    git pull origin main
else
    git clone https://github.com/josemestre3009/Admin-Skypass.git .
fi
print_success "Código fuente descargado"

# Paso 7: Crear entorno virtual
print_status "Paso 7/10: Configurando entorno virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
print_success "Entorno virtual configurado"

# Paso 8: Configurar variables de entorno
print_status "Paso 8/10: Configurando variables de entorno..."
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=postgresql://skypass_user:skypass123@localhost/admin_skypass
REDIS_URL=redis://localhost:6379/0

# Configuración de Email (CONFIGURAR MANUALMENTE)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_app_password
MAIL_DEFAULT_SENDER=tu_email@gmail.com

# Configuración de la aplicación
HOST=0.0.0.0
PORT=8000
DEBUG=False
EOF
print_success "Variables de entorno configuradas"

# Paso 9: Inicializar base de datos
print_status "Paso 9/10: Inicializando base de datos..."
source venv/bin/activate
python app.py --init-db 2>/dev/null || print_warning "Base de datos ya inicializada"
print_success "Base de datos inicializada"

# Paso 10: Crear servicio systemd
print_status "Paso 10/10: Configurando servicio del sistema..."
sudo tee /etc/systemd/system/admin-skypass.service > /dev/null << EOF
[Unit]
Description=Admin-Skypass Web Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/Admin-Skypass
Environment=PATH=/opt/Admin-Skypass/venv/bin
ExecStart=/opt/Admin-Skypass/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable admin-skypass
sudo systemctl start admin-skypass
print_success "Servicio configurado y iniciado"

# Configurar firewall
print_status "Configurando firewall..."
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
print_success "Firewall configurado"

# Obtener IP del servidor
SERVER_IP=$(hostname -I | awk '{print $1}')

# Mostrar información final
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    INSTALACIÓN COMPLETADA                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_success "Admin-Skypass instalado correctamente!"
echo ""
echo -e "${YELLOW}📋 INFORMACIÓN IMPORTANTE:${NC}"
echo -e "   🌐 URL de acceso: ${BLUE}http://$SERVER_IP:8000${NC}"
echo -e "   👤 Usuario por defecto: ${BLUE}admin${NC}"
echo -e "   🔑 Contraseña por defecto: ${BLUE}admin123${NC}"
echo ""
echo -e "${YELLOW}⚙️  CONFIGURACIÓN PENDIENTE:${NC}"
echo -e "   1. Editar archivo .env para configurar email:"
echo -e "      ${BLUE}sudo nano /opt/Admin-Skypass/.env${NC}"
echo -e "   2. Cambiar contraseña por defecto en la aplicación"
echo -e "   3. Agregar tus ISPs desde el dashboard"
echo ""
echo -e "${YELLOW}🔧 COMANDOS ÚTILES:${NC}"
echo -e "   Ver estado: ${BLUE}sudo systemctl status admin-skypass${NC}"
echo -e "   Reiniciar:  ${BLUE}sudo systemctl restart admin-skypass${NC}"
echo -e "   Ver logs:   ${BLUE}sudo journalctl -u admin-skypass -f${NC}"
echo ""
echo -e "${GREEN}¡Disfruta usando Admin-Skypass! 🚀${NC}"
