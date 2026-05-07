from __future__ import annotations
from typing import Optional
from PyQt6.QtWidgets import QDialog

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.models import User
from src.models.enums import PaymentMethod, PaymentStatus
from src.models.models import Payment
from src.services.payment_service import payment_service
from src.services.attendance_service import attendance_service
from src.domain.permissions_service import PermissionService
from src.domain.permissions_definitions import Permissions
from src.views.widgets.member_select_dialog import MemberSelectDialog


class PaymentPresenter:
    """Presenter for the PaymentView, handling business logic and communication with the service layer."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._current_user: Optional[User] = current_user

        self._connect_signals()
        self._load_user_information()
        self._handle_load_payments()

    def _connect_signals(self) -> None:
        self.view.save_requested.connect(self._handle_save)
        self.view.new_requested.connect(self._handle_new)
        self.view.filter_requested.connect(self._handle_load_payments)

    def _handle_load_payments(self) -> None:
        """Loads payments with current filters applied."""
        try:
            if not PermissionService.has_permission(self._current_user, Permissions.PAYMENTS_READ):
                self._emit_error(ErrorMessages.PAYMENTS_NO_PERMISSION_READ)
                return

            status = self._parse_filter_status()
            method = self._parse_filter_method()

            result = payment_service.get_payments(
                status=status,
                payment_method=method,
                date_from=self.view.get_date_from(),
                date_to=self.view.get_date_to(),
            )

            if result.success:
                self.view.populate_table(result.data)
            else:
                self._emit_error(result.error)
        except Exception as e:
            self.main_app.logger.error(f"Error loading payments: {e}")
            self._emit_error(ErrorMessages.PAYMENTS_UNEXPECTED_ERROR)

    def _handle_save(self) -> None:
        """Creates a new payment record."""
        if not PermissionService.has_permission(self._current_user, Permissions.PAYMENTS_CREATE):
            self._emit_error(ErrorMessages.PAYMENTS_NO_PERMISSION_CREATE)
            return

        term = self.view.get_search_term()
        if not term:
            self._emit_error(ErrorMessages.PAYMENTS_MEMBER_NOT_FOUND)
            return

        search_result = attendance_service.search_member_for_checkin(term)
        if not search_result.success:
            self._emit_error(ErrorMessages.PAYMENTS_MEMBER_NOT_FOUND)
            return

        members = search_result.data
        if len(members) == 1:
            member = members[0]
        else:
            dialog = MemberSelectDialog(members, parent=self.view)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            member = dialog.selected_member()

        amount = self.view.get_amount()
        if amount <= 0:
            self._emit_error(ErrorMessages.PAYMENTS_INVALID_AMOUNT)
            return

        method_str = self.view.get_payment_method()
        method = PaymentMethod(method_str)

        payment = Payment(
            member_id=member.id,
            amount=amount,
            payment_method=method,
        )

        result = payment_service.create_payment(payment, self._current_user.id)
        if result.success:
            self._emit_success(ErrorMessages.PAYMENTS_CREATED)
            self.view.clear_form()
            self._handle_load_payments()
        else:
            self._emit_error(ErrorMessages.PAYMENTS_CREATION_FAILED)

    def _handle_new(self) -> None:
        """Clears the form for a new payment."""
        self.view.clear_form()

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role": self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    def _parse_filter_status(self) -> Optional[PaymentStatus]:
        status_str = self.view.get_filter_status()
        if status_str:
            try:
                return PaymentStatus(status_str)
            except ValueError:
                return None
        return None

    def _parse_filter_method(self) -> Optional[PaymentMethod]:
        method_str = self.view.get_filter_method()
        if method_str:
            try:
                return PaymentMethod(method_str)
            except ValueError:
                return None
        return None

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)
