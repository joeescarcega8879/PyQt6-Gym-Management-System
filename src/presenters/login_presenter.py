from src.services import auth_service
import logging

logger = logging.getLogger(__name__)


class LoginPresenter:
    def __init__(self, view, on_login_success):
        self.view = view
        self._on_login_success = on_login_success
        self._connect_signals()
        
    
    def _connect_signals(self):
        self.view.login_requested.connect(self._handle_login)
        
    def _handle_login(self):
        data = self.view.get_credentials()
        username = data.get('username')
        password = data.get('password')
        
        try:
            # Intentar autenticar
            success, error_message, user = auth_service.login(username, password)
            
            if success and user:
                logger.info(f"Login exitoso para usuario: {username}")
                self._on_login_success(user)
            else:
                logger.warning(f"Login fallido para usuario: {username}")
                self.view.show_error(error_message or "Error desconocido")
                self.view.clear_form()
        
        except Exception as e:
            logger.error(f"Error durante el login: {str(e)}")
            self.view.show_error(f"Error de conexión: {str(e)}")
