from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time
import os
from functools import wraps
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu-clave-secreta-aqui')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///isps.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Función para leer configuración del .env en tiempo real
def get_env_config():
    env_file = '.env'
    config = {
        'GMAIL_USER': 'tu-email@gmail.com',
        'GMAIL_PASSWORD': 'tu-app-password',
        'SECRET_KEY': 'tu-clave-secreta-aqui'
    }
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    
    return config

# Configuración inicial
env_config = get_env_config()
GMAIL_USER = env_config['GMAIL_USER']
GMAIL_PASSWORD = env_config['GMAIL_PASSWORD']
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Modelo de datos
class ISP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ip_vm = db.Column(db.String(15), nullable=False)
    genieacs_url = db.Column(db.String(200), nullable=False)
    limite_clientes = db.Column(db.Integer, nullable=False)
    email_alerta = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    dispositivos_actuales = db.Column(db.Integer, default=0)
    ultima_verificacion = db.Column(db.DateTime)
    ultima_alerta = db.Column(db.DateTime)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Alerta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isp_id = db.Column(db.Integer, db.ForeignKey('isp.id'), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    enviada = db.Column(db.Boolean, default=False)
    
    # Relación con ISP
    isp = db.relationship('ISP', backref=db.backref('alertas', lazy=True))

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Función para verificar dispositivos en GenieACS
def verificar_dispositivos_genieacs(isp):
    try:
        # Limpiar la URL y asegurar que tenga el protocolo correcto
        genieacs_url = isp.genieacs_url.strip()
        
        # Siempre usar http:// como protocolo por defecto
        if genieacs_url.startswith('http://http://'):
            # Si tiene protocolo duplicado, limpiar
            genieacs_url = genieacs_url.replace('http://http://', 'http://')
        elif genieacs_url.startswith('https://'):
            # Si tiene https, cambiar a http
            genieacs_url = genieacs_url.replace('https://', 'http://')
        elif not genieacs_url.startswith('http://'):
            # Si no tiene protocolo, agregar http://
            genieacs_url = f"http://{genieacs_url}"
        
        # Remover barra final si existe
        genieacs_url = genieacs_url.rstrip('/')
        
        # Extraer la IP base para construir la URL de la API (puerto 7557)
        from urllib.parse import urlparse
        parsed_url = urlparse(genieacs_url)
        base_ip = parsed_url.netloc.split(':')[0]
        
        # Construir URL de API con puerto 7557
        api_base_url = f"http://{base_ip}:7557"
        
        print(f"URL original: {isp.genieacs_url}")
        print(f"URL UI (3000): {genieacs_url}")
        print(f"URL API (7557): {api_base_url}")
        
        # Intentar diferentes endpoints de GenieACS en puerto 7557
        endpoints_to_try = [
            f"{api_base_url}/devices",  # Endpoint principal
            f"{api_base_url}/api/v1/devices",  # API v1
            f"{api_base_url}/api/devices",  # API alternativa
        ]
        
        for endpoint in endpoints_to_try:
            try:
                print(f"Intentando conectar a: {endpoint}")
                response = requests.get(endpoint, timeout=10, headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                })
                
                if response.status_code == 200:
                    try:
                        devices = response.json()
                        if isinstance(devices, list):
                            device_count = len(devices)
                            print(f"Dispositivos encontrados en {isp.nombre}: {device_count}")
                            return device_count
                        elif isinstance(devices, dict) and 'devices' in devices:
                            device_count = len(devices['devices'])
                            print(f"Dispositivos encontrados en {isp.nombre}: {device_count}")
                            return device_count
                        else:
                            print(f"Formato de respuesta inesperado para {isp.nombre}")
                            continue
                    except ValueError as json_error:
                        print(f"Error al parsear JSON de {isp.nombre}: {json_error}")
                        continue
                else:
                    print(f"Error HTTP {response.status_code} para {isp.nombre} en {endpoint}")
                    continue
                    
            except requests.exceptions.RequestException as req_error:
                print(f"Error de conexión para {isp.nombre} en {endpoint}: {req_error}")
                continue
        
        print(f"No se pudo conectar con GenieACS para {isp.nombre} en ningún endpoint")
        return 0
        
    except Exception as e:
        print(f"Error general al verificar dispositivos para {isp.nombre}: {str(e)}")
        return 0

