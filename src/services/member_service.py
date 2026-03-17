"""
Member service — business logic layer for gym members.
All public methods return a ServiceResult to provide a consistent API
for callers (presenters, views) without exposing raw exceptions.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from src.database import db_manager
from src.models import Member, Gender
from src.services.result import ServiceResult

logger = logging.getLogger(__name__)

# Supabase table name
_TABLE = 'members'


class MemberService:
    """Handles all business operations related to gym members."""

    # ------------------------------------------------------------------
    # READ OPERATIONS
    # ------------------------------------------------------------------

    def get_all_members(self, include_inactive: bool = False) -> ServiceResult[list[Member]]:
        """
        Retrieves all members from the database.

        Args:
            include_inactive: When True, also returns deactivated members.

        Returns:
            ServiceResult with a list of Member objects.
        """
        try:
            filters = None if include_inactive else {'is_active': True}
            rows = db_manager.select(
                table=_TABLE,
                order_by='last_name',
                filters=filters,
            )
            members = [self._row_to_member(row) for row in rows]
            return ServiceResult.ok(members)

        except Exception as e:
            logger.error(f"Failed to fetch members: {e}")
            return ServiceResult.fail(f"Could not retrieve members: {e}")

    def get_member_by_id(self, member_id: str) -> ServiceResult[Member]:
        """
        Retrieves a single member by their primary key.

        Args:
            member_id: UUID of the member.

        Returns:
            ServiceResult with the Member object, or an error if not found.
        """
        try:
            rows = db_manager.select(table=_TABLE, filters={'id': member_id})
            if not rows:
                return ServiceResult.fail(f"Member with id '{member_id}' not found")
            return ServiceResult.ok(self._row_to_member(rows[0]))

        except Exception as e:
            logger.error(f"Failed to fetch member {member_id}: {e}")
            return ServiceResult.fail(f"Could not retrieve member: {e}")

    def get_member_by_code(self, member_code: str) -> ServiceResult[Member]:
        """
        Retrieves a single member by their unique member code.

        Args:
            member_code: The human-readable code assigned to the member.

        Returns:
            ServiceResult with the Member object, or an error if not found.
        """
        try:
            rows = db_manager.select(table=_TABLE, filters={'member_code': member_code})
            if not rows:
                return ServiceResult.fail(f"Member with code '{member_code}' not found")
            return ServiceResult.ok(self._row_to_member(rows[0]))

        except Exception as e:
            logger.error(f"Failed to fetch member by code {member_code}: {e}")
            return ServiceResult.fail(f"Could not retrieve member: {e}")

    def search_members(self, term: str) -> ServiceResult[list[Member]]:
        """
        Searches for active members by first name, last name, or email.
        Runs three partial-match queries and merges unique results.

        Args:
            term: The search string (case-insensitive partial match).

        Returns:
            ServiceResult with a list of matching Member objects.
        """
        if not term or not term.strip():
            return ServiceResult.fail("Search term cannot be empty")

        try:
            seen_ids: set[str] = set()
            members: list[Member] = []

            for column in ('first_name', 'last_name', 'email'):
                rows = db_manager.search(table=_TABLE, column=column, search_term=term.strip())
                for row in rows:
                    # Skip inactive members and already-seen results
                    if not row.get('is_active', True):
                        continue
                    if row['id'] not in seen_ids:
                        seen_ids.add(row['id'])
                        members.append(self._row_to_member(row))

            return ServiceResult.ok(members)

        except Exception as e:
            logger.error(f"Member search failed for term '{term}': {e}")
            return ServiceResult.fail(f"Search failed: {e}")

    # ------------------------------------------------------------------
    # WRITE OPERATIONS
    # ------------------------------------------------------------------

    def create_member(self, member: Member, created_by: Optional[str] = None) -> ServiceResult[Member]:
        """
        Validates and persists a new member to the database.
        Automatically generates a unique member_code if one is not provided.

        Args:
            member:     Member dataclass instance with the data to save.
            created_by: ID of the user performing the operation (optional).

        Returns:
            ServiceResult with the newly created Member (including its id).
        """
        # --- Validation ---
        validation_error = self._validate_member(member)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            # Check for duplicate email
            if member.email:
                existing = db_manager.select(table=_TABLE, filters={'email': member.email})
                if existing:
                    return ServiceResult.fail(f"Email '{member.email}' is already registered")

            # Auto-generate member code when not provided
            if not member.member_code:
                member.member_code = self._generate_member_code()

            data = self._member_to_row(member)
            data['created_by'] = created_by
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()

            row = db_manager.insert(table=_TABLE, data=data)
            created = self._row_to_member(row)

            logger.info(f"Member created: {created.member_code} — {created.full_name}")
            return ServiceResult.ok(created)

        except Exception as e:
            logger.error(f"Failed to create member: {e}")
            return ServiceResult.fail(f"Could not create member: {e}")

    def update_member(self, member: Member, updated_by: Optional[str] = None) -> ServiceResult[Member]:
        """
        Updates an existing member's information.

        Args:
            member:     Member dataclass with updated fields. Must have a valid id.
            updated_by: ID of the user performing the operation (optional).

        Returns:
            ServiceResult with the updated Member object.
        """
        if not member.id:
            return ServiceResult.fail("Member id is required for updates")

        # --- Validation ---
        validation_error = self._validate_member(member)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            # Confirm the member exists before updating
            existing = db_manager.select(table=_TABLE, filters={'id': member.id})
            if not existing:
                return ServiceResult.fail(f"Member with id '{member.id}' not found")

            # Check email uniqueness (excluding current member)
            if member.email:
                email_conflict = db_manager.select(table=_TABLE, filters={'email': member.email})
                if email_conflict and email_conflict[0]['id'] != member.id:
                    return ServiceResult.fail(f"Email '{member.email}' is already in use by another member")

            data = self._member_to_row(member)
            data['updated_at'] = datetime.now().isoformat()
            data.pop('created_at', None)   # Never overwrite creation timestamp
            data.pop('created_by', None)   # Never overwrite original creator
            data.pop('member_code', None)  # member_code is immutable after creation

            rows = db_manager.update(table=_TABLE, data=data, filters={'id': member.id})
            updated = self._row_to_member(rows[0])

            logger.info(f"Member updated: {member.id} — {member.full_name}")
            return ServiceResult.ok(updated)

        except Exception as e:
            logger.error(f"Failed to update member {member.id}: {e}")
            return ServiceResult.fail(f"Could not update member: {e}")

    def deactivate_member(self, member_id: str) -> ServiceResult[None]:
        """
        Soft-deletes a member by marking them as inactive.
        The record is preserved in the database for historical reporting.

        Args:
            member_id: UUID of the member to deactivate.

        Returns:
            ServiceResult with no data payload on success.
        """
        try:
            existing = db_manager.select(table=_TABLE, filters={'id': member_id})
            if not existing:
                return ServiceResult.fail(f"Member with id '{member_id}' not found")

            if not existing[0].get('is_active', True):
                return ServiceResult.fail("Member is already inactive")

            db_manager.update(
                table=_TABLE,
                data={'is_active': False, 'updated_at': datetime.now().isoformat()},
                filters={'id': member_id},
            )

            logger.info(f"Member deactivated: {member_id}")
            return ServiceResult.ok()

        except Exception as e:
            logger.error(f"Failed to deactivate member {member_id}: {e}")
            return ServiceResult.fail(f"Could not deactivate member: {e}")

    def reactivate_member(self, member_id: str) -> ServiceResult[None]:
        """
        Restores a previously deactivated member to active status.

        Args:
            member_id: UUID of the member to reactivate.

        Returns:
            ServiceResult with no data payload on success.
        """
        try:
            existing = db_manager.select(table=_TABLE, filters={'id': member_id})
            if not existing:
                return ServiceResult.fail(f"Member with id '{member_id}' not found")

            if existing[0].get('is_active', False):
                return ServiceResult.fail("Member is already active")

            db_manager.update(
                table=_TABLE,
                data={'is_active': True, 'updated_at': datetime.now().isoformat()},
                filters={'id': member_id},
            )

            logger.info(f"Member reactivated: {member_id}")
            return ServiceResult.ok()

        except Exception as e:
            logger.error(f"Failed to reactivate member {member_id}: {e}")
            return ServiceResult.fail(f"Could not reactivate member: {e}")

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_member(member: Member) -> Optional[str]:
        """
        Runs basic field-level validation on a Member instance.

        Returns:
            An error message string if validation fails, or None if valid.
        """
        if not member.first_name or not member.first_name.strip():
            return "First name is required"

        if not member.last_name or not member.last_name.strip():
            return "Last name is required"

        if member.email and '@' not in member.email:
            return f"'{member.email}' is not a valid email address"

        return None

    @staticmethod
    def _generate_member_code() -> str:
        """
        Generates a unique member code using the first 8 characters of a UUID.
        Format: MEM-XXXXXXXX  (e.g. MEM-A3F92C1B)
        """
        return f"MEM-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _row_to_member(row: dict) -> Member:
        """Converts a raw Supabase row (dict) into a Member dataclass."""
        return Member(
            id=row.get('id'),
            member_code=row.get('member_code', ''),
            first_name=row.get('first_name', ''),
            last_name=row.get('last_name', ''),
            email=row.get('email'),
            phone=row.get('phone'),
            date_of_birth=row.get('date_of_birth'),
            gender=Gender(row['gender']) if row.get('gender') else None,
            address=row.get('address'),
            emergency_contact_name=row.get('emergency_contact_name'),
            emergency_contact_phone=row.get('emergency_contact_phone'),
            photo_url=row.get('photo_url'),
            notes=row.get('notes'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            created_by=row.get('created_by'),
        )

    @staticmethod
    def _member_to_row(member: Member) -> dict:
        """Converts a Member dataclass into a plain dict suitable for Supabase."""
        row = {
            'first_name': member.first_name.strip(),
            'last_name': member.last_name.strip(),
            'email': member.email,
            'phone': member.phone,
            'date_of_birth': member.date_of_birth.isoformat() if member.date_of_birth else None,
            'gender': member.gender.value if member.gender else None,
            'address': member.address,
            'emergency_contact_name': member.emergency_contact_name,
            'emergency_contact_phone': member.emergency_contact_phone,
            'photo_url': member.photo_url,
            'notes': member.notes,
            'is_active': member.is_active,
        }
        # Only include member_code when it has a value — an empty string would
        # violate the UNIQUE constraint and corrupt existing records.
        if member.member_code:
            row['member_code'] = member.member_code
        return row


# Global instance
member_service = MemberService()
