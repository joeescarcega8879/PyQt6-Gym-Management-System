from __future__ import annotations
from typing import Optional
from PyQt6.QtWidgets import QDialog

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.models import User, MembershipPlan
from src.models.enums import MembershipStatus
from src.services.membership_service import membership_service
from src.services.attendance_service import attendance_service
from src.domain.permissions_service import PermissionService
from src.domain.permissions_definitions import Permissions
from src.views.widgets.member_select_dialog import MemberSelectDialog


class MembershipPresenter:
    """Presenter for the MembershipView, coordinating plans and memberships logic."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._current_user: Optional[User] = current_user
        self._selected_plan_id: Optional[str] = None

        self._connect_signals()
        self._load_user_information()
        self._handle_load_plans()
        self._handle_load_memberships()

    def _connect_signals(self) -> None:
        self.view.save_plan_requested.connect(self._handle_save_plan)
        self.view.new_plan_requested.connect(self._handle_new_plan)
        self.view.cancel_plan_requested.connect(self._handle_cancel_plan)
        self.view.toggle_status_requested.connect(self._handle_toggle_status)
        self.view.plan_selected.connect(self._handle_plan_selected)

        self.view.filter_requested.connect(self._handle_load_memberships)
        self.view.assign_requested.connect(self._handle_assign)
        self.view.suspend_requested.connect(self._handle_suspend)
        self.view.cancel_membership_requested.connect(self._handle_cancel_membership)
        self.view.reactivate_requested.connect(self._handle_reactivate)

    # ------------------------------------------------------------------ #
    # Plans tab
    # ------------------------------------------------------------------ #

    def _handle_load_plans(self) -> None:
        result = membership_service.get_all_plans(include_inactive=True)
        if result.success:
            self.view.populate_plans_table(result.data)
            self.view.populate_plan_combo([p for p in result.data if p.is_active])
        else:
            self._emit_error(result.error)

    def _handle_plan_selected(self) -> None:
        plan_id = self.view.get_selected_plan_id()
        if not plan_id:
            return
        result = membership_service.get_plan_by_id(plan_id)
        if result.success:
            self._selected_plan_id = plan_id
            self.view.set_plan_form_data(result.data)
        else:
            self._emit_error(result.error)

    def _handle_save_plan(self) -> None:
        if self._selected_plan_id:
            self._update_plan()
        else:
            self._create_plan()

    def _create_plan(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.PLANS_CREATE):
            self._emit_error(ErrorMessages.PLANS_NO_PERMISSION_CREATE)
            return
        plan = self._build_plan_from_form()
        result = membership_service.create_plan(plan)
        if result.success:
            self._emit_success(ErrorMessages.PLANS_CREATED)
            self._selected_plan_id = None
            self.view.clear_plan_form()
            self._handle_load_plans()
        else:
            self._emit_error(result.error or ErrorMessages.PLANS_CREATION_FAILED)

    def _update_plan(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.PLANS_UPDATE):
            self._emit_error(ErrorMessages.PLANS_NO_PERMISSION_UPDATE)
            return
        plan = self._build_plan_from_form(plan_id=self._selected_plan_id)
        result = membership_service.update_plan(plan)
        if result.success:
            self._emit_success(ErrorMessages.PLANS_UPDATED)
            self._selected_plan_id = None
            self.view.clear_plan_form()
            self._handle_load_plans()
        else:
            self._emit_error(result.error or ErrorMessages.PLANS_UPDATE_FAILED)

    def _handle_new_plan(self) -> None:
        self._selected_plan_id = None
        self.view.clear_plan_form()

    def _handle_cancel_plan(self) -> None:
        self._selected_plan_id = None
        self.view.clear_plan_form()

    def _handle_toggle_status(self) -> None:
        plan_id = self.view.get_selected_plan_id()
        if not plan_id:
            self._emit_error(ErrorMessages.PLANS_NO_SELECTION)
            return
        if not PermissionService.has_permission(self._current_user, Permissions.PLANS_UPDATE):
            self._emit_error(ErrorMessages.PLANS_NO_PERMISSION_UPDATE)
            return
        plan_result = membership_service.get_plan_by_id(plan_id)
        if not plan_result.success:
            self._emit_error(ErrorMessages.PLANS_UNEXPECTED_ERROR)
            return
        result = membership_service.toggle_plan_status(plan_id, not plan_result.data.is_active)
        if result.success:
            self._emit_success(ErrorMessages.PLANS_STATUS_UPDATED)
            self._handle_load_plans()
        else:
            self._emit_error(ErrorMessages.PLANS_STATUS_UPDATE_FAILED)

    # ------------------------------------------------------------------ #
    # Memberships tab
    # ------------------------------------------------------------------ #

    def _handle_load_memberships(self) -> None:
        try:
            if not PermissionService.has_permission(self._current_user, Permissions.MEMBERSHIPS_READ):
                self._emit_error(ErrorMessages.MEMBERSHIPS_NO_PERMISSION_READ)
                return

            expiring_days = self.view.get_expiring_days()
            search_term   = self.view.get_filter_search_term()

            if expiring_days is not None:
                result = membership_service.get_memberships(
                    expiring_days=expiring_days,
                    search_term=search_term,
                )
            else:
                result = membership_service.get_memberships(
                    status=self._parse_filter_status(),
                    search_term=search_term,
                    date_from=self.view.get_date_from(),
                    date_to=self.view.get_date_to(),
                )

            if result.success:
                self.view.populate_memberships_table(result.data)
            else:
                self._emit_error(result.error)
        except Exception as e:
            self.main_app.logger.error(f"Error loading memberships: {e}")
            self._emit_error(ErrorMessages.MEMBERSHIPS_UNEXPECTED_ERROR)

    def _handle_assign(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.MEMBERSHIPS_CREATE):
            self._emit_error(ErrorMessages.MEMBERSHIPS_NO_PERMISSION_CREATE)
            return

        term = self.view.get_assign_search_term()
        if not term:
            self._emit_error(ErrorMessages.MEMBERSHIPS_MEMBER_NOT_FOUND)
            return

        search_result = attendance_service.search_member_for_checkin(term)
        if not search_result.success:
            self._emit_error(ErrorMessages.MEMBERSHIPS_MEMBER_NOT_FOUND)
            return

        members = search_result.data
        if len(members) == 1:
            member = members[0]
        else:
            dialog = MemberSelectDialog(members, parent=self.view)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            member = dialog.selected_member()

        plan_id = self.view.get_assign_plan_id()
        if not plan_id:
            self._emit_error(ErrorMessages.MEMBERSHIPS_PLAN_NOT_FOUND)
            return

        result = membership_service.assign_membership(
            member_id=member.id,
            plan_id=plan_id,
            start_date=self.view.get_start_date(),
            notes=self.view.get_assign_notes(),
            created_by=self._current_user.id if self._current_user else None,
        )

        if result.success:
            self._emit_success(ErrorMessages.MEMBERSHIPS_ASSIGNED)
            self.view.clear_assign_form()
            self._handle_load_memberships()
        else:
            error = result.error or ""
            if "already has an active" in error.lower():
                self._emit_error(ErrorMessages.MEMBERSHIPS_ALREADY_ACTIVE)
            else:
                self._emit_error(ErrorMessages.MEMBERSHIPS_ASSIGN_FAILED)

    def _handle_suspend(self) -> None:
        self._change_membership_status(MembershipStatus.SUSPENDED)

    def _handle_cancel_membership(self) -> None:
        self._change_membership_status(MembershipStatus.CANCELLED)

    def _handle_reactivate(self) -> None:
        self._change_membership_status(MembershipStatus.ACTIVE)

    def _change_membership_status(self, new_status: MembershipStatus) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.MEMBERSHIPS_UPDATE):
            self._emit_error(ErrorMessages.MEMBERSHIPS_NO_PERMISSION_UPDATE)
            return

        membership_id = self.view.get_selected_membership_id()
        if not membership_id:
            self._emit_error(ErrorMessages.MEMBERSHIPS_NO_SELECTION)
            return

        result = membership_service.change_status(membership_id, new_status)
        if result.success:
            self._emit_success(ErrorMessages.MEMBERSHIPS_STATUS_UPDATED)
            self._handle_load_memberships()
        else:
            if result.is_not_found:
                self._emit_error(ErrorMessages.MEMBERSHIPS_UNEXPECTED_ERROR)
            else:
                self._emit_error(result.error or ErrorMessages.MEMBERSHIPS_INVALID_TRANSITION)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _parse_filter_status(self) -> Optional[MembershipStatus]:
        status_str = self.view.get_filter_status()
        if status_str:
            try:
                return MembershipStatus(status_str)
            except ValueError:
                return None
        return None

    def _build_plan_from_form(self, plan_id: Optional[str] = None) -> MembershipPlan:
        return MembershipPlan(
            id=plan_id,
            name=self.view.get_plan_name(),
            description=self.view.get_plan_description(),
            duration_days=self.view.get_duration_days(),
            price=self.view.get_price(),
            has_class_access=self.view.get_has_class_access(),
            max_classes_per_week=self.view.get_max_classes(),
            is_active=self.view.get_is_active(),
        )

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role": self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_info(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.INFO)
