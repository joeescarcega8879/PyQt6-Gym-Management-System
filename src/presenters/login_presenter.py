from PyQt6.QtCore import QThread, pyqtSignal
from src.services import auth_service
from src.models import User
import logging

logger = logging.getLogger(__name__)


class LoginWorker(QThread):
    """Executes auth_service.login() in a background thread to avoid blocking the UI."""

    login_success = pyqtSignal(object)   # emits User
    login_failed = pyqtSignal(str)       # emits error message

    def __init__(self, username: str, password: str):
        super().__init__()
        self._username = username
        self._password = password

    def run(self):
        try:
            success, error_message, user = auth_service.login(
                self._username, self._password
            )
            if success and user:
                logger.info(f"Login successful for user: {self._username}")
                self.login_success.emit(user)
            else:
                logger.warning(f"Login failed for user: {self._username}")
                self.login_failed.emit(error_message or "Unknown error")
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            self.login_failed.emit(f"Connection error: {str(e)}")


class LoginPresenter:
    def __init__(self, view, on_login_success):
        self.view = view
        self._on_login_success = on_login_success
        self._worker = None
        self._connect_signals()

    def _connect_signals(self):
        self.view.login_requested.connect(self._handle_login)

    def _handle_login(self):
        data = self.view.get_credentials()
        username = data.get('username')
        password = data.get('password')

        # Disable UI while login is in progress
        self.view.set_loading(True)

        # Create and start the background worker
        self._worker = LoginWorker(username, password)
        self._worker.login_success.connect(self._on_worker_success)
        self._worker.login_failed.connect(self._on_worker_failed)
        self._worker.start()

    def _on_worker_success(self, user):
        self.view.set_loading(False)
        self._on_login_success(user)

    def _on_worker_failed(self, error_message: str):
        self.view.set_loading(False)
        self.view.show_error(error_message)
        self.view.clear_form()
