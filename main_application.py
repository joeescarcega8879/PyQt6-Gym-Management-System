import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMdiSubWindow

from src.config import config
from src.utils.status_bar_controller import StatusBarController
from src.utils.status_type import StatusType

from src.views.login_view import LoginView
from src.views.main_view import MainView
from src.views.dashboard_view import DashboardView
from src.views.member_view import MemberView
from src.views.attendance_view import AttendanceView
from src.views.payment_view import PaymentView
from src.views.membership_view import MembershipView
from src.views.class_view import ClassView
from src.views.settings_view import SettingsView
from src.views.instructor_view import InstructorView
from src.views.equipment_view import EquipmentView

from src.presenters.login_presenter import LoginPresenter
from src.presenters.main_presenter import MainPresenter
from src.presenters.dashboard_presenter import DashboardPresenter
from src.presenters.member_presenter import MemberPresenter
from src.presenters.attendance_presenter import AttendancePresenter
from src.presenters.payment_presenter import PaymentPresenter
from src.presenters.membership_presenter import MembershipPresenter
from src.presenters.class_presenter import ClassPresenter
from src.presenters.settings_presenter import SettingsPresenter
from src.presenters.instructor_presenter import InstructorPresenter
from src.presenters.equipment_presenter import EquipmentPresenter

from src.services.settings_service import settings_service

import src.assets.resources_rc  # noqa — loads embedded icons into memory


class MainApplication:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        # Load saved theme preference before showing any UI
        saved = settings_service.load()
        theme_key = saved.data.get("theme", "dark_blue") if saved.success else "dark_blue"
        self.load_stylesheet(theme_key)
        self._init_login()

    def setup_logging(self) -> None:
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
    
    def load_stylesheet(self, theme_key: str = "dark_blue") -> None:
        """
        Loads and applies the CSS stylesheet for the given theme key.

        Tries src/assets/themes/<theme_key>.css first.
        Falls back to src/assets/styles.css if the theme file is missing.

        Args:
            theme_key: Key from AVAILABLE_THEMES (e.g. 'dark_blue', 'dark_green').
        """
        try:
            # Prefer the theme-specific file
            result = settings_service.load_theme_css(theme_key)
            if result.success:
                QApplication.instance().setStyleSheet(result.data)
                self.logger.info(f"Theme '{theme_key}' loaded successfully")
                return

            # Hard fallback: read the original styles.css
            css_path = os.path.join(os.path.dirname(__file__), 'src', 'assets', 'styles.css')
            if os.path.exists(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    QApplication.instance().setStyleSheet(f.read())
                self.logger.warning(f"Theme '{theme_key}' not found — loaded default styles.css")
            else:
                self.logger.warning("No stylesheet found")
        except Exception as e:
            self.logger.error(f"Failed to load stylesheet: {e}")
        
    def _init_login(self) -> None:
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, on_login_success=self._initialize_main_window)
        self.login_view.show()
    
    def _initialize_main_window(self, user) -> None:
        self.current_user = user
        
        self.main_view = MainView()
        self.status_bar_controller = StatusBarController(self.main_view.statusbar)
        self.main_presenter = MainPresenter(self.main_view, self, self.current_user)
        
        self.login_view.close()

    def logout(self) -> None:
        self.logger.info(f"User '{self.current_user.username}' logging out")

        self.main_view.close()
        self.current_user = None

        self._init_login()

    def open_dashboard_form(self) -> None:
        self.logger.info("Opening dashboard form")

        self.dashboard_view = DashboardView()
        self.dashboard_presenter = DashboardPresenter(self.dashboard_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.dashboard_view, mdi_sub_window)

    def open_members_form(self) -> None:
        self.logger.info("Opening members form")
        
        self.member_view = MemberView()
        self.member_presenter = MemberPresenter(self.member_view, self, self.status_bar_controller.show_message, self.current_user)
        
        mdi_sub_window = QMdiSubWindow()
        
        self.main_view.open_child_form(self.member_view, mdi_sub_window)

    def open_attendance_form(self) -> None:
        self.logger.info("Opening attendance form")

        self.attendance_view = AttendanceView()
        self.attendance_presenter = AttendancePresenter(self.attendance_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.attendance_view, mdi_sub_window)

    def open_payments_form(self) -> None:
        self.logger.info("Opening payments form")

        self.payment_view = PaymentView()
        self.payment_presenter = PaymentPresenter(self.payment_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.payment_view, mdi_sub_window)

    def open_memberships_form(self) -> None:
        self.logger.info("Opening memberships form")

        self.membership_view = MembershipView()
        self.membership_presenter = MembershipPresenter(self.membership_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.membership_view, mdi_sub_window)

    def open_classes_form(self) -> None:
        self.logger.info("Opening classes form")

        self.class_view = ClassView()
        self.class_presenter = ClassPresenter(self.class_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.class_view, mdi_sub_window)

    def open_settings_form(self) -> None:
        self.logger.info("Opening settings form")

        self.settings_view = SettingsView()
        self.settings_presenter = SettingsPresenter(
            self.settings_view, self, self.status_bar_controller.show_message, self.current_user
        )

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.settings_view, mdi_sub_window)

    def open_instructors_form(self) -> None:
        self.logger.info("Opening instructors form")

        self.instructor_view = InstructorView()
        self.instructor_presenter = InstructorPresenter(self.instructor_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.instructor_view, mdi_sub_window)

    def open_equipment_form(self) -> None:
        self.logger.info("Opening equipment form")

        self.equipment_view = EquipmentView()
        self.equipment_presenter = EquipmentPresenter(self.equipment_view, self, self.status_bar_controller.show_message, self.current_user)

        mdi_sub_window = QMdiSubWindow()

        self.main_view.open_child_form(self.equipment_view, mdi_sub_window)

def main():
    app = QApplication(sys.argv)
    
    controller = MainApplication()
    # sys.exit(app.exec())
    app.exec()
    
if __name__ == "__main__":
    main()