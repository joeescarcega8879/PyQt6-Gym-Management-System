import os 
import sys
from PyQt6 import uic
from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QApplication


class MainView(QMainWindow):
    
    def __init__(self):
        super(MainView, self).__init__()
        
        # Initialize components
        self.initialize_components()
        
    
    def initialize_components(self):
        # Load ui path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        # Load ui
        uic.loadUi(ui_path, self)
        
        self.show()
        

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    main_view = MainView()
    
    main_view.show()
    
    sys.exit(app.exec())