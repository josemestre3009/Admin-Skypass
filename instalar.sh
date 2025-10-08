#!/bin/bash

# 🚀 SCRIPT DE INSTALACIÓN AUTOMÁTICA - ADMIN-SKYPASS
# Autor: Jose Daniel
# Versión: 1.0
#curl -sSL https://raw.githubusercontent.com/josemestre3009/Admin-Skypass/main/instalar.sh | bash

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
echo "║              Sistema de Monitoreo de ISPs                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar si es root
if [[ $EUID -eq 0 ]]; then
   print_warning "Ejecutando como root. Esto no es recomendado pero se permitirá."
   # No salir, continuar con la instalación
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
if [[ $EUID -eq 0 ]]; then
    apt update > /dev/null 2>&1 && apt upgrade -y > /dev/null 2>&1
else
    sudo apt update > /dev/null 2>&1 && sudo apt upgrade -y > /dev/null 2>&1
fi
print_success "Sistema actualizado"

# Ajustar zona horaria a América/Bogotá
print_status "Ajustando zona horaria a America/Bogota..."
if [[ $EUID -eq 0 ]]; then
    timedatectl set-timezone America/Bogota > /dev/null 2>&1 || true
else
    sudo timedatectl set-timezone America/Bogota > /dev/null 2>&1 || true
fi
print_success "Zona horaria configurada"

# Paso 2: Instalar dependencias del sistema
print_status "Paso 2/10: Instalando dependencias del sistema..."
if [[ $EUID -eq 0 ]]; then
    apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib redis-server htop curl wget git > /dev/null 2>&1
else
    sudo apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib redis-server htop curl wget git > /dev/null 2>&1
fi
print_success "Dependencias instaladas"

# Paso 3: Configurar PostgreSQL
print_status "Paso 3/10: Configurando PostgreSQL..."
if [[ $EUID -eq 0 ]]; then
    systemctl enable postgresql > /dev/null 2>&1
    systemctl start postgresql > /dev/null 2>&1
    # Crear base de datos y usuario
    sudo -u postgres psql -c "CREATE DATABASE admin_skypass;" > /dev/null 2>&1 || true
    sudo -u postgres psql -c "CREATE USER skypass_user WITH PASSWORD 'skypass123';" > /dev/null 2>&1 || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE admin_skypass TO skypass_user;" > /dev/null 2>&1
else
    sudo systemctl enable postgresql > /dev/null 2>&1
    sudo systemctl start postgresql > /dev/null 2>&1
    # Crear base de datos y usuario
    sudo -u postgres psql -c "CREATE DATABASE admin_skypass;" > /dev/null 2>&1 || true
    sudo -u postgres psql -c "CREATE USER skypass_user WITH PASSWORD 'skypass123';" > /dev/null 2>&1 || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE admin_skypass TO skypass_user;" > /dev/null 2>&1
fi
print_success "PostgreSQL configurado"

# Paso 4: Configurar Redis
print_status "Paso 4/10: Configurando Redis..."
if [[ $EUID -eq 0 ]]; then
    systemctl enable redis-server > /dev/null 2>&1
    systemctl start redis-server > /dev/null 2>&1
else
    sudo systemctl enable redis-server > /dev/null 2>&1
    sudo systemctl start redis-server > /dev/null 2>&1
fi
print_success "Redis configurado"

# Paso 5: Crear directorio de la aplicación
print_status "Paso 5/10: Preparando directorio de la aplicación..."
mkdir -p /opt/Admin-Skypass
if [[ $EUID -ne 0 ]]; then
    sudo chown -R $USER:$USER /opt/Admin-Skypass
fi
print_success "Directorio creado"

# Paso 6: Clonar repositorio
print_status "Paso 6/10: Descargando código fuente..."
cd /opt/Admin-Skypass
if [ -d ".git" ]; then
    git pull origin main > /dev/null 2>&1
else
    git clone https://github.com/josemestre3009/Admin-Skypass.git . > /dev/null 2>&1
fi
print_success "Código fuente descargado"

# Paso 7: Crear entorno virtual
print_status "Paso 7/10: Configurando entorno virtual..."
python3 -m venv venv > /dev/null 2>&1
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
pip install gunicorn > /dev/null 2>&1
print_success "Entorno virtual configurado"

# Paso 8: Configurar variables de entorno
print_status "Paso 8/10: Configurando variables de entorno..."
cat > .env << EOF
# Configuración de Admin Skypass
# Copia este archivo como .env y configura tus valores

# Clave secreta para Flask (genera una nueva para producción)
SECRET_KEY=xxxxxxx

# Configuración de base de datos
DATABASE_URL=sqlite:///isps.db

# Configuración de email para alertas
GMAIL_USER=xxxxxxx@gmail.com
GMAIL_PASSWORD=xxxxxxx

# Configuración del servidor (opcional)
HOST=0.0.0.0
PORT=5000
DEBUG=False

# Configuración de monitoreo (opcional)
MONITORING_INTERVAL=600
ALERT_COOLDOWN=86400
EOF
print_success "Variables de entorno configuradas"

# Paso 9: Inicializar base de datos
print_status "Paso 9/10: Inicializando base de datos..."
source venv/bin/activate
python app.py --init-db > /dev/null 2>&1 || true
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
if [[ $EUID -eq 0 ]]; then
    systemctl daemon-reload > /dev/null 2>&1
    systemctl enable admin-skypass > /dev/null 2>&1
    systemctl start admin-skypass > /dev/null 2>&1
else
    sudo systemctl daemon-reload > /dev/null 2>&1
    sudo systemctl enable admin-skypass > /dev/null 2>&1
    sudo systemctl start admin-skypass > /dev/null 2>&1
fi
print_success "Servicio configurado y iniciado"

# Configurar firewall
print_status "Configurando firewall..."
if [[ $EUID -eq 0 ]]; then
    ufw allow 8000/tcp > /dev/null 2>&1
    ufw allow 22/tcp > /dev/null 2>&1
    ufw --force enable > /dev/null 2>&1
else
    sudo ufw allow 8000/tcp > /dev/null 2>&1
    sudo ufw allow 22/tcp > /dev/null 2>&1
    sudo ufw --force enable > /dev/null 2>&1
fi
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
