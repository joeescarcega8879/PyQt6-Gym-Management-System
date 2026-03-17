from PyQt6.QtCore import QTimer
from . status_type import StatusType
from . status_bar_styles import STATUS_BAR_STYLES


class StatusBarController:
    
    """Controller for managing status bar messages and styles."""
    
    def __init__(self, status_bar):
        self.status_bar = status_bar

    def show_message(self, message: str, duration:int, status: StatusType)-> None:
        """
        Displays a message in the status bar with a specific duration and style based on the status type.
        Args:
            message: The message to display.
            duration: Duration in milliseconds for which the message should be displayed.
            status: The type of status (success, error, warning) to determine the styling.
        """

        self.status_bar.setStyleSheet("")

        style = STATUS_BAR_STYLES.get(status)
        if style:
            self.status_bar.setStyleSheet(style)
        
        self.status_bar.showMessage(message, duration)

        QTimer.singleShot(duration, lambda: self.status_bar.setStyleSheet("background-color: white;"))

           