"""
Centralized application configuration.
Reads environment variables and provides settings for the entire app.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the project root directory (three levels up from this file)
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / '.env'

# Load environment variables from the .env file
load_dotenv(ENV_FILE)


class Config:
    """Main application configuration class."""

    # Application info
    APP_NAME = os.getenv('APP_NAME', 'Gym Management System')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

    # PostgreSQL connection
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'gym-system')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = ROOT_DIR / os.getenv('LOG_FILE', 'logs/gym_system.log')

    # Directory paths
    DATA_DIR = ROOT_DIR / 'data'
    LOGS_DIR = ROOT_DIR / 'logs'
    RESOURCES_DIR = ROOT_DIR / 'src' / 'resources'
    EXPORTS_DIR = ROOT_DIR / 'exports'

    @classmethod
    def validate(cls):
        """
        Validates that all required configuration values are present.

        Returns:
            tuple[bool, list[str]]: (is_valid, list of errors or warnings)
        """
        errors = []
        warnings = []

        if not cls.DB_HOST:
            errors.append("DB_HOST is not set in .env")

        if not cls.DB_NAME:
            errors.append("DB_NAME is not set in .env")

        if not cls.DB_USER:
            errors.append("DB_USER is not set in .env")

        if cls.SECRET_KEY == 'default-secret-key-change-in-production':
            warnings.append("SECRET_KEY is using the default value; change it before going to production")

        if errors:
            return False, errors

        return True, warnings

    @classmethod
    def setup_directories(cls):
        """Creates required directories if they do not already exist."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.EXPORTS_DIR.mkdir(exist_ok=True)

    @classmethod
    def get_database_config(cls) -> dict:
        """
        Returns the database connection configuration.

        Returns:
            dict: Dictionary with host, port, dbname, user, password.
        """
        return {
            'host': cls.DB_HOST,
            'port': int(cls.DB_PORT),
            'dbname': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
        }


# Global configuration instance
config = Config()
