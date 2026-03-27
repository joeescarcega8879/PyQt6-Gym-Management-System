import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate
from PyQt6.QtWidgets import QWidget, QMessageBox
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon

class AttendanceView(QWidget):

    # Signals for communication with the presenter


    def __init__(self) -> None:
        super(AttendanceView, self).__init__()

        # Initialize components
        self.initialize_components()

    def initialize_components(self) -> None:
        # Load ui path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "attendance_view.ui")
        # Load ui
        uic.loadUi(ui_path, self)

        self.btn_close.clicked.connect(self.close)
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))