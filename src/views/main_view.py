import os 
import sys
from PyQt6 import uic
from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QApplication


class MainView(QMainWindow):

    # Signal to indicate that a child form should be opened
    form_members_requested = pyqtSignal()
    
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
        

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    main_view = MainView()
    
    main_view.show()
    
    sys.exit(app.exec())