from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QDialog
from datetime import date

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.models import User
from src.services.attendance_service import attendance_service
from src.domain.permissions_service import PermissionService
from src.domain.permissions_definitions import Permissions
from src.views.widgets.member_select_dialog import MemberSelectDialog


class AttendancePresenter:
    """Presenter for the AttendanceView, handling business logic and communication with the service layer."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._current_user: Optional[User] = current_user

        self._connect_signals()
        self._load_user_information()
        self._handle_load_attendance()

    def _connect_signals(self) -> None:
        self.view.checkin_requested.connect(self._handle_checkin)
        self.view.checkout_requested.connect(self._handle_checkout)
        self.view.date_changed.connect(self._handle_date_changed)
        self.view.today_requested.connect(self._handle_today)

    def _handle_load_attendance(self, filter_date: Optional[date] = None) -> None:
        """Loads attendance records for the given date (defaults to today)."""
        try:
            if not PermissionService.has_permission(self._current_user, Permissions.ATTENDANCE_READ):
                self._emit_error(ErrorMessages.ATTENDANCE_NO_PERMISSION_READ)
                return

            target_date = filter_date or date.today()
            result = attendance_service.get_attendance_by_date(target_date)

            if result.success:
                self.view.populate_table(result.data)
            else:
                self._emit_error(result.error)
        except Exception as e:
            self.main_app.logger.error(f"Error loading attendance records: {e}")
            self._emit_error(ErrorMessages.ATTENDANCE_UNEXPECTED_ERROR)

    def _handle_checkin(self) -> None:
        """Searches for a member and registers a check-in."""
        term = self.view.get_search_term()
        if not term:
            self._emit_error(ErrorMessages.ATTENDANCE_SEARCH_EMPTY)
            return

        if not PermissionService.has_permission(self._current_user, Permissions.ATTENDANCE_CREATE):
            self._emit_error(ErrorMessages.ATTENDANCE_NO_PERMISSION_CREATE)
            return

        search_result = attendance_service.search_member_for_checkin(term)
        if not search_result.success:
            self._emit_error(ErrorMessages.ATTENDANCE_MEMBER_NOT_FOUND)
            return

        members = search_result.data
        if len(members) == 1:
            member = members[0]
        else:
            dialog = MemberSelectDialog(members, parent=self.view)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            member = dialog.selected_member()

        result = attendance_service.check_in(member.id, self._current_user.id)
        if result.success:
            self._emit_success(ErrorMessages.ATTENDANCE_CHECKIN_SUCCESS)
            self._handle_load_attendance(self.view.get_current_date())
            self.view.clear_search()
        else:
            self._emit_error(ErrorMessages.ATTENDANCE_CHECKIN_FAILED)

    def _handle_checkout(self) -> None:
        """Registers a check-out.

        Two modes:
        1. A row is selected in the table → check out by attendance UUID (original behaviour).
        2. No row selected but search box has text → find the member, then look up
           their open check-in for today and check it out.
        """
        if not PermissionService.has_permission(self._current_user, Permissions.ATTENDANCE_CREATE):
            self._emit_error(ErrorMessages.ATTENDANCE_NO_PERMISSION_CREATE)
            return

        # --- Mode 1: row already selected in the table ---
        attendance_id = self.view.get_selected_attendance_id()
        if attendance_id:
            self._do_checkout(attendance_id)
            return

        # --- Mode 2: search by member code / name ---
        term = self.view.get_search_term()
        if not term:
            self._emit_error(ErrorMessages.ATTENDANCE_NO_SELECTION)
            return

        search_result = attendance_service.search_member_for_checkin(term)
        if not search_result.success:
            self._emit_error(ErrorMessages.ATTENDANCE_MEMBER_NOT_FOUND)
            return

        members = search_result.data
        if len(members) == 1:
            member = members[0]
        else:
            dialog = MemberSelectDialog(members, parent=self.view)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            member = dialog.selected_member()

        open_result = attendance_service.find_open_checkin_for_member(member.id)
        if not open_result.success:
            self._emit_error(ErrorMessages.ATTENDANCE_NO_OPEN_CHECKIN_FOR_MEMBER)
            return

        self._do_checkout(open_result.data.id)

    def _do_checkout(self, attendance_id: str) -> None:
        """Performs the actual check-out call and reloads the table."""
        result = attendance_service.check_out(attendance_id)
        if result.success:
            self._emit_success(ErrorMessages.ATTENDANCE_CHECKOUT_SUCCESS)
            self._handle_load_attendance(self.view.get_current_date())
            self.view.clear_search()
        else:
            self._emit_error(ErrorMessages.ATTENDANCE_CHECKOUT_FAILED)

    def _handle_date_changed(self, qdate) -> None:
        """Reloads the table when the date filter changes."""
        self._handle_load_attendance(qdate.toPyDate())

    def _handle_today(self) -> None:
        """Resets the date filter to today and reloads the table."""
       
        self.view.date_filter.setDate(QDate.currentDate())
        # _handle_load_attendance is triggered automatically via dateChanged signal

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role": self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_warning(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.WARNING)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)
