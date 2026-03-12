import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

class MemberView(QWidget):

    def __init__(self):
        super(MemberView, self).__init__()

        # Initialize components
        self.initialize_components()

    def initialize_components(self):
        # Load ui path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "member_view.ui")
        # Load ui
        uic.loadUi(ui_path, self)