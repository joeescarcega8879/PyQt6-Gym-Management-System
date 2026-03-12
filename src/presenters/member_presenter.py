"""
Member presenter — mediates between the member view and the member service.
Follows the MVP pattern: the view emits signals, the presenter handles them
by calling the service and instructing the view how to update itself.
"""
from __future__ import annotations

import logging
from typing import Optional

from src.models import Member, Gender
from src.services.member_service import member_service

logger = logging.getLogger(__name__)


class MemberPresenter:
    """
    Handles all user interactions originating from the member management view.
    The presenter is the only component that knows both the view contract
    and the service layer — neither the view nor the service knows each other.
    """

    def __init__(self, view, current_user_id: Optional[str] = None):
        """
        Args:
            view:            The member view instance. Must satisfy the view contract
                             described at the bottom of this module.
            current_user_id: ID of the logged-in user, forwarded to the service
                             for audit fields (created_by / updated_by).
        """
        self.view = view
        self._current_user_id = current_user_id
        self._connect_signals()

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self):
        """Connects view signals to their corresponding handler methods."""
        pass
        # self.view.load_requested.connect(self._handle_load_all)
        # self.view.search_requested.connect(self._handle_search)
        # self.view.create_requested.connect(self._handle_create)
        # self.view.update_requested.connect(self._handle_update)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

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
        data = self.view.get_form_data()

        # Build the Member dataclass from raw form values
        member = self._build_member_from_form(data)

        result = member_service.create_member(
            member=member,
            created_by=self._current_user_id,
        )

        if result:
            logger.info(f"Member created: {result.data.member_code if result.data else 'unknown'}")
            self.view.show_success("Member created successfully")
            self.view.clear_form()
            self._handle_load_all()
        else:
            logger.warning(f"Member creation failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_update(self):
        """
        Reads form data and the selected member id from the view, then
        delegates the update to the service.
        is_active is read from the form's combobox and included in the update.
        On success: clears the form and refreshes the table.
        On failure: surfaces the error message to the view.
        """
        member_id = self.view.get_selected_member_id()
        if not member_id:
            self.view.show_error("No member selected for update")
            return

        data = self.view.get_form_data()

        # Build the Member dataclass, injecting the existing id
        member = self._build_member_from_form(data, member_id=member_id)

        result = member_service.update_member(
            member=member,
            updated_by=self._current_user_id,
        )

        if result:
            logger.info(f"Member updated: {member_id}")
            self.view.show_success("Member updated successfully")
            self.view.clear_form()
            self._handle_load_all()
        else:
            logger.warning(f"Member update failed: {result.error}")
            self.view.show_error(result.error)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# View contract (for documentation purposes)
# ---------------------------------------------------------------------------
#
# The view class connected to this presenter must expose:
#
# Signals:
#   load_requested   — emitted when the view opens or needs a full refresh
#   search_requested — emitted with a str search term
#   create_requested — emitted when the user clicks [Save]
#   update_requested — emitted when the user clicks [Update]
#
# Methods:
#   get_form_data()                        -> dict
#       Must include keys: first_name, last_name, email, phone,
#       date_of_birth, gender, address, emergency_contact_name,
#       emergency_contact_phone, notes, is_active (bool from combobox)
#   get_selected_member_id()               -> str | None
#   populate_table(members: list[Member])  -> None
#   clear_form()                           -> None
#   show_success(message: str)             -> None
#   show_error(message: str)               -> None
