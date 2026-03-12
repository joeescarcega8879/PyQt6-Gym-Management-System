
import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMdiSubWindow

from src.config import config

from src.views.login_view import LoginView
from src.views.main_view import MainView
from src.views.member_view import MemberView

from src.presenters.login_presenter import LoginPresenter
from src.presenters.main_presenter import MainPresenter
from src.presenters.member_presenter import MemberPresenter


class MainApplication:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self._init_login()

    def setup_logging(self):
        """Configura el sistema de logging"""
        config.setup_directories()
        
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
    def _init_login(self):
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, on_login_success=self._initialize_main_window)
        self.login_view.show()
    
    def _initialize_main_window(self, user):
        self.current_user = user
        
        self.main_view = MainView()
        self.main_presenter = MainPresenter(self.main_view, self, self.current_user)
        
        self.login_view.close()

    def open_members_form(self):
        self.logger.info("Opening members form")
        
        member_view = MemberView()
        member_presenter = MemberPresenter(member_view, self.current_user)
        
        mdi_sub_window = QMdiSubWindow()
        
        self.main_view.open_child_form(member_view, mdi_sub_window)

        
def main():
    app = QApplication(sys.argv)
    
    controller = MainApplication()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()