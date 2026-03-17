from __future__ import annotations

import logging
from typing import Optional

from src.utils.status_type import StatusType
from src.models import Member, Gender, User
from src.services.member_service import member_service

from src.domain.permissions import Permissions
from src.domain.permissions_service import PermissionService

logger = logging.getLogger(__name__)


class MemberPresenter:
    """
    Handles all user interactions originating from the member management view.
    The presenter is the only component that knows both the view contract
    and the service layer — neither the view nor the service knows each other.
    """

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None):
        """
        Args:
            view:         The member view instance. Must satisfy the view contract
                          described at the bottom of this module.
            main_app:     The main application instance.
            status_handler: The status handler for displaying messages.
            current_user: The logged-in User object, used for permission checks
                          and audit fields (created_by / updated_by).
        """
        self._is_editing = False
        self._current_member_id: Optional[str] = None
        self._current_user: Optional[User] = current_user

        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._connect_signals()
        self._handle_load_all()  # Load all members when the view opens

    def _connect_signals(self):
        """Connects view signals to their corresponding handler methods."""
        self.view.create_requested.connect(self._handle_create)
        self.view.update_requested.connect(self._handle_update)
        # self.view.search_requested.connect(self._handle_search)

    def _handle_load_all(self):
        """
        Loads all active members and populates the view table.
        Triggered when the view first opens or requests a full refresh.
        """
        result = member_service.get_all_members()

        if result:
            self.view.populate_table(result.data)
        else:
            logger.error(f"Load all members failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_search(self, term: str):
        """
        Searches for members matching the given term and updates the table.

        Args:
            term: Partial string to match against name or email.
        """
        if not term or not term.strip():
            # Empty search → show all members instead
            self._handle_load_all()
            return

        result = member_service.search_members(term)

        if result:
            self.view.populate_table(result.data)
        else:
            logger.warning(f"Member search failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_create(self):
        """
        Reads form data from the view, builds a Member instance and
        delegates creation to the service.
        On success: clears the form and refreshes the table.
        On failure: surfaces the error message to the view.
        """

        data = self.view.get_form_data() or {}

        try:
            if self._is_editing:
                if self._current_member_id is None:
                    self._emit_error("Member ID is required for updates")
                    return
                
                if not PermissionService.has_permission(self._current_user, Permissions.MEMBERS_UPDATE):
                    self._emit_error("You do not have permission to update members")
                    return
                
                member = self._build_member_from_form(data, member_id=self._current_member_id)
                result = member_service.update_member(
                    member=member,
                    updated_by=self._current_user.id if self._current_user else None,
                )

                if result:
                    logger.info(f"Member updated: {result.data.member_code if result.data else 'unknown'}")
                    self._emit_success("Member updated successfully")
                    self._is_editing = False
                    self._current_member_id = None
                    self.view.clear_form()
                    self._handle_load_all()
                else:
                    logger.warning(f"Member update failed: {result.error}")
                    self._emit_error(result.error or "Update failed")
            else:
                if not PermissionService.has_permission(self._current_user, Permissions.MEMBERS_CREATE):
                    self._emit_error("You do not have permission to create members")
                    return
                
                member = self._build_member_from_form(data)
                result = member_service.create_member(
                    member=member,
                    created_by=self._current_user.id if self._current_user else None,
                )

                if result:
                    logger.info(f"Member created: {result.data.member_code if result.data else 'unknown'}")
                    self._emit_success("Member created successfully")
                    self.view.clear_form()
                    self._handle_load_all()
                else:
                    logger.warning(f"Member creation failed: {result.error}")
                    self._emit_error(result.error or "Creation failed")
        except Exception as e:
            logger.error(f"Error in create/update handler: {e}")
            self._emit_error("An unexpected error occurred. Please try again.")

    def _handle_update(self) -> None:
        """
        Reads form data and the selected member id from the view, then
        delegates the update to the service.
        is_active is read from the form's combobox and included in the update.
        On success: clears the form and refreshes the table.
        On failure: surfaces the error message to the view.
        """
        data = self.view.get_selected_member_data() or {}

        if not data or not data.get('id'):
            self._emit_error("No member selected for update")
            return
        
        self._is_editing = True
        self._current_member_id = data.get('id')   # UUID, not member_code
        self.view.set_form_data(data)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    @staticmethod
    def _build_member_from_form(data: dict, member_id: Optional[str] = None) -> Member:
        """
        Converts a raw form data dictionary into a Member dataclass.
        is_active is read from the form and included in both create and update.

        Args:
            data:      Dictionary returned by view.get_form_data().
            member_id: When provided, sets the id field (used for updates).

        Returns:
            A Member instance ready to be passed to the service.
        """
        raw_gender = data.get('gender')
        gender = Gender(raw_gender) if raw_gender else None

        return Member(
            id=member_id,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            email=data.get('email') or None,
            phone=data.get('phone') or None,
            date_of_birth=data.get('date_of_birth'),
            gender=gender,
            address=data.get('address') or None,
            emergency_contact_name=data.get('emergency_contact_name') or None,
            emergency_contact_phone=data.get('emergency_contact_phone') or None,
            notes=data.get('notes') or None,
            is_active=data.get('is_active', True),
        )

