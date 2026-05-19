from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QDialog

from src.domain.permissions_definitions import Permissions
from src.domain.permissions_service import PermissionService
from src.models import User, Class, ClassSchedule
from src.models.enums import DifficultyLevel, EnrollmentStatus
from src.services.class_service import class_service
from src.services.attendance_service import attendance_service  # reuse search_member_for_checkin
from src.utils.error_messages import ErrorMessages
from src.utils.status_type import StatusType
from src.views.widgets.member_select_dialog import MemberSelectDialog


class ClassPresenter:
    """Coordinates the ClassView with ClassService. Handles all three tabs."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view           = view
        self.main_app       = main_app
        self.status_handler = status_handler
        self._current_user  = current_user

        # Internal state
        self._selected_class_id:    Optional[str] = None
        self._selected_schedule_id: Optional[str] = None

        self._connect_signals()
        self._load_user_information()
        self._handle_load_classes()
        self._handle_load_schedules()
        self._handle_load_enrollments()

    # ================================================================== #
    # Signal wiring
    # ================================================================== #

    def _connect_signals(self) -> None:
        v = self.view

        # Tab 1 — Classes
        v.save_class_requested.connect(self._handle_save_class)
        v.new_class_requested.connect(self._handle_new_class)
        v.cancel_class_requested.connect(self._handle_cancel_class)
        v.toggle_class_status_requested.connect(self._handle_toggle_class_status)
        v.class_selected.connect(self._handle_class_selected)

        # Tab 2 — Schedules
        v.filter_schedules_requested.connect(self._handle_filter_schedules)
        v.clear_schedule_filters_requested.connect(self._handle_clear_schedule_filters)
        v.save_schedule_requested.connect(self._handle_save_schedule)
        v.new_schedule_requested.connect(self._handle_new_schedule)
        v.toggle_schedule_status_requested.connect(self._handle_toggle_schedule_status)
        v.schedule_selected.connect(self._handle_schedule_selected)

        # Tab 3 — Enrollments
        v.filter_enrollments_requested.connect(self._handle_filter_enrollments)
        v.clear_enrollment_filters_requested.connect(self._handle_clear_enrollment_filters)
        v.enroll_requested.connect(self._handle_enroll)
        v.mark_attended_requested.connect(self._handle_mark_attended)
        v.mark_absent_requested.connect(self._handle_mark_absent)
        v.cancel_enrollment_requested.connect(self._handle_cancel_enrollment)

    # ================================================================== #
    # Tab 1 — Classes
    # ================================================================== #

    def _handle_load_classes(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.CLASSES_READ):
            self._emit_error(ErrorMessages.CLASSES_NO_PERMISSION_READ)
            return

        result = class_service.get_all_classes(include_inactive=True)
        if result.success:
            self.view.populate_classes_table(result.data)
            self.view.populate_class_combos([c for c in result.data if c.is_active])
            # Also refresh schedule combo for enrollments
            schedules_result = class_service.get_schedules(include_inactive=False)
            if schedules_result.success:
                self.view.populate_schedule_combo_for_enrollment(schedules_result.data)

    def _handle_class_selected(self) -> None:
        class_id = self.view.get_selected_class_id()
        if not class_id:
            return
        self._selected_class_id = class_id
        result = class_service.get_class_by_id(class_id)
        if result.success:
            c = result.data
            self.view.set_class_form_data({
                "name":             c.name,
                "description":      c.description,
                "duration_minutes": c.duration_minutes,
                "max_capacity":     c.max_capacity,
                "difficulty_level": c.difficulty_level,
                "is_active":        c.is_active,
            })

    def _handle_new_class(self) -> None:
        self._selected_class_id = None
        self.view.clear_class_form()
        self.view.classes_table.clearSelection()

    def _handle_cancel_class(self) -> None:
        self._selected_class_id = None
        self.view.clear_class_form()
        self.view.classes_table.clearSelection()

    def _handle_save_class(self) -> None:
        if self._selected_class_id:
            self._update_class()
        else:
            self._create_class()

    def _create_class(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.CLASSES_CREATE):
            self._emit_error(ErrorMessages.CLASSES_NO_PERMISSION_CREATE)
            return

        gym_class = Class(
            name=self.view.get_class_name(),
            description=self.view.get_class_description(),
            duration_minutes=self.view.get_duration_minutes(),
            max_capacity=self.view.get_max_capacity(),
            difficulty_level=self.view.get_difficulty_level(),
            is_active=self.view.get_class_is_active(),
        )
        result = class_service.create_class(gym_class)
        if result.success:
            self._emit_success(ErrorMessages.CLASSES_CREATED)
            self._handle_new_class()
            self._handle_load_classes()
        else:
            self._emit_error(result.error or ErrorMessages.CLASSES_CREATION_FAILED)

    def _update_class(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.CLASSES_UPDATE):
            self._emit_error(ErrorMessages.CLASSES_NO_PERMISSION_UPDATE)
            return

        gym_class = Class(
            id=self._selected_class_id,
            name=self.view.get_class_name(),
            description=self.view.get_class_description(),
            duration_minutes=self.view.get_duration_minutes(),
            max_capacity=self.view.get_max_capacity(),
            difficulty_level=self.view.get_difficulty_level(),
            is_active=self.view.get_class_is_active(),
        )
        result = class_service.update_class(gym_class)
        if result.success:
            self._emit_success(ErrorMessages.CLASSES_UPDATED)
            self._handle_load_classes()
        else:
            self._emit_error(result.error or ErrorMessages.CLASSES_UPDATE_FAILED)

    def _handle_toggle_class_status(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.CLASSES_UPDATE):
            self._emit_error(ErrorMessages.CLASSES_NO_PERMISSION_UPDATE)
            return

        class_id = self.view.get_selected_class_id()
        if not class_id:
            self._emit_error(ErrorMessages.CLASSES_NO_SELECTION)
            return

        result_get = class_service.get_class_by_id(class_id)
        if not result_get.success:
            self._emit_error(ErrorMessages.CLASSES_NO_SELECTION)
            return

        new_status = not result_get.data.is_active
        result = class_service.toggle_class_status(class_id, new_status)
        if result.success:
            self._emit_success(ErrorMessages.CLASSES_STATUS_UPDATED)
            self._handle_load_classes()
        else:
            self._emit_error(result.error or ErrorMessages.CLASSES_STATUS_UPDATE_FAILED)

    # ================================================================== #
    # Tab 2 — Schedules
    # ================================================================== #

    def _handle_load_schedules(
        self,
        class_id: Optional[str] = None,
        day_of_week: Optional[int] = None,
        include_inactive: bool = True,
    ) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.SCHEDULES_READ):
            return

        result = class_service.get_schedules(
            class_id=class_id,
            day_of_week=day_of_week,
            include_inactive=include_inactive,
        )
        if result.success:
            self.view.populate_schedules_table(result.data)

    def _handle_filter_schedules(self) -> None:
        class_id        = self.view.get_schedule_filter_class_id()
        day             = self.view.get_schedule_filter_day()
        show_inactive   = self.view.get_show_inactive_schedules()
        self._handle_load_schedules(
            class_id=class_id,
            day_of_week=day,
            include_inactive=show_inactive,
        )

    def _handle_clear_schedule_filters(self) -> None:
        self.view.combo_filter_class.setCurrentIndex(0)
        self.view.combo_filter_day.setCurrentIndex(0)
        self.view.check_show_inactive_schedules.setChecked(False)
        self._handle_load_schedules(include_inactive=False)

    def _handle_schedule_selected(self) -> None:
        schedule_id = self.view.get_selected_schedule_id()
        if not schedule_id:
            return
        self._selected_schedule_id = schedule_id
        result = class_service.get_schedule_by_id(schedule_id)
        if result.success:
            s = result.data
            self.view.set_schedule_form_data({
                "class_id":    s.class_id,
                "day_of_week": s.day_of_week,
                "start_time":  s.start_time,
                "end_time":    s.end_time,
                "room":        s.room,
            })

    def _handle_new_schedule(self) -> None:
        self._selected_schedule_id = None
        self.view.clear_schedule_form()
        self.view.schedules_table.clearSelection()

    def _handle_save_schedule(self) -> None:
        if self._selected_schedule_id:
            self._update_schedule()
        else:
            self._create_schedule()

    def _create_schedule(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.SCHEDULES_CREATE):
            self._emit_error(ErrorMessages.SCHEDULES_NO_PERMISSION_CREATE)
            return

        class_id = self.view.get_sched_class_id()
        if not class_id:
            self._emit_error(ErrorMessages.SCHEDULES_CLASS_REQUIRED)
            return

        schedule = ClassSchedule(
            class_id=class_id,
            day_of_week=self.view.get_sched_day_of_week(),
            start_time=self.view.get_sched_start_time(),
            end_time=self.view.get_sched_end_time(),
            room=self.view.get_sched_room(),
            is_active=True,
        )
        result = class_service.create_schedule(schedule)
        if result.success:
            self._emit_success(ErrorMessages.SCHEDULES_CREATED)
            self._handle_new_schedule()
            self._handle_load_schedules()
            # Refresh enrollment schedule combo
            schedules_result = class_service.get_schedules(include_inactive=False)
            if schedules_result.success:
                self.view.populate_schedule_combo_for_enrollment(schedules_result.data)
        else:
            self._emit_error(result.error or ErrorMessages.SCHEDULES_CREATION_FAILED)

    def _update_schedule(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.SCHEDULES_UPDATE):
            self._emit_error(ErrorMessages.SCHEDULES_NO_PERMISSION_UPDATE)
            return

        class_id = self.view.get_sched_class_id()
        if not class_id:
            self._emit_error(ErrorMessages.SCHEDULES_CLASS_REQUIRED)
            return

        schedule = ClassSchedule(
            id=self._selected_schedule_id,
            class_id=class_id,
            day_of_week=self.view.get_sched_day_of_week(),
            start_time=self.view.get_sched_start_time(),
            end_time=self.view.get_sched_end_time(),
            room=self.view.get_sched_room(),
            is_active=True,
        )
        result = class_service.update_schedule(schedule)
        if result.success:
            self._emit_success(ErrorMessages.SCHEDULES_UPDATED)
            self._handle_load_schedules()
        else:
            self._emit_error(result.error or ErrorMessages.SCHEDULES_UPDATE_FAILED)

    def _handle_toggle_schedule_status(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.SCHEDULES_UPDATE):
            self._emit_error(ErrorMessages.SCHEDULES_NO_PERMISSION_UPDATE)
            return

        schedule_id = self.view.get_selected_schedule_id()
        if not schedule_id:
            self._emit_error(ErrorMessages.SCHEDULES_NO_SELECTION)
            return

        result_get = class_service.get_schedule_by_id(schedule_id)
        if not result_get.success:
            self._emit_error(ErrorMessages.SCHEDULES_NO_SELECTION)
            return

        new_status = not result_get.data.is_active
        result = class_service.toggle_schedule_status(schedule_id, new_status)
        if result.success:
            self._emit_success(ErrorMessages.SCHEDULES_STATUS_UPDATED)
            self._handle_load_schedules()
        else:
            self._emit_error(result.error or ErrorMessages.SCHEDULES_STATUS_UPDATE_FAILED)

    # ================================================================== #
    # Tab 3 — Enrollments
    # ================================================================== #

    def _handle_load_enrollments(
        self,
        search_term: Optional[str] = None,
        status_value: Optional[str] = None,
        class_date=None,
    ) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.ENROLLMENTS_READ):
            return

        status = None
        if status_value:
            try:
                status = EnrollmentStatus(status_value)
            except ValueError:
                pass

        result = class_service.get_enrollments(
            class_date=class_date,
            status=status,
            search_term=search_term,
        )
        if result.success:
            self.view.populate_enrollments_table(result.data)

    def _handle_filter_enrollments(self) -> None:
        self._handle_load_enrollments(
            search_term=self.view.get_enrollment_search_term(),
            status_value=self.view.get_enrollment_status_filter(),
            class_date=self.view.get_enrollment_date_filter(),
        )

    def _handle_clear_enrollment_filters(self) -> None:
        self.view.clear_enrollment_filters()
        self._handle_load_enrollments()

    def _handle_enroll(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.ENROLLMENTS_CREATE):
            self._emit_error(ErrorMessages.ENROLLMENTS_NO_PERMISSION_CREATE)
            return

        # Search member
        search_term = self.view.get_enroll_member_search()
        if not search_term:
            self._emit_error(ErrorMessages.ENROLLMENTS_MEMBER_NOT_FOUND)
            return

        search_result = attendance_service.search_member_for_checkin(search_term)
        if not search_result.success:
            self._emit_error(ErrorMessages.ENROLLMENTS_MEMBER_NOT_FOUND)
            return

        members = search_result.data
        if len(members) == 1:
            member = members[0]
        else:
            dialog = MemberSelectDialog(members, parent=self.view)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            member = dialog.selected_member()
            if not member:
                return

        # Get schedule
        schedule_id = self.view.get_enroll_schedule_id()
        if not schedule_id:
            self._emit_error(ErrorMessages.ENROLLMENTS_SCHEDULE_REQUIRED)
            return

        class_date = self.view.get_enroll_class_date()
        notes      = self.view.get_enroll_notes()
        created_by = self._current_user.id if self._current_user else None

        result = class_service.enroll_member(
            schedule_id=schedule_id,
            member_id=member.id,
            class_date=class_date,
            notes=notes,
            created_by=created_by,
        )
        if result.success:
            self._emit_success(ErrorMessages.ENROLLMENTS_ENROLLED)
            self._handle_load_enrollments()
        else:
            self._emit_error(result.error or ErrorMessages.ENROLLMENTS_ENROLL_FAILED)

    def _handle_mark_attended(self) -> None:
        self._change_enrollment_status(EnrollmentStatus.ATTENDED)

    def _handle_mark_absent(self) -> None:
        self._change_enrollment_status(EnrollmentStatus.ABSENT)

    def _handle_cancel_enrollment(self) -> None:
        self._change_enrollment_status(EnrollmentStatus.CANCELLED)

    def _change_enrollment_status(self, new_status: EnrollmentStatus) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.ENROLLMENTS_UPDATE):
            self._emit_error(ErrorMessages.ENROLLMENTS_NO_PERMISSION_UPDATE)
            return

        enrollment_id = self.view.get_selected_enrollment_id()
        if not enrollment_id:
            self._emit_error(ErrorMessages.ENROLLMENTS_NO_SELECTION)
            return

        result = class_service.update_enrollment_status(enrollment_id, new_status)
        if result.success:
            self._emit_success(ErrorMessages.ENROLLMENTS_STATUS_UPDATED)
            self._handle_load_enrollments()
        else:
            self._emit_error(result.error or ErrorMessages.ENROLLMENTS_STATUS_UPDATE_FAILED)

    # ================================================================== #
    # Helpers
    # ================================================================== #

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role":     self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_info(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.INFO)
