from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional

from src.database import db_manager
from src.models import Class, ClassSchedule, ClassEnrollment, Member, Instructor
from src.models.enums import DifficultyLevel, EnrollmentStatus
from src.services import ServiceResult

logger = logging.getLogger(__name__)

_CLASSES_TABLE     = 'classes'
_SCHEDULES_TABLE   = 'class_schedules'
_ENROLLMENTS_TABLE = 'class_enrollments'

# Days of week mapping (0=Sunday, 6=Saturday)
DAYS_OF_WEEK = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}

_SCHEDULE_COLUMNS = (
    "class_schedules.id, class_schedules.class_id, class_schedules.instructor_id, "
    "class_schedules.day_of_week, class_schedules.start_time, class_schedules.end_time, "
    "class_schedules.room, class_schedules.is_active, "
    "class_schedules.created_at, class_schedules.updated_at, "
    "classes.name AS class_name, classes.duration_minutes, classes.max_capacity, "
    "classes.difficulty_level, classes.description AS class_description"
)
_SCHEDULE_JOINS = [
    "LEFT JOIN classes ON classes.id = class_schedules.class_id",
]

_ENROLLMENT_COLUMNS = (
    "class_enrollments.id, class_enrollments.schedule_id, class_enrollments.member_id, "
    "class_enrollments.enrollment_date, class_enrollments.status, "
    "class_enrollments.class_date, class_enrollments.notes, "
    "members.member_code, members.first_name, members.last_name, "
    "class_schedules.day_of_week, class_schedules.start_time, class_schedules.end_time, "
    "class_schedules.room, class_schedules.class_id, "
    "classes.name AS class_name"
)
_ENROLLMENT_JOINS = [
    "LEFT JOIN members ON members.id = class_enrollments.member_id",
    "LEFT JOIN class_schedules ON class_schedules.id = class_enrollments.schedule_id",
    "LEFT JOIN classes ON classes.id = class_schedules.class_id",
]


