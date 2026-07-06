from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from src.database import db_manager
from src.models import Instructor
from src.services.result import ServiceResult

logger = logging.getLogger(__name__)

# Database table name
_TABLE = 'instructors'

# Columns searchable via search_instructors()
_SEARCHABLE_COLUMNS = ('first_name', 'last_name', 'email')


class InstructorService:
    """Handles all business operations related to gym instructors."""

    # Public methods
    def get_all_instructors(self, include_inactive: bool = False) -> ServiceResult[list[Instructor]]:
        """
        Retrieves all instructors from the database.

        Args:
            include_inactive: When True, also returns deactivated instructors.

        Returns:
            ServiceResult with a list of Instructor objects.
        """
        try:
            filters = None if include_inactive else {'is_active': True}
            rows = db_manager.select(
                table=_TABLE,
                order_by='last_name',
                filters=filters,
            )
            instructors = [self._row_to_instructor(row) for row in rows]
            return ServiceResult.ok(instructors)

        except Exception as e:
            logger.error(f"Failed to fetch instructors: {e}")
            return ServiceResult.fail(f"Could not retrieve instructors: {e}")

    def get_instructor_by_id(self, instructor_id: str) -> ServiceResult[Instructor]:
        """
        Retrieves a single instructor by their primary key.

        Args:
            instructor_id: UUID of the instructor.

        Returns:
            ServiceResult with the Instructor object, or an error if not found.
        """
        try:
            rows = db_manager.select(table=_TABLE, filters={'id': instructor_id})
            if not rows:
                return ServiceResult.fail(f"Instructor with id '{instructor_id}' not found")
            return ServiceResult.ok(self._row_to_instructor(rows[0]))

        except Exception as e:
            logger.error(f"Failed to fetch instructor {instructor_id}: {e}")
            return ServiceResult.fail(f"Could not retrieve instructor: {e}")

    def search_instructors(self, term: str, column: Optional[str] = None) -> ServiceResult[list[Instructor]]:
        """
        Searches for active instructors by a partial, case-insensitive match.

        Args:
            term:   The search string.
            column: When provided, restricts the search to that single column
                    ('first_name', 'last_name', or 'email').
                    When None, searches across all three columns and merges
                    unique results.

        Returns:
            ServiceResult with a list of matching Instructor objects.
        """
        if not term or not term.strip():
            return ServiceResult.fail("Search term cannot be empty")

        if column and column in _SEARCHABLE_COLUMNS:
            columns_to_search = (column,)
        else:
            columns_to_search = _SEARCHABLE_COLUMNS

        try:
            seen_ids: set[str] = set()
            instructors: list[Instructor] = []

            for col in columns_to_search:
                rows = db_manager.search(
                    table=_TABLE,
                    column=col,
                    search_term=term.strip(),
                    filters={'is_active': True},
                )
                for row in rows:
                    if row['id'] not in seen_ids:
                        seen_ids.add(row['id'])
                        instructors.append(self._row_to_instructor(row))

            return ServiceResult.ok(instructors)

        except Exception as e:
            logger.error(f"Instructor search failed for term '{term}': {e}")
            return ServiceResult.fail(f"Search failed: {e}")

    def create_instructor(self, instructor: Instructor) -> ServiceResult[Instructor]:
        """
        Validates and persists a new instructor to the database.

        Args:
            instructor: Instructor dataclass instance with the data to save.

        Returns:
            ServiceResult with the newly created Instructor (including its id).
        """
        validation_error = self._validate_instructor(instructor)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            if instructor.email:
                existing = db_manager.select(table=_TABLE, filters={'email': instructor.email})
                if existing:
                    return ServiceResult.fail(f"Email '{instructor.email}' is already registered")

            data = self._instructor_to_row(instructor)
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()

            row = db_manager.insert(table=_TABLE, data=data)
            created = self._row_to_instructor(row)

            logger.info(f"Instructor created: {created.id} — {created.full_name}")
            return ServiceResult.ok(created)

        except Exception as e:
            logger.error(f"Failed to create instructor: {e}")
            return ServiceResult.fail(f"Could not create instructor: {e}")

    def update_instructor(self, instructor: Instructor) -> ServiceResult[Instructor]:
        """
        Updates an existing instructor's information.

        Args:
            instructor: Instructor dataclass with updated fields. Must have a valid id.

        Returns:
            ServiceResult with the updated Instructor object.
        """
        if not instructor.id:
            return ServiceResult.fail("Instructor id is required for updates")

        validation_error = self._validate_instructor(instructor)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            existing = db_manager.select(table=_TABLE, filters={'id': instructor.id})
            if not existing:
                return ServiceResult.fail(f"Instructor with id '{instructor.id}' not found")

            if instructor.email:
                email_conflict = db_manager.select(table=_TABLE, filters={'email': instructor.email})
                if email_conflict and email_conflict[0]['id'] != instructor.id:
                    return ServiceResult.fail(f"Email '{instructor.email}' is already in use by another instructor")

            data = self._instructor_to_row(instructor)
            data['updated_at'] = datetime.now().isoformat()
            data.pop('created_at', None)  # Never overwrite creation timestamp

            rows = db_manager.update(table=_TABLE, data=data, filters={'id': instructor.id})
            updated = self._row_to_instructor(rows[0])

            logger.info(f"Instructor updated: {instructor.id} — {instructor.full_name}")
            return ServiceResult.ok(updated)

        except Exception as e:
            logger.error(f"Failed to update instructor {instructor.id}: {e}")
            return ServiceResult.fail(f"Could not update instructor: {e}")

    # Private helper methods
    @staticmethod
    def _validate_instructor(instructor: Instructor) -> Optional[str]:
        """
        Runs basic field-level validation on an Instructor instance.

        Returns:
            An error message string if validation fails, or None if valid.
        """
        if not instructor.first_name or not instructor.first_name.strip():
            return "First name is required"

        if not instructor.last_name or not instructor.last_name.strip():
            return "Last name is required"

        if instructor.email and '@' not in instructor.email:
            return f"'{instructor.email}' is not a valid email address"

        return None

    @staticmethod
    def _row_to_instructor(row: dict) -> Instructor:
        """Converts a raw database row (dict) into an Instructor dataclass."""
        return Instructor(
            id=row.get('id'),
            user_id=row.get('user_id'),
            first_name=row.get('first_name', ''),
            last_name=row.get('last_name', ''),
            email=row.get('email'),
            phone=row.get('phone'),
            specialties=list(row['specialties']) if row.get('specialties') else [],
            certifications=row.get('certifications'),
            hire_date=row.get('hire_date'),
            photo_url=row.get('photo_url'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _instructor_to_row(instructor: Instructor) -> dict:
        """Converts an Instructor dataclass into a plain dict suitable for the database."""
        return {
            'user_id': instructor.user_id,
            'first_name': instructor.first_name.strip(),
            'last_name': instructor.last_name.strip(),
            'email': instructor.email,
            'phone': instructor.phone,
            'specialties': instructor.specialties or [],
            'certifications': instructor.certifications,
            'hire_date': instructor.hire_date.isoformat() if instructor.hire_date else None,
            'photo_url': instructor.photo_url,
            'is_active': instructor.is_active,
        }


# Global instance
instructor_service = InstructorService()
