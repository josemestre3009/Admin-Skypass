# 🌐 Admin Skypass - Sistema de Administración de ISPs

Sistema web simple para administrar ISPs con monitoreo automático de dispositivos y alertas por email.

## ✨ Características

- **🔐 Login simple** - Autenticación básica para administradores
- **📊 Dashboard** - Resumen general con estadísticas en tiempo real
- **📋 Gestión de ISPs** - CRUD completo para administrar ISPs
- **🔍 Monitoreo automático** - Verificación cada 10 minutos via GenieACS API
- **📧 Alertas por email** - Notificaciones cuando se supere el límite de clientes
- **🎨 Interfaz moderna** - Bootstrap 5 con diseño responsivo

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd Admin-Skypass
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (opcional)
```bash
# Windows
set SECRET_KEY=tu-clave-secreta-muy-segura
set GMAIL_USER=tu-email@gmail.com
set GMAIL_PASSWORD=tu-app-password

# Linux/Mac
export SECRET_KEY=tu-clave-secreta-muy-segura
export GMAIL_USER=tu-email@gmail.com
export GMAIL_PASSWORD=tu-app-password
```

### 4. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## 🔧 Configuración

### Usuario por defecto
- **Usuario:** `admin`
- **Contraseña:** `admin123`

⚠️ **Importante:** Cambia la contraseña por defecto en producción.

### Configuración de Gmail

1. **Activar verificación en 2 pasos** en tu cuenta de Gmail
2. **Generar App Password:**
   - Ve a Configuración de Google → Seguridad
   - Busca "Contraseñas de aplicaciones"
   - Genera una nueva contraseña para "Admin Skypass"
3. **Actualizar configuración:**
   - Edita `app.py` y cambia las variables `GMAIL_USER` y `GMAIL_PASSWORD`
   - O usa variables de entorno

### Configuración de GenieACS

Cada ISP debe tener su propia instancia de GenieACS configurada:

1. **Instalar GenieACS** en la máquina virtual del ISP
2. **Configurar puerto 7557** (puerto por defecto)
3. **Verificar acceso HTTP** desde el servidor de Admin Skypass
4. **URL de ejemplo:** `http://192.168.1.100:7557`

## 📊 Uso del Sistema

### 1. Dashboard
- **Estadísticas generales:** Total de ISPs, dispositivos, alertas
- **ISPs cerca del límite:** ISPs que han alcanzado el 80% de su capacidad
- **ISPs sobrepasados:** ISPs que han superado su límite
- **Últimas alertas:** Historial de notificaciones enviadas

### 2. Gestión de ISPs
- **Agregar ISP:** Formulario con validación de datos
- **Lista de ISPs:** Tabla con estado en tiempo real
- **Verificar dispositivos:** Botón para verificación manual
- **Editar/Eliminar:** Gestión completa de ISPs

### 3. Monitoreo Automático
- **Verificación cada 10 minutos** de todos los ISPs
- **Conteo de dispositivos** via API de GenieACS
- **Alertas automáticas** cuando se supere el límite
- **Cooldown de 24 horas** para evitar spam de emails

## 🗄️ Base de Datos

### Estructura de tablas

```sql
-- Tabla de ISPs
CREATE TABLE isps (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    ip_vm TEXT NOT NULL,
    genieacs_url TEXT NOT NULL,
    limite_clientes INTEGER NOT NULL,
    email_alerta TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dispositivos_actuales INTEGER DEFAULT 0,
    ultima_verificacion TIMESTAMP,
    ultima_alerta TIMESTAMP
);

-- Tabla de administradores
CREATE TABLE admin (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Tabla de alertas
CREATE TABLE alerta (
    id INTEGER PRIMARY KEY,
    isp_id INTEGER NOT NULL,
    mensaje TEXT NOT NULL,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enviada BOOLEAN DEFAULT FALSE
);
```

## 🔌 API de GenieACS

El sistema utiliza la API REST de GenieACS para obtener información de dispositivos:

- **Endpoint:** `GET /devices`
- **Respuesta:** Array de dispositivos JSON
- **Conteo:** Número total de dispositivos registrados

### Ejemplo de respuesta GenieACS:
```json
[
  {
    "_id": "device1",
    "_lastInform": "2024-01-01T10:00:00Z",
    "InternetGatewayDevice.DeviceInfo.SerialNumber": "ABC123"
  },
  {
    "_id": "device2", 
    "_lastInform": "2024-01-01T10:05:00Z",
    "InternetGatewayDevice.DeviceInfo.SerialNumber": "DEF456"
  }
]
```

## 📧 Sistema de Alertas

### Configuración de alertas
- **Trigger:** `dispositivos_actuales > limite_clientes`
- **Frecuencia:** Máximo una vez por día por ISP
- **Formato:** Email HTML con información detallada
- **SMTP:** Gmail con App Password

### Contenido del email de alerta
```html
🚨 Alerta de Límite de Clientes

ISP: MiISP Colombia
IP de VM: 192.168.1.100
URL GenieACS: http://192.168.1.100:7557
Dispositivos actuales: 1050
Límite establecido: 1000
Fecha: 2024-01-01 10:30:00

⚠️ El ISP ha superado su límite de clientes configurado.
```

## 🛠️ Desarrollo

### Estructura del proyecto
```
Admin-Skypass/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuración del sistema
├── requirements.txt      # Dependencias Python
├── README.md            # Documentación
├── isps.db             # Base de datos SQLite (generada automáticamente)
└── templates/          # Templates HTML
    ├── base.html       # Template base
    ├── login.html      # Página de login
    ├── dashboard.html  # Dashboard principal
    ├── lista_isps.html # Lista de ISPs
    ├── agregar_isp.html # Formulario agregar ISP
    └── configuracion.html # Página de configuración
```

### Variables de entorno
```bash
SECRET_KEY=clave-secreta-para-flask
GMAIL_USER=email-para-alertas@gmail.com
GMAIL_PASSWORD=app-password-de-gmail
DATABASE_URL=sqlite:///isps.db
```

### Comandos útiles
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
python app.py

# Crear backup de base de datos
cp isps.db backup_$(date +%Y%m%d).db

# Ver logs de la aplicación
tail -f app.log
```

## 🔒 Seguridad

### Recomendaciones para producción
1. **Cambiar contraseña por defecto** del administrador
2. **Usar variables de entorno** para credenciales sensibles
3. **Configurar HTTPS** con certificado SSL
4. **Hacer backups regulares** de la base de datos
5. **Monitorear logs** de la aplicación
6. **Restringir acceso** por IP si es necesario

### Configuración de firewall
```bash
# Permitir solo puerto 5000 desde IPs específicas
ufw allow from 192.168.1.0/24 to any port 5000
ufw deny 5000
```

## 🐛 Solución de problemas

### Error de conexión a GenieACS
- Verificar que GenieACS esté ejecutándose
- Comprobar conectividad de red
- Validar URL y puerto
- Revisar logs de GenieACS

### Error de envío de emails
- Verificar credenciales de Gmail
- Comprobar App Password
- Revisar configuración SMTP
- Verificar conectividad a internet

### Error de base de datos
- Verificar permisos de escritura
- Comprobar espacio en disco
- Revisar integridad de la base de datos
- Restaurar desde backup si es necesario

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico o preguntas:

- **Email:** soporte@tudominio.com
- **Issues:** [GitHub Issues](https://github.com/tu-usuario/Admin-Skypass/issues)
- **Documentación:** [Wiki del proyecto](https://github.com/tu-usuario/Admin-Skypass/wiki)

---

**Admin Skypass** - Sistema de Administración de ISPs v1.0.0