# Función para enviar email de alerta
def enviar_alerta_email(isp, dispositivos_actuales, tipo_alerta="superado"):
    try:
        # Leer configuración actual del .env
        current_config = get_env_config()
        current_gmail_user = current_config['GMAIL_USER']
        current_gmail_password = current_config['GMAIL_PASSWORD']
        
        # Determinar tipo de alerta y contenido
        if tipo_alerta == "superado":
            icono = "🚨"
            titulo = "Límite de clientes superado"
            color_alerta = "#dc3545"
            mensaje_principal = "ha superado su límite de clientes configurado"
        else:  # cerca_limite
            icono = "⚠️"
            titulo = "Cerca del límite de clientes"
            color_alerta = "#ffc107"
            mensaje_principal = "está cerca de su límite de clientes configurado"
        
        # Email simple para el cliente
        msg_cliente = MIMEMultipart()
        msg_cliente['From'] = current_gmail_user
        msg_cliente['To'] = isp.email_alerta
        msg_cliente['Subject'] = f"{icono} {titulo}: {isp.nombre}"
        
        body_cliente = f"""
        <h2>{icono} {titulo}</h2>
        <p>Hola,</p>
        <p>Te informamos que <strong>{isp.nombre}</strong> {mensaje_principal}.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>📊 Resumen:</strong></p>
            <ul>
                <li>Dispositivos actuales: <strong>{dispositivos_actuales}</strong></li>
                <li>Límite permitido: <strong>{isp.limite_clientes}</strong></li>
                <li>Porcentaje de uso: <strong>{(dispositivos_actuales / isp.limite_clientes) * 100:.1f}%</strong></li>
                {f'<li>Exceso: <strong>{dispositivos_actuales - isp.limite_clientes} dispositivo(s)</strong></li>' if tipo_alerta == "superado" else ''}
            </ul>
        </div>
        
        <p style="color: {color_alerta};"><strong>⚠️ Por favor, comunícate con la empresa para cambiar de plan.</strong></p>
        
        <p>Fecha: {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
        
        <hr>
        <p><small>Sistema de Monitoreo SKYPASS Admin</small></p>
        """
        
        msg_cliente.attach(MIMEText(body_cliente, 'html'))
        
        # Email detallado para el admin (tú)
        msg_admin = MIMEMultipart()
        msg_admin['From'] = current_gmail_user
        msg_admin['To'] = current_gmail_user  # Te lo envías a ti mismo
        msg_admin['Subject'] = f"🔧 [ADMIN] {titulo}: {isp.nombre} - Detalles técnicos"
        
        body_admin = f"""
        <h2>🔧 Alerta Técnica para Administrador</h2>
        <p><strong>Tipo de Alerta:</strong> {titulo}</p>
        <p><strong>ISP:</strong> {isp.nombre}</p>
        <p><strong>IP de VM:</strong> {isp.ip_vm}</p>
        <p><strong>URL GenieACS:</strong> {isp.genieacs_url}</p>
        <p><strong>Dispositivos actuales:</strong> {dispositivos_actuales}</p>
        <p><strong>Límite establecido:</strong> {isp.limite_clientes}</p>
        <p><strong>Porcentaje de uso:</strong> {(dispositivos_actuales / isp.limite_clientes) * 100:.1f}%</p>
        {f'<p><strong>Exceso:</strong> {dispositivos_actuales - isp.limite_clientes} dispositivo(s)</p>' if tipo_alerta == "superado" else ''}
        <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>📋 Acciones recomendadas:</strong></p>
            <ul>
                <li>Verificar conectividad con GenieACS</li>
                <li>Revisar configuración de límites</li>
                <li>Contactar al ISP si es necesario</li>
            </ul>
        </div>
        
        <p style="color: {color_alerta};"><strong>⚠️ El ISP {mensaje_principal}.</strong></p>
        """
        
        msg_admin.attach(MIMEText(body_admin, 'html'))
        
        # Enviar ambos emails
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(current_gmail_user, current_gmail_password)
        
        # Email al cliente
        text_cliente = msg_cliente.as_string()
        server.sendmail(current_gmail_user, isp.email_alerta, text_cliente)
        
        # Email al admin (tú)
        text_admin = msg_admin.as_string()
        server.sendmail(current_gmail_user, current_gmail_user, text_admin)
        
        server.quit()
        
        # Registrar la alerta en la base de datos
        if tipo_alerta == "superado":
            mensaje_alerta = f"🚨 ALERTA: {isp.nombre} superó el límite: {dispositivos_actuales}/{isp.limite_clientes}"
        else:
            mensaje_alerta = f"⚠️ CERCA DEL LÍMITE: {isp.nombre} está cerca del límite: {dispositivos_actuales}/{isp.limite_clientes} ({(dispositivos_actuales / isp.limite_clientes) * 100:.1f}%)"
        
        alerta = Alerta(
            isp_id=isp.id,
            mensaje=mensaje_alerta,
            enviada=True
        )
        db.session.add(alerta)
        isp.ultima_alerta = datetime.now(timezone.utc)
        db.session.commit()
        
        print(f"Alerta enviada para {isp.nombre} (cliente y admin)")
        return True
    except Exception as e:
        print(f"Error al enviar email para {isp.nombre}: {str(e)}")
        return False