class ClassService:
    """Service layer for managing gym classes, schedules, and enrollments."""

    # ------------------------------------------------------------------ #
    # Class methods
    # ------------------------------------------------------------------ #

    def get_all_classes(self, include_inactive: bool = False) -> ServiceResult[list[Class]]:
        """Fetches all classes, optionally including inactive ones."""
        try:
            filters = None if include_inactive else {'is_active': True}
            rows = db_manager.select(
                table=_CLASSES_TABLE,
                filters=filters,
                order_by='name',
            )
            return ServiceResult.ok([self._row_to_class(row) for row in rows])
        except Exception as e:
            logger.error(f"Failed to fetch classes: {e}")
            return ServiceResult.fail(str(e))

    def get_class_by_id(self, class_id: str) -> ServiceResult[Class]:
        """Retrieves a single class by its primary key."""
        try:
            rows = db_manager.select(table=_CLASSES_TABLE, filters={'id': class_id})
            if not rows:
                return ServiceResult.not_found("Class not found")
            return ServiceResult.ok(self._row_to_class(rows[0]))
        except Exception as e:
            logger.error(f"Failed to fetch class {class_id}: {e}")
            return ServiceResult.fail(str(e))

    def create_class(self, gym_class: Class) -> ServiceResult[Class]:
        """Validates and persists a new class."""
        validation_error = self._validate_class(gym_class)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            data = self._class_to_row(gym_class)
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()
            row = db_manager.insert(_CLASSES_TABLE, data)
            logger.info(f"Class created: {gym_class.name}")
            return ServiceResult.ok(self._row_to_class(row))
        except Exception as e:
            logger.error(f"Failed to create class: {e}")
            return ServiceResult.fail(str(e))

    def update_class(self, gym_class: Class) -> ServiceResult[Class]:
        """Updates an existing class. Requires a valid gym_class.id."""
        if not gym_class.id:
            return ServiceResult.fail("Class ID is required for updates")

        validation_error = self._validate_class(gym_class)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            existing = db_manager.select(table=_CLASSES_TABLE, filters={'id': gym_class.id})
            if not existing:
                return ServiceResult.fail("Class not found")

            data = self._class_to_row(gym_class)
            data['updated_at'] = datetime.now().isoformat()
            rows = db_manager.update(_CLASSES_TABLE, data, filters={'id': gym_class.id})
            logger.info(f"Class updated: {gym_class.id}")
            return ServiceResult.ok(self._row_to_class(rows[0]))
        except Exception as e:
            logger.error(f"Failed to update class {gym_class.id}: {e}")
            return ServiceResult.fail(str(e))

    def toggle_class_status(self, class_id: str, is_active: bool) -> ServiceResult[bool]:
        """Activates or deactivates a class."""
        try:
            db_manager.update(
                _CLASSES_TABLE,
                {'is_active': is_active, 'updated_at': datetime.now().isoformat()},
                filters={'id': class_id},
            )
            return ServiceResult.ok(True)
        except Exception as e:
            logger.error(f"Failed to toggle class status {class_id}: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Schedule methods
    # ------------------------------------------------------------------ #

    def get_schedules(
        self,
        class_id: Optional[str] = None,
        day_of_week: Optional[int] = None,
        include_inactive: bool = False,
    ) -> ServiceResult[list[ClassSchedule]]:
        """Returns schedules with optional filters by class and/or day of week."""
        try:
            filters: dict = {}
            if not include_inactive:
                filters['class_schedules.is_active'] = True
            if class_id:
                filters['class_schedules.class_id'] = class_id
            if day_of_week is not None:
                filters['class_schedules.day_of_week'] = day_of_week

            rows = db_manager.select(
                table=_SCHEDULES_TABLE,
                columns=_SCHEDULE_COLUMNS,
                joins=_SCHEDULE_JOINS,
                filters=filters if filters else None,
                order_by='class_schedules.day_of_week, class_schedules.start_time',
            )
            return ServiceResult.ok([self._row_to_schedule(row) for row in rows])
        except Exception as e:
            logger.error(f"Failed to fetch schedules: {e}")
            return ServiceResult.fail(str(e))

    def get_schedule_by_id(self, schedule_id: str) -> ServiceResult[ClassSchedule]:
        """Retrieves a single schedule by its primary key."""
        try:
            rows = db_manager.select(
                table=_SCHEDULES_TABLE,
                columns=_SCHEDULE_COLUMNS,
                joins=_SCHEDULE_JOINS,
                filters={'class_schedules.id': schedule_id},
            )
            if not rows:
                return ServiceResult.not_found("Schedule not found")
            return ServiceResult.ok(self._row_to_schedule(rows[0]))
        except Exception as e:
            logger.error(f"Failed to fetch schedule {schedule_id}: {e}")
            return ServiceResult.fail(str(e))

    def create_schedule(self, schedule: ClassSchedule) -> ServiceResult[ClassSchedule]:
        """Validates and persists a new class schedule."""
        validation_error = self._validate_schedule(schedule)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            data = self._schedule_to_row(schedule)
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()
            row = db_manager.insert(_SCHEDULES_TABLE, data)
            logger.info(f"Schedule created for class {schedule.class_id}")
            return ServiceResult.ok(self._row_to_schedule(row))
        except Exception as e:
            logger.error(f"Failed to create schedule: {e}")
            return ServiceResult.fail(str(e))

    def update_schedule(self, schedule: ClassSchedule) -> ServiceResult[ClassSchedule]:
        """Updates an existing schedule. Requires a valid schedule.id."""
        if not schedule.id:
            return ServiceResult.fail("Schedule ID is required for updates")

        validation_error = self._validate_schedule(schedule)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            existing = db_manager.select(table=_SCHEDULES_TABLE, filters={'id': schedule.id})
            if not existing:
                return ServiceResult.fail("Schedule not found")

            data = self._schedule_to_row(schedule)
            data['updated_at'] = datetime.now().isoformat()
            rows = db_manager.update(_SCHEDULES_TABLE, data, filters={'id': schedule.id})
            logger.info(f"Schedule updated: {schedule.id}")
            return ServiceResult.ok(self._row_to_schedule(rows[0]))
        except Exception as e:
            logger.error(f"Failed to update schedule {schedule.id}: {e}")
            return ServiceResult.fail(str(e))

    def toggle_schedule_status(self, schedule_id: str, is_active: bool) -> ServiceResult[bool]:
        """Activates or deactivates a class schedule."""
        try:
            db_manager.update(
                _SCHEDULES_TABLE,
                {'is_active': is_active, 'updated_at': datetime.now().isoformat()},
                filters={'id': schedule_id},
            )
            return ServiceResult.ok(True)
        except Exception as e:
            logger.error(f"Failed to toggle schedule status {schedule_id}: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Enrollment methods
    # ------------------------------------------------------------------ #

    def get_enrollments(
        self,
        schedule_id: Optional[str] = None,
        class_date: Optional[date] = None,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None,
    ) -> ServiceResult[list[ClassEnrollment]]:
        """Returns enrollments with optional filters."""
        try:
            filters: dict = {}
            if schedule_id:
                filters['class_enrollments.schedule_id'] = schedule_id
            if status:
                filters['class_enrollments.status'] = status.value
            if class_date:
                filters['class_enrollments.class_date'] = class_date.isoformat()

            rows = db_manager.select(
                table=_ENROLLMENTS_TABLE,
                columns=_ENROLLMENT_COLUMNS,
                joins=_ENROLLMENT_JOINS,
                filters=filters if filters else None,
                order_by='class_enrollments.class_date, class_schedules.start_time',
            )

            enrollments = [self._row_to_enrollment(row) for row in rows]

            if search_term:
                term = search_term.strip().lower()
                enrollments = [
                    e for e in enrollments
                    if e.member and (
                        term in e.member.full_name.lower() or
                        term in e.member.member_code.lower()
                    )
                ]

            return ServiceResult.ok(enrollments)
        except Exception as e:
            logger.error(f"Failed to fetch enrollments: {e}")
            return ServiceResult.fail(str(e))

    def get_enrollments_by_member(self, member_id: str) -> ServiceResult[list[ClassEnrollment]]:
        """Returns all enrollments for a specific member."""
        try:
            rows = db_manager.select(
                table=_ENROLLMENTS_TABLE,
                columns=_ENROLLMENT_COLUMNS,
                joins=_ENROLLMENT_JOINS,
                filters={'class_enrollments.member_id': member_id},
                order_by='class_enrollments.class_date',
            )
            return ServiceResult.ok([self._row_to_enrollment(row) for row in rows])
        except Exception as e:
            logger.error(f"Failed to fetch enrollments for member {member_id}: {e}")
            return ServiceResult.fail(str(e))

    def enroll_member(
        self,
        schedule_id: str,
        member_id: str,
        class_date: date,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> ServiceResult[ClassEnrollment]:
        """Enrolls a member into a class schedule for a specific date.

        Fails if:
        - The member is already enrolled in this schedule on this date.
        - The class has reached its maximum capacity.
        """
        try:
            # Check for duplicate enrollment
            existing = db_manager.select(
                table=_ENROLLMENTS_TABLE,
                filters={
                    'schedule_id': schedule_id,
                    'member_id': member_id,
                    'class_date': class_date.isoformat(),
                },
            )
            if existing:
                return ServiceResult.fail("This member is already enrolled in this class on this date")

            # Check capacity
            capacity_error = self._validate_capacity(schedule_id, class_date)
            if capacity_error:
                return ServiceResult.fail(capacity_error)

            data = {
                'schedule_id': schedule_id,
                'member_id': member_id,
                'enrollment_date': datetime.now().isoformat(),
                'status': EnrollmentStatus.ENROLLED.value,
                'class_date': class_date.isoformat(),
                'notes': notes,
                'created_by': created_by,
            }
            row = db_manager.insert(_ENROLLMENTS_TABLE, data)
            logger.info(f"Member {member_id} enrolled in schedule {schedule_id} for {class_date}")
            return ServiceResult.ok(self._row_to_enrollment(row))
        except Exception as e:
            logger.error(f"Failed to enroll member {member_id}: {e}")
            return ServiceResult.fail(str(e))

    def update_enrollment_status(
        self,
        enrollment_id: str,
        new_status: EnrollmentStatus,
    ) -> ServiceResult[bool]:
        """Updates the status of an enrollment (attended, absent, cancelled)."""
        try:
            rows = db_manager.select(table=_ENROLLMENTS_TABLE, filters={'id': enrollment_id})
            if not rows:
                return ServiceResult.not_found("Enrollment not found")

            db_manager.update(
                _ENROLLMENTS_TABLE,
                {'status': new_status.value},
                filters={'id': enrollment_id},
            )
            logger.info(f"Enrollment {enrollment_id} status updated to {new_status.value}")
            return ServiceResult.ok(True)
        except Exception as e:
            logger.error(f"Failed to update enrollment status {enrollment_id}: {e}")
            return ServiceResult.fail(str(e))

    def get_enrollment_count(self, schedule_id: str, class_date: date) -> int:
        """Returns the number of active enrollments for a schedule on a given date."""
        try:
            rows = db_manager.select(
                table=_ENROLLMENTS_TABLE,
                filters={
                    'schedule_id': schedule_id,
                    'class_date': class_date.isoformat(),
                },
            )
            active = [
                r for r in rows
                if r.get('status') != EnrollmentStatus.CANCELLED.value
            ]
            return len(active)
        except Exception:
            return 0

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _validate_capacity(self, schedule_id: str, class_date: date) -> Optional[str]:
        """Returns an error string if the class is at full capacity, or None if OK."""
        schedule_rows = db_manager.select(
            table=_SCHEDULES_TABLE,
            columns=_SCHEDULE_COLUMNS,
            joins=_SCHEDULE_JOINS,
            filters={'class_schedules.id': schedule_id},
        )
        if not schedule_rows:
            return None  # schedule not found — let insert fail naturally

        schedule = self._row_to_schedule(schedule_rows[0])
        max_capacity = schedule.class_info.max_capacity if schedule.class_info else None

        if max_capacity is None:
            return None  # unlimited capacity

        current_count = self.get_enrollment_count(schedule_id, class_date)
        if current_count >= max_capacity:
            return "This class has reached its maximum capacity"
        return None

    @staticmethod
    def _validate_class(gym_class: Class) -> Optional[str]:
        """Returns an error message if the class is invalid, or None if valid."""
        if not gym_class.name or not gym_class.name.strip():
            return "Class name is required"
        if gym_class.duration_minutes < 1:
            return "Duration must be at least 1 minute"
        if gym_class.max_capacity is not None and gym_class.max_capacity < 1:
            return "Capacity must be greater than zero"
        return None

    @staticmethod
    def _validate_schedule(schedule: ClassSchedule) -> Optional[str]:
        """Returns an error message if the schedule is invalid, or None if valid."""
        if not schedule.class_id:
            return "A class must be selected for the schedule"
        if schedule.day_of_week not in range(7):
            return "Invalid day of week"
        if schedule.start_time >= schedule.end_time:
            return "End time must be after start time"
        return None

    @staticmethod
    def _class_to_row(gym_class: Class) -> dict:
        """Converts a Class dataclass into a plain dict for the database."""
        return {
            'name': gym_class.name.strip(),
            'description': gym_class.description,
            'duration_minutes': gym_class.duration_minutes,
            'max_capacity': gym_class.max_capacity,
            'difficulty_level': gym_class.difficulty_level.value,
            'is_active': gym_class.is_active,
        }

    @staticmethod
    def _schedule_to_row(schedule: ClassSchedule) -> dict:
        """Converts a ClassSchedule dataclass into a plain dict for the database."""
        return {
            'class_id': schedule.class_id,
            'instructor_id': schedule.instructor_id,
            'day_of_week': schedule.day_of_week,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'room': schedule.room,
            'is_active': schedule.is_active,
        }

    @staticmethod
    def _row_to_class(row: dict) -> Class:
        """Converts a raw database row into a Class dataclass."""
        return Class(
            id=row.get('id'),
            name=row.get('name', ''),
            description=row.get('description'),
            duration_minutes=row.get('duration_minutes', 60),
            max_capacity=row.get('max_capacity'),
            difficulty_level=DifficultyLevel(row.get('difficulty_level', DifficultyLevel.ALL.value)),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _row_to_schedule(row: dict) -> ClassSchedule:
        """Converts a raw database row (with joins) into a ClassSchedule dataclass."""
        class_name = row.get('class_name')
        class_info = Class(
            id=row.get('class_id'),
            name=class_name or '',
            description=row.get('class_description'),
            duration_minutes=row.get('duration_minutes', 60),
            max_capacity=row.get('max_capacity'),
            difficulty_level=DifficultyLevel(row.get('difficulty_level', DifficultyLevel.ALL.value)),
        ) if class_name else None

        return ClassSchedule(
            id=row.get('id'),
            class_id=row.get('class_id', ''),
            instructor_id=row.get('instructor_id'),
            day_of_week=row.get('day_of_week', 0),
            start_time=str(row.get('start_time', '00:00')),
            end_time=str(row.get('end_time', '00:00')),
            room=row.get('room'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            class_info=class_info,
        )

    @staticmethod
    def _row_to_enrollment(row: dict) -> ClassEnrollment:
        """Converts a raw database row (with joins) into a ClassEnrollment dataclass."""
        member_code = row.get('member_code')
        member = Member(
            id=row.get('member_id'),
            member_code=member_code or '',
            first_name=row.get('first_name', ''),
            last_name=row.get('last_name', ''),
        ) if member_code else None

        class_name = row.get('class_name')
        class_info = Class(
            id=row.get('class_id'),
            name=class_name or '',
        ) if class_name else None

        schedule = ClassSchedule(
            id=row.get('schedule_id'),
            class_id=row.get('class_id', ''),
            day_of_week=row.get('day_of_week', 0),
            start_time=str(row.get('start_time', '00:00')),
            end_time=str(row.get('end_time', '00:00')),
            room=row.get('room'),
            class_info=class_info,
        ) if row.get('schedule_id') else None

        def parse_date(value) -> Optional[date]:
            if not value:
                return None
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value))
            except ValueError:
                return None

        def parse_dt(value) -> Optional[datetime]:
            if not value:
                return None
            if isinstance(value, datetime):
                return value
            try:
                return datetime.fromisoformat(str(value))
            except ValueError:
                return None

        return ClassEnrollment(
            id=row.get('id'),
            schedule_id=row.get('schedule_id', ''),
            member_id=row.get('member_id', ''),
            enrollment_date=parse_dt(row.get('enrollment_date')) or datetime.now(),
            status=EnrollmentStatus(row.get('status', EnrollmentStatus.ENROLLED.value)),
            class_date=parse_date(row.get('class_date')) or date.today(),
            notes=row.get('notes'),
            schedule=schedule,
            member=member,
        )


# Global instance
class_service = ClassService()
