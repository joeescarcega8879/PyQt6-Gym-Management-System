"""
Servicio de autenticación.
Gestiona el login, logout y sesiones de usuario.
"""
from typing import Optional, Tuple
import bcrypt
import logging
from src.database import db_manager
from src.models import User, UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """Servicio de autenticación de usuarios"""
    
    def __init__(self):
        self.current_user: Optional[User] = None
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Autentica un usuario.
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            Tuple[bool, Optional[str], Optional[User]]: 
                - Éxito (True/False)
                - Mensaje de error (si aplica)
                - Usuario autenticado (si aplica)
        """
        try:
            # Buscar usuario por username
            users = db_manager.select(
                table='users',
                filters={'username': username, 'is_active': True}
            )
            
            if not users:
                return False, "Usuario no encontrado o inactivo", None
            
            user_data = users[0]
            
            # Verificar contraseña
            password_valid = self._verify_password(
                password, 
                user_data['password_hash']
            )
            
            if not password_valid:
                logger.warning(f"Intento de login fallido para usuario: {username}")
                return False, "Contraseña incorrecta", None
            
            # Crear objeto User
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                role=UserRole(user_data['role']),
                is_active=user_data['is_active'],
                created_at=user_data['created_at'],
                updated_at=user_data['updated_at']
            )
            
            self.current_user = user
            logger.info(f"Usuario {username} autenticado exitosamente")
            
            return True, None, user
            
        except Exception as e:
            error_msg = f"Error durante el login: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def logout(self):
        """Cierra la sesión del usuario actual"""
        if self.current_user:
            logger.info(f"Usuario {self.current_user.username} cerró sesión")
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """
        Verifica si hay un usuario autenticado.
        
        Returns:
            bool: True si hay un usuario autenticado
        """
        return self.current_user is not None
    
    def has_permission(self, required_role: UserRole) -> bool:
        """
        Verifica si el usuario actual tiene los permisos necesarios.
        
        Args:
            required_role: Rol requerido
            
        Returns:
            bool: True si tiene permisos
        """
        if not self.is_authenticated():
            return False
        
        # Admin tiene acceso a todo
        if self.current_user.role == UserRole.ADMIN:
            return True
        
        # Verificar rol específico
        return self.current_user.role == required_role
    
    def get_current_user(self) -> Optional[User]:
        """
        Retorna el usuario actualmente autenticado.
        
        Returns:
            Optional[User]: Usuario actual o None
        """
        return self.current_user
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Genera un hash de contraseña usando bcrypt.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica si una contraseña coincide con su hash.
        
        Args:
            password: Contraseña en texto plano
            password_hash: Hash almacenado
            
        Returns:
            bool: True si la contraseña es correcta
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error al verificar contraseña: {str(e)}")
            return False
    
    def create_user(self, username: str, email: str, password: str,
                   full_name: str, role: UserRole = UserRole.RECEPTIONIST) -> Tuple[bool, Optional[str]]:
        """
        Crea un nuevo usuario en el sistema.
        
        Args:
            username: Nombre de usuario
            email: Email
            password: Contraseña en texto plano
            full_name: Nombre completo
            role: Rol del usuario
            
        Returns:
            Tuple[bool, Optional[str]]: Éxito y mensaje de error (si aplica)
        """
        try:
            # Verificar si el usuario ya existe
            existing = db_manager.select(
                table='users',
                filters={'username': username}
            )
            
            if existing:
                return False, "El nombre de usuario ya existe"
            
            # Verificar email
            existing_email = db_manager.select(
                table='users',
                filters={'email': email}
            )
            
            if existing_email:
                return False, "El email ya está registrado"
            
            # Hash de contraseña
            password_hash = self.hash_password(password)
            
            # Crear usuario
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'full_name': full_name,
                'role': role.value
            }
            
            db_manager.insert('users', user_data)
            logger.info(f"Usuario {username} creado exitosamente")
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error al crear usuario: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def change_password(self, user_id: str, old_password: str, 
                       new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            user_id: ID del usuario
            old_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Tuple[bool, Optional[str]]: Éxito y mensaje de error (si aplica)
        """
        try:
            # Obtener usuario
            users = db_manager.select(
                table='users',
                filters={'id': user_id}
            )
            
            if not users:
                return False, "Usuario no encontrado"
            
            user_data = users[0]
            
            # Verificar contraseña actual
            if not self._verify_password(old_password, user_data['password_hash']):
                return False, "Contraseña actual incorrecta"
            
            # Hash de nueva contraseña
            new_password_hash = self.hash_password(new_password)
            
            # Actualizar contraseña
            db_manager.update(
                table='users',
                data={'password_hash': new_password_hash},
                filters={'id': user_id}
            )
            
            logger.info(f"Contraseña cambiada para usuario ID: {user_id}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error al cambiar contraseña: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Instancia global del servicio de autenticación
auth_service = AuthService()