# Función para monitoreo automático
def monitoreo_automatico():
    while True:
        try:
            with app.app_context():
                isps = ISP.query.all()
                for isp in isps:
                    dispositivos_actuales = verificar_dispositivos_genieacs(isp)
                    isp.dispositivos_actuales = dispositivos_actuales
                    isp.ultima_verificacion = datetime.now(timezone.utc)
                    
                    # Verificar si necesita alerta (cerca del límite o superado)
                    porcentaje_uso = (dispositivos_actuales / isp.limite_clientes) * 100
                    necesita_alerta = False
                    tipo_alerta = ""
                    
                    if dispositivos_actuales > isp.limite_clientes:
                        necesita_alerta = True
                        tipo_alerta = "superado"
                    elif porcentaje_uso >= 80:  # 80% o más del límite
                        necesita_alerta = True
                        tipo_alerta = "cerca_limite"
                    
                    if (necesita_alerta and 
                        isp.email_alerta and 
                        (not isp.ultima_alerta or 
                         (isp.ultima_alerta and 
                          datetime.now(timezone.utc) - isp.ultima_alerta.replace(tzinfo=timezone.utc) > timedelta(days=1)))):
                        enviar_alerta_email(isp, dispositivos_actuales, tipo_alerta)
                    
                    db.session.commit()
                
                print(f"Monitoreo completado: {datetime.now()}")
        except Exception as e:
            print(f"Error en monitoreo automático: {str(e)}")
        
        time.sleep(600)  # 10 minutos

# Ruta para servir archivos estáticos
@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

# Rutas de la aplicación
@app.route('/')
@login_required
def dashboard():
    isps = ISP.query.all()
    total_isps = len(isps)
    total_dispositivos = sum(isp.dispositivos_actuales for isp in isps)
    
    # ISPs cerca del límite (80% o más)
    isps_cerca_limite = [isp for isp in isps if isp.dispositivos_actuales >= isp.limite_clientes * 0.8 and isp.dispositivos_actuales <= isp.limite_clientes]
    
    # ISPs sobrepasados
    isps_sobrepasados = [isp for isp in isps if isp.dispositivos_actuales > isp.limite_clientes]
    
    # ISPs que requieren atención (combinados)
    isps_problemas = isps_cerca_limite + isps_sobrepasados
    
    # Calcular estadísticas adicionales
    isps_activos = len([isp for isp in isps if isp.dispositivos_actuales > 0])
    isps_inactivos = total_isps - isps_activos
    
    # Últimas alertas
    ultimas_alertas = Alerta.query.order_by(Alerta.fecha_envio.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         total_isps=total_isps,
                         total_dispositivos=total_dispositivos,
                         isps_activos=isps_activos,
                         isps_inactivos=isps_inactivos,
                         isps_cerca_limite=isps_cerca_limite,
                         isps_sobrepasados=isps_sobrepasados,
                         isps_problemas=isps_problemas,
                         isps=isps,  # Lista completa para la tabla breve
                         ultimas_alertas=ultimas_alertas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['logged_in'] = True
            session['username'] = username
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/isps')
@login_required
def lista_isps():
    isps = ISP.query.all()
    return render_template('lista_isps.html', isps=isps)

@app.route('/agregar_isp', methods=['GET', 'POST'])
@login_required
def agregar_isp():
    if request.method == 'POST':
        nombre = request.form['nombre']
        ip_vm = request.form['ip_vm']
        genieacs_url = request.form['genieacs_url']
        limite_clientes = int(request.form['limite_clientes'])
        email_alerta = request.form.get('email_alerta', '')
        
        # Verificar que no exista un ISP con la misma IP
        isp_existente = ISP.query.filter_by(ip_vm=ip_vm).first()
        if isp_existente:
            return jsonify({'success': False, 'message': 'Ya existe un ISP con esa IP de VM'})
        
        nuevo_isp = ISP(
            nombre=nombre,
            ip_vm=ip_vm,
            genieacs_url=genieacs_url,
            limite_clientes=limite_clientes,
            email_alerta=email_alerta
        )
        
        db.session.add(nuevo_isp)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'ISP {nombre} agregado correctamente'})
    
    return render_template('agregar_isp.html')

