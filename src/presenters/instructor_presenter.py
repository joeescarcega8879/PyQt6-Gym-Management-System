from __future__ import annotations

import logging
from typing import Optional

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.models import Instructor, User
from src.services.instructor_service import instructor_service

from src.domain.permissions import Permissions
from src.domain.permissions_service import PermissionService

logger = logging.getLogger(__name__)


class InstructorPresenter:
    """
    Handles all user interactions originating from the instructor management view.
    The presenter is the only component that knows both the view contract
    and the service layer — neither the view nor the service knows each other.
    """

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None):
        """Initializes the InstructorPresenter.

        Args:
            view: The view associated with this presenter.
            main_app: The main application instance.
            status_handler: A callable to handle status messages.
            current_user: The currently logged-in user, if any.
        """
        self._is_editing = False
        self._current_instructor_id: Optional[str] = None
        self._current_user: Optional[User] = current_user

        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._connect_signals()
        self._load_user_information()
        self._handle_load_all()  # Load all instructors when the view opens

    def _connect_signals(self):
        """Connects view signals to their corresponding handler methods."""
        self.view.create_requested.connect(self._handle_create)
        self.view.update_requested.connect(self._handle_edit_requested)
        self.view.cancel_requested.connect(self._handle_cancel)
        self.view.search_requested.connect(self._handle_search)
        self.view.no_selection_error.connect(lambda: self._emit_error(ErrorMessages.INSTRUCTORS_NO_SELECTION))
        self.view.clear_action_requested.connect(self._handle_clear_search)
        self.view.show_inactive_requested.connect(self._handle_load_all)

    def _handle_load_all(self):
        """
        Loads all active instructors and populates the view table.
        Triggered when the view first opens or requests a full refresh.
        """
        if not PermissionService.has_permission(self._current_user, Permissions.INSTRUCTORS_READ):
            self._emit_error(ErrorMessages.INSTRUCTORS_NO_PERMISSION_READ)
            return

        include_inactive = self.view.check_show_inactives.isChecked()
        result = instructor_service.get_all_instructors(include_inactive=include_inactive)

        if result:
            self.view.populate_table(result.data)
        else:
            logger.error(f"Load all instructors failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_search(self, term: str) -> None:
        """
        Searches for instructors matching the given term and updates the table.
        The search column is determined by the view's search option combobox.

        Args:
            term: Partial string to match. Empty string triggers a full reload.
        """
        current_search_option = self.view.get_selected_search_option()
        if not current_search_option:
            self._emit_error(ErrorMessages.INSTRUCTORS_SELECT_SEARCH_OPTION)
            return

        # Normalize: treat blank input as "show all" regardless of search mode
        if not term or not term.strip():
            self._handle_load_all()
            return

        result = instructor_service.search_instructors(term, column=current_search_option)

        if result:
            self.view.populate_table(result.data)
        else:
            logger.warning(f"Instructor search failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_clear_search(self) -> None:
        """Clears the search input and resets the table to show all instructors."""
        self.view.clear_search()
        self._handle_load_all()

    def _handle_create(self):
        """
        Reads form data from the view, builds an Instructor instance and
        delegates creation to the service.
        On success: clears the form and refreshes the table.
        On failure: surfaces the error message to the view.
        """
        data = self.view.get_form_data() or {}

        try:
            if self._is_editing:
                if self._current_instructor_id is None:
                    self._emit_error(ErrorMessages.INSTRUCTORS_ID_REQUIRED)
                    return

                if not PermissionService.has_permission(self._current_user, Permissions.INSTRUCTORS_UPDATE):
                    self._emit_error(ErrorMessages.INSTRUCTORS_NO_PERMISSION_UPDATE)
                    return

                instructor = self._build_instructor_from_form(data, instructor_id=self._current_instructor_id)
                result = instructor_service.update_instructor(instructor)

                if result:
                    logger.info(f"Instructor updated: {result.data.id if result.data else 'unknown'}")
                    self._emit_success(ErrorMessages.INSTRUCTORS_UPDATED)
                    self._is_editing = False
                    self._current_instructor_id = None
                    self.view.clear_form()
                    self._handle_load_all()
                else:
                    logger.warning(f"Instructor update failed: {result.error}")
                    self._emit_error(result.error or ErrorMessages.INSTRUCTORS_UPDATE_FAILED)
            else:
                if not PermissionService.has_permission(self._current_user, Permissions.INSTRUCTORS_CREATE):
                    self._emit_error(ErrorMessages.INSTRUCTORS_NO_PERMISSION_CREATE)
                    return

                instructor = self._build_instructor_from_form(data)
                result = instructor_service.create_instructor(instructor)

                if result:
                    logger.info(f"Instructor created: {result.data.id if result.data else 'unknown'}")
                    self._emit_success(ErrorMessages.INSTRUCTORS_CREATED)
                    self.view.clear_form()
                    self._handle_load_all()
                else:
                    logger.warning(f"Instructor creation failed: {result.error}")
                    self._emit_error(result.error or ErrorMessages.INSTRUCTORS_CREATION_FAILED)
        except Exception as e:
            logger.error(f"Error in create/update handler: {e}")
            self._emit_error(ErrorMessages.INSTRUCTORS_UNEXPECTED_ERROR)

    def _handle_edit_requested(self) -> None:
        """
        Reads the selected instructor's data from the view and switches to edit mode.
        """
        data = self.view.get_selected_instructor_data() or {}

        if not data or not data.get('id'):
            self._emit_error(ErrorMessages.INSTRUCTORS_NO_SELECTION)
            return

        self._is_editing = True
        self._current_instructor_id = data.get('id')  # UUID
        self.view.set_form_data(data)

    def _handle_cancel(self) -> None:
        """Cancels any in-progress create or update operation."""
        self._is_editing = False
        self._current_instructor_id = None
        self.view.clear_form()

        self._emit_success(ErrorMessages.INSTRUCTORS_OPERATION_CANCELLED)

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
    def _build_instructor_from_form(data: dict, instructor_id: Optional[str] = None) -> Instructor:
        """
        Converts a raw form data dictionary into an Instructor dataclass.

        Args:
            data:           Dictionary returned by view.get_form_data().
            instructor_id:  When provided, sets the id field (used for updates).

        Returns:
            An Instructor instance ready to be passed to the service.
        """
        return Instructor(
            id=instructor_id,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            email=data.get('email') or None,
            phone=data.get('phone') or None,
            specialties=data.get('specialties') or [],
            certifications=data.get('certifications') or None,
            hire_date=data.get('hire_date'),
            is_active=data.get('is_active', True),
        )
