from __future__ import annotations
from typing import Optional

from src.models import User
from src.services.dashboard_service import dashboard_service
from src.domain.permissions_service import PermissionService
from src.domain.permissions_definitions import Permissions
from src.utils.error_messages import ErrorMessages
from src.utils.status_type import StatusType


class DashboardPresenter:
    """Coordinates DashboardView with DashboardService."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._current_user = current_user

        self._connect_signals()
        self._load_user_information()
        self._handle_refresh()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #

    def _connect_signals(self) -> None:
        self.view.refresh_requested.connect(self._handle_refresh)

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role": self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    # ------------------------------------------------------------------ #
    # Signal handlers
    # ------------------------------------------------------------------ #

    def _handle_refresh(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.DASHBOARD_READ):
            self._emit_error(ErrorMessages.DASHBOARD_NO_PERMISSION_READ)
            return

        try:
            result = dashboard_service.get_summary()
            if result.success:
                self.view.set_summary(result.data)
            else:
                self._emit_error(result.error or ErrorMessages.DASHBOARD_LOAD_FAILED)
        except Exception as e:
            self.main_app.logger.error(f"Error loading dashboard: {e}")
            self._emit_error(ErrorMessages.DASHBOARD_UNEXPECTED_ERROR)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_info(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.INFO)