@app.route('/editar_isp/<int:isp_id>', methods=['GET', 'POST'])
@login_required
def editar_isp(isp_id):
    isp = ISP.query.get_or_404(isp_id)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        ip_vm = request.form['ip_vm']
        genieacs_url = request.form['genieacs_url']
        limite_clientes = int(request.form['limite_clientes'])
        email_alerta = request.form.get('email_alerta', '')
        
        # Verificar que no exista otro ISP con la misma IP
        isp_existente = ISP.query.filter(ISP.ip_vm == ip_vm, ISP.id != isp_id).first()
        if isp_existente:
            return jsonify({'success': False, 'message': 'Ya existe otro ISP con esa IP de VM'})
        
        isp.nombre = nombre
        isp.ip_vm = ip_vm
        isp.genieacs_url = genieacs_url
        isp.limite_clientes = limite_clientes
        isp.email_alerta = email_alerta
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'ISP {nombre} actualizado correctamente'})
    
    return render_template('editar_isp.html', isp=isp)

@app.route('/verificar_dispositivos/<int:isp_id>')
@login_required
def verificar_dispositivos(isp_id):
    isp = ISP.query.get_or_404(isp_id)
    dispositivos_actuales = verificar_dispositivos_genieacs(isp)
    isp.dispositivos_actuales = dispositivos_actuales
    isp.ultima_verificacion = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        'dispositivos_actuales': dispositivos_actuales,
        'limite_clientes': isp.limite_clientes,
        'estado': 'sobrepasado' if dispositivos_actuales > isp.limite_clientes else 'normal'
    })

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if request.method == 'POST':
        # Actualizar archivo .env
        env_file = '.env'
        env_content = []
        
        # Leer archivo .env existente o crear uno nuevo
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.readlines()
        else:
            # Crear archivo .env básico si no existe
            env_content = [
                "# Configuración de Admin Skypass\n",
                "SECRET_KEY=tu-clave-secreta-muy-segura-aqui\n",
                "DATABASE_URL=sqlite:///isps.db\n",
                "GMAIL_USER=tu-email@gmail.com\n",
                "GMAIL_PASSWORD=tu-app-password-de-16-caracteres\n",
                "HOST=0.0.0.0\n",
                "PORT=5000\n",
                "DEBUG=False\n",
                "MONITORING_INTERVAL=600\n",
                "ALERT_COOLDOWN=86400\n"
            ]
        
        # Actualizar variables
        updated_vars = {
            'GMAIL_USER': request.form.get('gmail_user', ''),
            'GMAIL_PASSWORD': request.form.get('gmail_password', ''),
            'SECRET_KEY': request.form.get('secret_key', ''),
        }
        
        # Manejar cambio de contraseña de admin
        admin_password = request.form.get('admin_password', '')
        if admin_password:
            # Actualizar contraseña en la base de datos
            admin = Admin.query.first()
            if admin:
                admin.password = generate_password_hash(admin_password)
                db.session.commit()
                flash('Contraseña de admin actualizada correctamente.', 'success')
            else:
                flash('Error: No se encontró usuario admin.', 'error')
        
        # Procesar cada línea del archivo .env
        new_content = []
        updated_keys = set()
        
        for line in env_content:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in updated_vars and updated_vars[key]:
                    new_content.append(f"{key}={updated_vars[key]}\n")
                    updated_keys.add(key)
                else:
                    new_content.append(line)
            else:
                new_content.append(line)
        
        # Agregar variables que no existían
        for key, value in updated_vars.items():
            if key not in updated_keys and value:
                new_content.append(f"{key}={value}\n")
        
        # Escribir archivo .env actualizado
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_content)
        
        flash('Configuración actualizada correctamente.', 'success')
        return redirect(url_for('configuracion'))
    
    # Leer configuración actual del .env
    current_config = get_env_config()
    
    return render_template('configuracion.html', 
                         gmail_user=current_config['GMAIL_USER'],
                         gmail_password="••••••••••••••••",
                         secret_key=current_config['SECRET_KEY'])

