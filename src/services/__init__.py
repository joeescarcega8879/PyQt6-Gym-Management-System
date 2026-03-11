"""
Servicios de la aplicación.
Contiene toda la lógica de negocio reutilizable.
"""
from src.services.auth_service import auth_service, AuthService

__all__ = ['auth_service', 'AuthService']
