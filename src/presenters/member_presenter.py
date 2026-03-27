from __future__ import annotations

import logging
from typing import Optional

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
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
        """Initializes the MemberPresenter.

        Args:
            view: The view associated with this presenter.
            main_app: The main application instance.
            status_handler: A callable to handle status messages.
            current_user: The currently logged-in user, if any.
        """
        self._is_editing = False
        self._current_member_id: Optional[str] = None
        self._current_user: Optional[User] = current_user

        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._connect_signals()
        self._load_user_information()
        self._handle_load_all()  # Load all members when the view opens

    def _connect_signals(self):
        """Connects view signals to their corresponding handler methods."""
        self.view.create_requested.connect(self._handle_create)
        self.view.update_requested.connect(self._handle_edit_requested)
        self.view.cancel_requested.connect(self._handle_cancel)
        self.view.search_requested.connect(self._handle_search)
        self.view.no_selection_error.connect(lambda: self._emit_error(ErrorMessages.MEMBERS_NO_SELECTION))
        self.view.clear_action_requested.connect(self._handle_clear_search)
        self.view.show_inactive_requested.connect(self._handle_load_all)

    def _handle_load_all(self):
        """
        Loads all active members and populates the view table.
        Triggered when the view first opens or requests a full refresh.
        """
        if not PermissionService.has_permission(self._current_user, Permissions.MEMBERS_READ):
            self._emit_error(ErrorMessages.MEMBERS_NO_PERMISSION_READ)
            return
        
        include_inactive = self.view.check_show_inactives.isChecked()
        result = member_service.get_all_members(include_inactive=include_inactive)

        if result:
            self.view.populate_table(result.data)
        else:
            logger.error(f"Load all members failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_search(self, term: str):
        """
        Searches for members matching the given term and updates the table.
        The search column is determined by the view's search option combobox.

        Args:
            term:   Partial string to match. Empty string triggers a full reload.
        """
        current_search_option = self.view.get_selected_search_option()
        if not current_search_option:
            self._emit_error(ErrorMessages.MEMBERS_SELECT_SEARCH_OPTION)
            return

        # Normalize: treat blank input as "show all" regardless of search mode
        if not term or not term.strip():
            self._handle_load_all()
            return

        if current_search_option == "member_code":
            # Exact-match lookup by member code
            result = member_service.get_member_by_code(term.strip())

            if result:
                self.view.populate_table([result.data])
            elif result.is_not_found:
                # Informational — record simply doesn't exist, not a service error
                logger.info(f"Member code lookup: no match for '{term.strip()}'")
                self._emit_info(result.error or ErrorMessages.MEMBERS_NOT_FOUND_BY_CODE)
            else:
                # Technical failure (DB error, connection issue, etc.)
                logger.warning(f"Member code search failed: {result.error}")
                self.view.show_error(result.error)

        else:
            # Partial-match search restricted to the selected column
            result = member_service.search_members(term, column=current_search_option)

            if result:
                self.view.populate_table(result.data)
            else:
                logger.warning(f"Member search failed: {result.error}")
                self.view.show_error(result.error)

    def _handle_clear_search(self) -> None:
        """
        Clears the search input and resets the table to show all members.
        """
        self.view.clear_search()
        self._handle_load_all()

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
                    self._emit_error(ErrorMessages.MEMBERS_ID_REQUIRED)
                    return
                
                if not PermissionService.has_permission(self._current_user, Permissions.MEMBERS_UPDATE):
                    self._emit_error(ErrorMessages.MEMBERS_NO_PERMISSION_UPDATE)
                    return
                
                member = self._build_member_from_form(data, member_id=self._current_member_id)
                result = member_service.update_member(
                    member=member,
                    updated_by=self._current_user.id if self._current_user else None,
                )

                if result:
                    logger.info(f"Member updated: {result.data.member_code if result.data else 'unknown'}")
                    self._emit_success(ErrorMessages.MEMBERS_UPDATED)
                    self._is_editing = False
                    self._current_member_id = None
                    self.view.clear_form()
                    self._handle_load_all()
                else:
                    logger.warning(f"Member update failed: {result.error}")
                    self._emit_error(result.error or ErrorMessages.MEMBERS_UPDATE_FAILED)
            else:
                if not PermissionService.has_permission(self._current_user, Permissions.MEMBERS_CREATE):
                    self._emit_error(ErrorMessages.MEMBERS_NO_PERMISSION_CREATE)
                    return
                
                member = self._build_member_from_form(data)
                result = member_service.create_member(
                    member=member,
                    created_by=self._current_user.id if self._current_user else None,
                )

                if result:
                    logger.info(f"Member created: {result.data.member_code if result.data else 'unknown'}")
                    self._emit_success(ErrorMessages.MEMBERS_CREATED)
                    self.view.clear_form()
                    self._handle_load_all()
                else:
                    logger.warning(f"Member creation failed: {result.error}")
                    self._emit_error(result.error or ErrorMessages.MEMBERS_CREATION_FAILED)
        except Exception as e:
            logger.error(f"Error in create/update handler: {e}")
            self._emit_error(ErrorMessages.MEMBERS_UNEXPECTED_ERROR)

    def _handle_edit_requested(self) -> None:
        """
        Reads form data and the selected member id from the view, then
        delegates the update to the service.
        is_active is read from the form's combobox and included in the update.
        On success: clears the form and refreshes the table.
        On failure: surfaces the error message to the view.
        """
        data = self.view.get_selected_member_data() or {}

        if not data or not data.get('id'):
            self._emit_error(ErrorMessages.MEMBERS_NO_SELECTION)
            return
       
        self._is_editing = True
        self._current_member_id = data.get('id')   # UUID, not member_code
        self.view.set_form_data(data)

    def _handle_cancel(self) -> None:
        """
        Cancels any in-progress create or update operation.
        Resets editing state and clears the form.
        """
        self._is_editing = False
        self._current_member_id = None
        self.view.clear_form()

        self._emit_success(ErrorMessages.MEMBERS_OPERATION_CANCELLED)

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role": self._current_user.role.value if self._current_user else "Unknown"
        }

        self.view.set_user_info(user_info)
        
    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_info(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.INFO)
        
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

