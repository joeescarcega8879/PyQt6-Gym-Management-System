import os 
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QMessageBox

class LoginView(QWidget):
    
    # Signals
    login_requested = pyqtSignal()
    
    def __init__(self):
        super(LoginView, self).__init__()
        
        # Initialize Components
        self.initialize_components()
        
        
    def initialize_components(self):
        # Load UI Path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "login_view.ui")
        # Load UI
        uic.loadUi(ui_path, self)
        
        self.input_username.setFocus()
        
        # Connect Signals
        self.btn_login.clicked.connect(self.login_requested.emit)
        
    def get_credentials(self):
        return{
            'username': self.input_username.text(),
            'password': self.input_password.text()
        }
        
    def clear_form(self):
        self.input_username.clear()
        self.input_password.clear()
        self.input_username.setFocus()
        
    def show_error(self, message):
        QMessageBox.critical(self, "Login Error", message)