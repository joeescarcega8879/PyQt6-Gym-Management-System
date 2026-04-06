import os 
import sys
from PyQt6 import uic
from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtWidgets import QMainWindow, QApplication
from src.assets.resources_rc import get_icon


class MainView(QMainWindow):

    # Signal to indicate that a child form should be opened
    form_members_requested = pyqtSignal()
    form_attendance_requested = pyqtSignal()
    
    def __init__(self):
        super(MainView, self).__init__()
        
        # Initialize components
        self.initialize_components()
        
    
    def initialize_components(self):
        # Load ui path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        # Load ui
        uic.loadUi(ui_path, self)

        self.btn_members.clicked.connect(self.form_members_requested.emit)
        self.btn_attendance.clicked.connect(self.form_attendance_requested.emit)
        
        self.btn_colapse.clicked.connect(self.toggle_sidebar_frame)

        # Assign sidebar icons
        icon_size = QSize(24, 24)
        self.btn_dashboard.setIcon(get_icon(":/icons/IMG-Dashboard.png"))
        self.btn_dashboard.setIconSize(icon_size)
        
        self.btn_members.setIcon(get_icon(":/icons/IMG-Members.png"))
        self.btn_members.setIconSize(icon_size)
        
        self.btn_attendance.setIcon(get_icon(":/icons/IMG-Attendance.png"))
        self.btn_attendance.setIconSize(icon_size)
        
        self.btn_payments.setIcon(get_icon(":/icons/IMG-Payments.png"))
        self.btn_payments.setIconSize(icon_size)
        self.btn_memberships.setIcon(get_icon(":/icons/IMG-Memberships.png"))
        self.btn_memberships.setIconSize(icon_size)
        self.btn_classes.setIcon(get_icon(":/icons/IMG-Classes.png"))
        self.btn_classes.setIconSize(icon_size)
        self.btn_instructors.setIcon(get_icon(":/icons/IMG-Instructors.png"))
        self.btn_instructors.setIconSize(icon_size)
        self.btn_equipment.setIcon(get_icon(":/icons/IMG-Equipment.png"))
        self.btn_equipment.setIconSize(icon_size)
        self.btn_reports.setIcon(get_icon(":/icons/IMG-Reports.png"))
        self.btn_reports.setIconSize(icon_size)
        self.btn_settings.setIcon(get_icon(":/icons/IMG-Settings.png"))
        self.btn_settings.setIconSize(icon_size)
        self.btn_logout.setIcon(get_icon(":/icons/IMG-Logout.png"))
        self.btn_logout.setIconSize(icon_size)
        
        self.show()

    def open_child_form(self, objectInstance, mdiSubWindow) -> None:
        """"
        Opens a child form inside the MDI container.
        Closes any previously opened child forms.
        
        :param objectInstance: The instance of the child form to be opened.
        :param mdiSubWindow: The QMdiSubWindow that will contain the child form.

        """
        self.mdi_area.closeAllSubWindows()

        # StyleManager.apply_global_styles(objectInstance)

        mdiSubWindow.setWidget(objectInstance)
        mdiSubWindow.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        mdiSubWindow.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)

        self.mdi_area.addSubWindow(mdiSubWindow)
        mdiSubWindow.showMaximized()
        
    def toggle_sidebar_frame(self) -> None:
        if self.sidebar_frame.width() == 220:
            self.sidebar_frame.setFixedWidth(64)
            self.btn_colapse.setText(">")
            self.btn_dashboard.setText("")
            self.btn_members.setText("")
            self.btn_attendance.setText("")
            self.btn_payments.setText("")
            self.btn_memberships.setText("")
            self.btn_classes.setText("")
            self.btn_instructors.setText("")
            self.btn_equipment.setText("")
            self.btn_reports.setText("")
            self.btn_settings.setText("")
            self.btn_logout.setText("")
            
        else:
            self.sidebar_frame.setFixedWidth(220)
            self.btn_colapse.setText("< Collapse")
            self.btn_dashboard.setText("Dashboard")
            self.btn_members.setText("Members")
            self.btn_attendance.setText("Attendance")
            self.btn_payments.setText("Payments")
            self.btn_memberships.setText("Memberships")
            self.btn_classes.setText("Classes")
            self.btn_instructors.setText("Instructors")
            self.btn_equipment.setText("Equipment")
            self.btn_reports.setText("Reports")
            self.btn_settings.setText("Settings")
            self.btn_logout.setText("Logout")

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    main_view = MainView()
    
    main_view.show()
    
    sys.exit(app.exec())