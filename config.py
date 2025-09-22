import os

class Config:
    """Configuración base de la aplicación"""
    
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-muy-segura-aqui'
    
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///isps.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de email
    GMAIL_USER = os.environ.get('GMAIL_USER') or 'tu-email@gmail.com'
    GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD') or 'tu-app-password'
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    
    # Configuración de monitoreo
    MONITORING_INTERVAL = 600  # 10 minutos en segundos
    ALERT_COOLDOWN = 86400  # 24 horas en segundos
    
    # Configuración de GenieACS
    GENIEACS_TIMEOUT = 10  # segundos
    GENIEACS_RETRY_ATTEMPTS = 3

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # En producción, usar variables de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY no configurada en producción")

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
