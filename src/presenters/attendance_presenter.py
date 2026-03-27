from __future__ import annotations
import logging
from typing import Optional

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.models import Attendance, User
from src.services.attendance_service import attendance_service


class AttendancePresenter:
    """Presenter for the AttendanceView, handling business logic and communication with the service layer."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        """Initializes the AttendancePresenter.

        Args:
            view: The view associated with this presenter.
            main_app: The main application instance.
            status_handler: A callable to handle status messages.
            current_user: The currently logged-in user, if any.
        """
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler

        self._is_editing = False
        self._current_attendance_id: Optional[str] = None
        self._current_user: Optional[User] = current_user

        self._connect_signals()


    def _connect_signals(self) -> None:
        """Connects signals from the view to the appropriate handler methods."""
        pass