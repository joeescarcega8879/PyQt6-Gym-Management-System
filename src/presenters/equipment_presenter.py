from __future__ import annotations

import logging
from typing import Optional

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.models import User, Equipment
from src.models.enums import MaintenanceType, EquipmentCondition
from src.services.equipment_service import equipment_service

from src.domain.permissions import Permissions
from src.domain.permissions_service import PermissionService

logger = logging.getLogger(__name__)


class EquipmentPresenter:
    """Presenter for the EquipmentView, coordinating equipment and maintenance logic."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._current_user: Optional[User] = current_user
        self._selected_equipment_id: Optional[str] = None

        self._connect_signals()
        self._load_user_information()
        self._handle_load_equipment()
        self._handle_load_maintenance()

    def _connect_signals(self) -> None:
        # Tab 1 — Equipment signals
        self.view.save_requested.connect(self._handle_save)
        self.view.new_requested.connect(self._handle_new)
        self.view.cancel_requested.connect(self._handle_cancel)
        self.view.equipment_selected.connect(self._handle_equipment_selected)
        self.view.search_requested.connect(self._handle_search)
        self.view.clear_action_requested.connect(self._handle_load_equipment)
        self.view.show_inactive_requested.connect(self._handle_load_equipment)

        # Tab 2 — Maintenance signals
        self.view.filter_maintenance_requested.connect(self._handle_load_maintenance)
        self.view.log_maintenance_requested.connect(self._handle_log_maintenance)

    # ------------------------------------------------------------------ #
    # Equipment tab
    # ------------------------------------------------------------------ #

    def _handle_load_equipment(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.EQUIPMENT_READ):
            self._emit_error(ErrorMessages.EQUIPMENT_NO_PERMISSION_READ)
            return

        include_inactive = self.view.check_show_inactives.isChecked()
        result = equipment_service.get_all_equipment(include_inactive=include_inactive)

        if result.success:
            self.view.populate_table(result.data)
            active_equipment = [e for e in result.data if e.is_active]
            self.view.populate_equipment_combos(active_equipment)
        else:
            logger.error(f"Load all equipment failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_search(self, term: str) -> None:
        current_search_option = self.view.get_selected_search_option()

        if not term or not term.strip():
            self._handle_load_equipment()
            return

        result = equipment_service.search_equipment(term, column=current_search_option)

        if result.success:
            self.view.populate_table(result.data)
        else:
            logger.warning(f"Equipment search failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_equipment_selected(self) -> None:
        equipment_id = self.view.get_selected_equipment_id()
        if not equipment_id:
            return
        result = equipment_service.get_equipment_by_id(equipment_id)
        if result.success:
            self._selected_equipment_id = equipment_id
            self.view.set_form_data(self._equipment_to_form_dict(result.data))
        else:
            self._emit_error(result.error)

    def _handle_save(self) -> None:
        if self._selected_equipment_id:
            self._update_equipment()
        else:
            self._create_equipment()

    def _create_equipment(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.EQUIPMENT_CREATE):
            self._emit_error(ErrorMessages.EQUIPMENT_NO_PERMISSION_CREATE)
            return

        equipment = self._build_equipment_from_form()
        result = equipment_service.create_equipment(equipment)

        if result.success:
            self._emit_success(ErrorMessages.EQUIPMENT_CREATED)
            self.view.clear_form()
            self._handle_load_equipment()
        else:
            self._emit_error(result.error or ErrorMessages.EQUIPMENT_CREATION_FAILED)

    def _update_equipment(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.EQUIPMENT_UPDATE):
            self._emit_error(ErrorMessages.EQUIPMENT_NO_PERMISSION_UPDATE)
            return

        equipment = self._build_equipment_from_form(equipment_id=self._selected_equipment_id)
        result = equipment_service.update_equipment(equipment)

        if result.success:
            self._emit_success(ErrorMessages.EQUIPMENT_UPDATED)
            self._selected_equipment_id = None
            self.view.clear_form()
            self._handle_load_equipment()
        else:
            self._emit_error(result.error or ErrorMessages.EQUIPMENT_UPDATE_FAILED)

    def _handle_new(self) -> None:
        self._selected_equipment_id = None
        self.view.clear_form()

    def _handle_cancel(self) -> None:
        self._selected_equipment_id = None
        self.view.clear_form()
        self._emit_success(ErrorMessages.EQUIPMENT_OPERATION_CANCELLED)

    # ------------------------------------------------------------------ #
    # Maintenance tab
    # ------------------------------------------------------------------ #

    def _handle_load_maintenance(self) -> None:
        try:
            if not PermissionService.has_permission(self._current_user, Permissions.MAINTENANCE_READ):
                self._emit_error(ErrorMessages.MAINTENANCE_NO_PERMISSION_READ)
                return

            result = equipment_service.get_maintenance_records(
                equipment_id=self.view.get_filter_equipment_id(),
                maintenance_type=self._parse_maintenance_type(self.view.get_filter_maintenance_type()),
                date_from=self.view.get_filter_date_from(),
                date_to=self.view.get_filter_date_to(),
            )

            if result.success:
                self.view.populate_maintenance_table(result.data)
            else:
                self._emit_error(result.error)
        except Exception as e:
            self.main_app.logger.error(f"Error loading maintenance records: {e}")
            self._emit_error(ErrorMessages.MAINTENANCE_UNEXPECTED_ERROR)

    def _handle_log_maintenance(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.MAINTENANCE_CREATE):
            self._emit_error(ErrorMessages.MAINTENANCE_NO_PERMISSION_CREATE)
            return

        equipment_id = self.view.get_log_equipment_id()
        if not equipment_id:
            self._emit_error(ErrorMessages.MAINTENANCE_EQUIPMENT_REQUIRED)
            return

        result = equipment_service.log_maintenance(
            equipment_id=equipment_id,
            maintenance_date=self.view.get_log_maintenance_date(),
            maintenance_type=MaintenanceType(self.view.get_log_maintenance_type()),
            description=self.view.get_log_description(),
            cost=self.view.get_log_cost(),
            performed_by=self.view.get_log_performed_by(),
            next_maintenance_date=self.view.get_log_next_maintenance_date(),
            created_by=self._current_user.id if self._current_user else None,
        )

        if result.success:
            self._emit_success(ErrorMessages.MAINTENANCE_LOGGED)
            self.view.clear_log_form()
            self._handle_load_maintenance()
        else:
            self._emit_error(result.error or ErrorMessages.MAINTENANCE_LOG_FAILED)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_maintenance_type(value: Optional[str]) -> Optional[MaintenanceType]:
        if not value:
            return None
        try:
            return MaintenanceType(value)
        except ValueError:
            return None

    @staticmethod
    def _equipment_to_form_dict(equipment: Equipment) -> dict:
        return {
            "name": equipment.name,
            "category": equipment.category,
            "brand": equipment.brand,
            "model": equipment.model,
            "serial_number": equipment.serial_number,
            "purchase_date": equipment.purchase_date.strftime("%Y-%m-%d") if equipment.purchase_date else None,
            "purchase_price": equipment.purchase_price,
            "condition": equipment.condition.value,
            "location": equipment.location,
            "notes": equipment.notes,
            "is_active": equipment.is_active,
        }

    def _build_equipment_from_form(self, equipment_id: Optional[str] = None) -> Equipment:
        data = self.view.get_form_data()
        return Equipment(
            id=equipment_id,
            name=data.get('name', '').strip(),
            category=data.get('category') or None,
            brand=data.get('brand') or None,
            model=data.get('model') or None,
            serial_number=data.get('serial_number') or None,
            purchase_date=data.get('purchase_date'),
            purchase_price=data.get('purchase_price'),
            condition=EquipmentCondition(data.get('condition', 'good')),
            location=data.get('location') or None,
            notes=data.get('notes') or None,
            is_active=data.get('is_active', True),
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
