"""
Configuración centralizada de la aplicación.
Lee variables de entorno y proporciona configuración para toda la app.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Obtener el directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / '.env'

# Cargar variables de entorno
load_dotenv(ENV_FILE)


class Config:
    """Configuración principal de la aplicación"""
    
    # Información de la aplicación
    APP_NAME = os.getenv('APP_NAME', 'Gym Management System')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
    
    # Base de datos local (offline)
    LOCAL_DB_PATH = ROOT_DIR / os.getenv('LOCAL_DB_PATH', 'data/gym_local.db')
    
    # Logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = ROOT_DIR / os.getenv('LOG_FILE', 'logs/gym_system.log')
    
    # Directorios
    DATA_DIR = ROOT_DIR / 'data'
    LOGS_DIR = ROOT_DIR / 'logs'
    RESOURCES_DIR = ROOT_DIR / 'src' / 'resources'
    
    @classmethod
    def validate(cls):
        """Valida que la configuración sea correcta"""
        errors = []
        
        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL no está configurada en .env")
        
        if not cls.SUPABASE_KEY:
            errors.append("SUPABASE_KEY no está configurada en .env")
        
        if cls.SECRET_KEY == 'default-secret-key-change-in-production':
            errors.append("SECRET_KEY debe ser cambiada en producción")
        
        if errors:
            return False, errors
        
        return True, []
    
    @classmethod
    def setup_directories(cls):
        """Crea los directorios necesarios si no existen"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_database_config(cls):
        """Retorna la configuración de la base de datos"""
        return {
            'url': cls.SUPABASE_URL,
            'key': cls.SUPABASE_KEY
        }


# Instancia global de configuración
config = Config()