@app.route('/enviar_email_alerta/<int:isp_id>')
@login_required
def enviar_email_alerta(isp_id):
    try:
        isp = ISP.query.get_or_404(isp_id)
        
        if not isp.email_alerta:
            return jsonify({'success': False, 'message': 'No hay email configurado para este ISP'})
        
        # Determinar tipo de alerta basado en el uso actual
        porcentaje_uso = (isp.dispositivos_actuales / isp.limite_clientes) * 100
        
        if isp.dispositivos_actuales > isp.limite_clientes:
            tipo_alerta = "superado"
        elif porcentaje_uso >= 80:
            tipo_alerta = "cerca_limite"
        else:
            tipo_alerta = "cerca_limite"  # Por defecto, enviar como "cerca del límite"
        
        # Enviar la alerta
        success = enviar_alerta_email(isp, isp.dispositivos_actuales, tipo_alerta)
        
        if success:
            return jsonify({'success': True, 'message': f'Email de alerta enviado a {isp.nombre}'})
        else:
            return jsonify({'success': False, 'message': 'Error al enviar el email'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/reenviar_alerta/<int:alerta_id>')
@login_required
def reenviar_alerta(alerta_id):
    try:
        alerta = Alerta.query.get_or_404(alerta_id)
        isp = alerta.isp
        
        if not isp.email_alerta:
            return jsonify({'success': False, 'message': 'No hay email configurado para este ISP'})
        
        # Determinar tipo de alerta basado en el mensaje
        if "superó el límite" in alerta.mensaje:
            tipo_alerta = "superado"
        else:
            tipo_alerta = "cerca_limite"
        
        # Reenviar la alerta
        success = enviar_alerta_email(isp, isp.dispositivos_actuales, tipo_alerta)
        
        if success:
            # Actualizar la fecha de la alerta
            alerta.fecha_envio = datetime.now(timezone.utc)
            alerta.enviada = True
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'Alerta reenviada correctamente a {isp.nombre}'})
        else:
            return jsonify({'success': False, 'message': 'Error al reenviar la alerta'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/eliminar_isp/<int:isp_id>')
@login_required
def eliminar_isp(isp_id):
    isp = ISP.query.get_or_404(isp_id)
    nombre = isp.nombre
    db.session.delete(isp)
    db.session.commit()
    flash(f'ISP {nombre} eliminado correctamente', 'success')
    return redirect(url_for('lista_isps'))

@app.route('/probar_conexion', methods=['POST'])
@login_required
def probar_conexion():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL no proporcionada'})
        
        # Crear un objeto ISP temporal para probar
        class TempISP:
            def __init__(self, url):
                self.nombre = 'Prueba'
                self.genieacs_url = url
        
        temp_isp = TempISP(url)
        dispositivos = verificar_dispositivos_genieacs(temp_isp)
        
        if dispositivos >= 0:
            return jsonify({
                'success': True, 
                'dispositivos': dispositivos,
                'mensaje': f'Conexión exitosa. Se encontraron {dispositivos} dispositivos.'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'No se pudo conectar con el servidor GenieACS'
            })
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error al probar conexión: {str(e)}'
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Crear usuario admin por defecto si no existe
        admin_existente = Admin.query.filter_by(username='admin').first()
        if not admin_existente:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado: admin / admin123")
    
    # Iniciar monitoreo en hilo separado
    monitor_thread = threading.Thread(target=monitoreo_automatico, daemon=True)
    monitor_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
