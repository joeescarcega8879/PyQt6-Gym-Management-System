"""
Tests for ClassService.

All database interactions are isolated by patching the global `db_manager`
singleton that `class_service` imports at module level.

Patch target: 'src.services.class_service.db_manager'
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime

from src.services.class_service import ClassService
from src.models.models import Class, ClassSchedule, ClassEnrollment
from src.models.enums import DifficultyLevel, EnrollmentStatus


# ---------------------------------------------------------------------------
# Shared test data factories
# ---------------------------------------------------------------------------

def make_class_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the classes table schema."""
    defaults = dict(
        id="cls-001",
        name="Yoga",
        description="Relaxing yoga class",
        duration_minutes=60,
        max_capacity=20,
        difficulty_level="all",
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return defaults


def make_schedule_row(**kwargs) -> dict:
    """Factory for a raw DB row matching class_schedules with join columns."""
    defaults = dict(
        id="sched-001",
        class_id="cls-001",
        instructor_id=None,
        day_of_week=1,
        start_time="08:00",
        end_time="09:00",
        room="Studio A",
        is_active=True,
        created_at=None,
        updated_at=None,
        class_name="Yoga",
        duration_minutes=60,
        max_capacity=20,
        difficulty_level="all",
        class_description="Relaxing yoga class",
    )
    defaults.update(kwargs)
    return defaults


def make_enrollment_row(**kwargs) -> dict:
    """Factory for a raw DB row matching class_enrollments with join columns."""
    defaults = dict(
        id="enr-001",
        schedule_id="sched-001",
        member_id="mem-001",
        enrollment_date=datetime.now().isoformat(),
        status="enrolled",
        class_date="2026-05-19",
        notes=None,
        member_code="MEM-001",
        first_name="John",
        last_name="Doe",
        day_of_week=1,
        start_time="08:00",
        end_time="09:00",
        room="Studio A",
        class_id="cls-001",
        class_name="Yoga",
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _validate_class  (pure static)
# ---------------------------------------------------------------------------

class TestValidateClass:
    def test_valid_class_returns_none(self):
        c = Class(name="Yoga", duration_minutes=60)
        assert ClassService._validate_class(c) is None

    def test_empty_name_returns_error(self):
        c = Class(name="", duration_minutes=60)
        result = ClassService._validate_class(c)
        assert result is not None
        assert "name" in result.lower()

    def test_whitespace_name_returns_error(self):
        c = Class(name="   ", duration_minutes=60)
        result = ClassService._validate_class(c)
        assert result is not None

    def test_zero_duration_returns_error(self):
        c = Class(name="Yoga", duration_minutes=0)
        result = ClassService._validate_class(c)
        assert result is not None
        assert "duration" in result.lower()

    def test_negative_duration_returns_error(self):
        c = Class(name="Yoga", duration_minutes=-1)
        result = ClassService._validate_class(c)
        assert result is not None

    def test_zero_capacity_is_valid(self):
        # 0 is invalid (means user entered 0 explicitly, not unlimited)
        c = Class(name="Yoga", duration_minutes=60, max_capacity=0)
        result = ClassService._validate_class(c)
        assert result is not None
        assert "capacity" in result.lower()

    def test_none_capacity_is_valid(self):
        c = Class(name="Yoga", duration_minutes=60, max_capacity=None)
        assert ClassService._validate_class(c) is None

    def test_positive_capacity_is_valid(self):
        c = Class(name="Yoga", duration_minutes=60, max_capacity=20)
        assert ClassService._validate_class(c) is None


# ---------------------------------------------------------------------------
# _validate_schedule  (pure static)
# ---------------------------------------------------------------------------

class TestValidateSchedule:
    def test_valid_schedule_returns_none(self):
        s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="08:00", end_time="09:00")
        assert ClassService._validate_schedule(s) is None

    def test_missing_class_id_returns_error(self):
        s = ClassSchedule(class_id="", day_of_week=1, start_time="08:00", end_time="09:00")
        result = ClassService._validate_schedule(s)
        assert result is not None
        assert "class" in result.lower()

    def test_invalid_day_returns_error(self):
        s = ClassSchedule(class_id="cls-001", day_of_week=7, start_time="08:00", end_time="09:00")
        result = ClassService._validate_schedule(s)
        assert result is not None
        assert "day" in result.lower()

    def test_start_after_end_returns_error(self):
        s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="10:00", end_time="09:00")
        result = ClassService._validate_schedule(s)
        assert result is not None
        assert "time" in result.lower()

    def test_start_equal_end_returns_error(self):
        s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="09:00", end_time="09:00")
        result = ClassService._validate_schedule(s)
        assert result is not None

    def test_all_days_valid(self):
        for day in range(7):
            s = ClassSchedule(class_id="cls-001", day_of_week=day, start_time="08:00", end_time="09:00")
            assert ClassService._validate_schedule(s) is None


# ---------------------------------------------------------------------------
# _row_to_class  (pure static)
# ---------------------------------------------------------------------------

class TestRowToClass:
    def test_converts_valid_row(self):
        row = make_class_row()
        c = ClassService._row_to_class(row)
        assert c.id == "cls-001"
        assert c.name == "Yoga"
        assert c.duration_minutes == 60
        assert c.max_capacity == 20
        assert c.difficulty_level == DifficultyLevel.ALL
        assert c.is_active is True

    def test_difficulty_level_parsed_correctly(self):
        for level in DifficultyLevel:
            row = make_class_row(difficulty_level=level.value)
            c = ClassService._row_to_class(row)
            assert c.difficulty_level == level

    def test_none_capacity_preserved(self):
        row = make_class_row(max_capacity=None)
        c = ClassService._row_to_class(row)
        assert c.max_capacity is None


# ---------------------------------------------------------------------------
# _row_to_schedule  (pure static)
# ---------------------------------------------------------------------------

class TestRowToSchedule:
    def test_converts_valid_row(self):
        row = make_schedule_row()
        s = ClassService._row_to_schedule(row)
        assert s.id == "sched-001"
        assert s.class_id == "cls-001"
        assert s.day_of_week == 1
        assert s.start_time == "08:00"
        assert s.end_time == "09:00"
        assert s.room == "Studio A"
        assert s.is_active is True

    def test_class_info_populated_from_join(self):
        row = make_schedule_row()
        s = ClassService._row_to_schedule(row)
        assert s.class_info is not None
        assert s.class_info.name == "Yoga"
        assert s.class_info.max_capacity == 20

    def test_class_info_none_when_no_class_name(self):
        row = make_schedule_row(class_name=None)
        s = ClassService._row_to_schedule(row)
        assert s.class_info is None


# ---------------------------------------------------------------------------
# _row_to_enrollment  (pure static)
# ---------------------------------------------------------------------------

class TestRowToEnrollment:
    def test_converts_valid_row(self):
        row = make_enrollment_row()
        e = ClassService._row_to_enrollment(row)
        assert e.id == "enr-001"
        assert e.schedule_id == "sched-001"
        assert e.member_id == "mem-001"
        assert e.status == EnrollmentStatus.ENROLLED
        assert e.class_date == date(2026, 5, 19)

    def test_member_populated_from_join(self):
        row = make_enrollment_row()
        e = ClassService._row_to_enrollment(row)
        assert e.member is not None
        assert e.member.member_code == "MEM-001"
        assert e.member.first_name == "John"

    def test_member_none_when_no_code(self):
        row = make_enrollment_row(member_code=None)
        e = ClassService._row_to_enrollment(row)
        assert e.member is None

    def test_schedule_populated_from_join(self):
        row = make_enrollment_row()
        e = ClassService._row_to_enrollment(row)
        assert e.schedule is not None
        assert e.schedule.start_time == "08:00"

    def test_all_statuses_parsed(self):
        for status in EnrollmentStatus:
            row = make_enrollment_row(status=status.value)
            e = ClassService._row_to_enrollment(row)
            assert e.status == status


# ---------------------------------------------------------------------------
# get_all_classes
# ---------------------------------------------------------------------------

class TestGetAllClasses:
    def test_returns_active_classes_by_default(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_class_row()]
            result = ClassService().get_all_classes()
            assert result.success
            assert len(result.data) == 1
            mock_db.select.assert_called_once_with(
                table='classes',
                filters={'is_active': True},
                order_by='name',
            )

    def test_returns_all_classes_when_include_inactive(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_class_row(), make_class_row(id="cls-002", is_active=False)]
            result = ClassService().get_all_classes(include_inactive=True)
            assert result.success
            assert len(result.data) == 2
            mock_db.select.assert_called_once_with(
                table='classes',
                filters=None,
                order_by='name',
            )

    def test_returns_fail_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            result = ClassService().get_all_classes()
            assert not result.success
            assert result.error is not None

    def test_returns_empty_list_when_no_classes(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = []
            result = ClassService().get_all_classes()
            assert result.success
            assert result.data == []


# ---------------------------------------------------------------------------
# get_class_by_id
# ---------------------------------------------------------------------------

class TestGetClassById:
    def test_returns_class_when_found(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_class_row()]
            result = ClassService().get_class_by_id("cls-001")
            assert result.success
            assert result.data.id == "cls-001"

    def test_returns_not_found_when_missing(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = []
            result = ClassService().get_class_by_id("cls-999")
            assert not result.success
            assert result.is_not_found

    def test_returns_fail_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            result = ClassService().get_class_by_id("cls-001")
            assert not result.success


# ---------------------------------------------------------------------------
# create_class
# ---------------------------------------------------------------------------

class TestCreateClass:
    def test_creates_class_successfully(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.insert.return_value = make_class_row()
            c = Class(name="Yoga", duration_minutes=60)
            result = ClassService().create_class(c)
            assert result.success
            assert result.data.name == "Yoga"
            mock_db.insert.assert_called_once()

    def test_fails_on_empty_name(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            c = Class(name="", duration_minutes=60)
            result = ClassService().create_class(c)
            assert not result.success
            mock_db.insert.assert_not_called()

    def test_fails_on_zero_duration(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            c = Class(name="Yoga", duration_minutes=0)
            result = ClassService().create_class(c)
            assert not result.success
            mock_db.insert.assert_not_called()

    def test_fails_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.insert.side_effect = Exception("DB error")
            c = Class(name="Yoga", duration_minutes=60)
            result = ClassService().create_class(c)
            assert not result.success


# ---------------------------------------------------------------------------
# update_class
# ---------------------------------------------------------------------------

class TestUpdateClass:
    def test_updates_class_successfully(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_class_row()]
            mock_db.update.return_value = [make_class_row(name="Pilates")]
            c = Class(id="cls-001", name="Pilates", duration_minutes=60)
            result = ClassService().update_class(c)
            assert result.success
            assert result.data.name == "Pilates"

    def test_fails_when_no_id(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            c = Class(name="Yoga", duration_minutes=60)
            result = ClassService().update_class(c)
            assert not result.success
            mock_db.update.assert_not_called()

    def test_fails_when_class_not_found(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = []
            c = Class(id="cls-999", name="Yoga", duration_minutes=60)
            result = ClassService().update_class(c)
            assert not result.success

    def test_fails_on_validation_error(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            c = Class(id="cls-001", name="", duration_minutes=60)
            result = ClassService().update_class(c)
            assert not result.success
            mock_db.update.assert_not_called()


# ---------------------------------------------------------------------------
# toggle_class_status
# ---------------------------------------------------------------------------

class TestToggleClassStatus:
    def test_activates_class(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.update.return_value = [make_class_row(is_active=True)]
            result = ClassService().toggle_class_status("cls-001", True)
            assert result.success
            assert result.data is True

    def test_deactivates_class(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.update.return_value = [make_class_row(is_active=False)]
            result = ClassService().toggle_class_status("cls-001", False)
            assert result.success

    def test_fails_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.update.side_effect = Exception("DB error")
            result = ClassService().toggle_class_status("cls-001", True)
            assert not result.success


# ---------------------------------------------------------------------------
# get_schedules
# ---------------------------------------------------------------------------

class TestGetSchedules:
    def test_returns_active_schedules_by_default(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_schedule_row()]
            result = ClassService().get_schedules()
            assert result.success
            assert len(result.data) == 1

    def test_filters_by_class_id(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_schedule_row()]
            result = ClassService().get_schedules(class_id="cls-001")
            assert result.success
            call_kwargs = mock_db.select.call_args[1]
            assert call_kwargs['filters']['class_schedules.class_id'] == 'cls-001'

    def test_filters_by_day_of_week(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_schedule_row()]
            result = ClassService().get_schedules(day_of_week=1)
            assert result.success
            call_kwargs = mock_db.select.call_args[1]
            assert call_kwargs['filters']['class_schedules.day_of_week'] == 1

    def test_returns_fail_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            result = ClassService().get_schedules()
            assert not result.success


# ---------------------------------------------------------------------------
# create_schedule
# ---------------------------------------------------------------------------

class TestCreateSchedule:
    def test_creates_schedule_successfully(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.insert.return_value = make_schedule_row()
            s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="08:00", end_time="09:00")
            result = ClassService().create_schedule(s)
            assert result.success
            mock_db.insert.assert_called_once()

    def test_fails_when_no_class_id(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            s = ClassSchedule(class_id="", day_of_week=1, start_time="08:00", end_time="09:00")
            result = ClassService().create_schedule(s)
            assert not result.success
            mock_db.insert.assert_not_called()

    def test_fails_when_start_after_end(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="10:00", end_time="09:00")
            result = ClassService().create_schedule(s)
            assert not result.success
            mock_db.insert.assert_not_called()

    def test_fails_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.insert.side_effect = Exception("DB error")
            s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="08:00", end_time="09:00")
            result = ClassService().create_schedule(s)
            assert not result.success


# ---------------------------------------------------------------------------
# update_schedule
# ---------------------------------------------------------------------------

class TestUpdateSchedule:
    def test_updates_schedule_successfully(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_schedule_row()]
            mock_db.update.return_value = [make_schedule_row(room="Studio B")]
            s = ClassSchedule(id="sched-001", class_id="cls-001", day_of_week=1, start_time="08:00", end_time="09:00")
            result = ClassService().update_schedule(s)
            assert result.success

    def test_fails_when_no_id(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            s = ClassSchedule(class_id="cls-001", day_of_week=1, start_time="08:00", end_time="09:00")
            result = ClassService().update_schedule(s)
            assert not result.success
            mock_db.update.assert_not_called()

    def test_fails_when_not_found(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = []
            s = ClassSchedule(id="sched-999", class_id="cls-001", day_of_week=1, start_time="08:00", end_time="09:00")
            result = ClassService().update_schedule(s)
            assert not result.success


# ---------------------------------------------------------------------------
# toggle_schedule_status
# ---------------------------------------------------------------------------

class TestToggleScheduleStatus:
    def test_deactivates_schedule(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.update.return_value = [make_schedule_row(is_active=False)]
            result = ClassService().toggle_schedule_status("sched-001", False)
            assert result.success

    def test_activates_schedule(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.update.return_value = [make_schedule_row(is_active=True)]
            result = ClassService().toggle_schedule_status("sched-001", True)
            assert result.success

    def test_fails_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.update.side_effect = Exception("DB error")
            result = ClassService().toggle_schedule_status("sched-001", True)
            assert not result.success


# ---------------------------------------------------------------------------
# get_enrollments
# ---------------------------------------------------------------------------

class TestGetEnrollments:
    def test_returns_all_enrollments(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_enrollment_row()]
            result = ClassService().get_enrollments()
            assert result.success
            assert len(result.data) == 1

    def test_filters_by_status(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_enrollment_row()]
            result = ClassService().get_enrollments(status=EnrollmentStatus.ENROLLED)
            assert result.success
            call_kwargs = mock_db.select.call_args[1]
            assert call_kwargs['filters']['class_enrollments.status'] == 'enrolled'

    def test_filters_by_class_date(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_enrollment_row()]
            target_date = date(2026, 5, 19)
            result = ClassService().get_enrollments(class_date=target_date)
            assert result.success
            call_kwargs = mock_db.select.call_args[1]
            assert call_kwargs['filters']['class_enrollments.class_date'] == '2026-05-19'

    def test_search_term_filters_in_python(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            rows = [
                make_enrollment_row(first_name="John",  last_name="Doe",   member_code="MEM-001"),
                make_enrollment_row(id="enr-002", first_name="Jane", last_name="Smith", member_code="MEM-002"),
            ]
            mock_db.select.return_value = rows
            result = ClassService().get_enrollments(search_term="john")
            assert result.success
            assert len(result.data) == 1
            assert result.data[0].member.first_name == "John"

    def test_returns_fail_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            result = ClassService().get_enrollments()
            assert not result.success


# ---------------------------------------------------------------------------
# enroll_member
# ---------------------------------------------------------------------------

class TestEnrollMember:
    def test_enrolls_member_successfully(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = [
                [],             # no duplicate enrollment
                [make_schedule_row()],  # capacity check — schedule lookup
            ]
            mock_db.insert.return_value = make_enrollment_row()
            result = ClassService().enroll_member(
                schedule_id="sched-001",
                member_id="mem-001",
                class_date=date(2026, 5, 19),
            )
            assert result.success
            mock_db.insert.assert_called_once()

    def test_fails_when_already_enrolled(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            # First select returns existing enrollment (duplicate)
            mock_db.select.return_value = [make_enrollment_row()]
            result = ClassService().enroll_member(
                schedule_id="sched-001",
                member_id="mem-001",
                class_date=date(2026, 5, 19),
            )
            assert not result.success
            assert "already enrolled" in result.error.lower()
            mock_db.insert.assert_not_called()

    def test_fails_when_class_full(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            # No duplicate, but class is at capacity (max_capacity=1, 1 existing)
            mock_db.select.side_effect = [
                [],                         # no duplicate
                [make_schedule_row(max_capacity=1)],  # schedule lookup (capacity check)
                [make_enrollment_row()],    # count existing enrollments
            ]
            result = ClassService().enroll_member(
                schedule_id="sched-001",
                member_id="mem-002",
                class_date=date(2026, 5, 19),
            )
            assert not result.success
            assert "capacity" in result.error.lower()

    def test_unlimited_capacity_always_allows_enrollment(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = [
                [],  # no duplicate
                [make_schedule_row(max_capacity=None)],  # unlimited capacity
            ]
            mock_db.insert.return_value = make_enrollment_row()
            result = ClassService().enroll_member(
                schedule_id="sched-001",
                member_id="mem-002",
                class_date=date(2026, 5, 19),
            )
            assert result.success

    def test_fails_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            result = ClassService().enroll_member(
                schedule_id="sched-001",
                member_id="mem-001",
                class_date=date(2026, 5, 19),
            )
            assert not result.success


# ---------------------------------------------------------------------------
# update_enrollment_status
# ---------------------------------------------------------------------------

class TestUpdateEnrollmentStatus:
    def test_marks_as_attended(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_enrollment_row()]
            mock_db.update.return_value = [make_enrollment_row(status="attended")]
            result = ClassService().update_enrollment_status("enr-001", EnrollmentStatus.ATTENDED)
            assert result.success
            assert result.data is True

    def test_marks_as_absent(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_enrollment_row()]
            mock_db.update.return_value = [make_enrollment_row(status="absent")]
            result = ClassService().update_enrollment_status("enr-001", EnrollmentStatus.ABSENT)
            assert result.success

    def test_cancels_enrollment(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [make_enrollment_row()]
            mock_db.update.return_value = [make_enrollment_row(status="cancelled")]
            result = ClassService().update_enrollment_status("enr-001", EnrollmentStatus.CANCELLED)
            assert result.success

    def test_returns_not_found_when_missing(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = []
            result = ClassService().update_enrollment_status("enr-999", EnrollmentStatus.ATTENDED)
            assert not result.success
            assert result.is_not_found
            mock_db.update.assert_not_called()

    def test_fails_on_db_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            result = ClassService().update_enrollment_status("enr-001", EnrollmentStatus.ATTENDED)
            assert not result.success


# ---------------------------------------------------------------------------
# get_enrollment_count
# ---------------------------------------------------------------------------

class TestGetEnrollmentCount:
    def test_counts_non_cancelled_enrollments(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = [
                make_enrollment_row(status="enrolled"),
                make_enrollment_row(id="enr-002", status="attended"),
                make_enrollment_row(id="enr-003", status="cancelled"),
            ]
            count = ClassService().get_enrollment_count("sched-001", date(2026, 5, 19))
            assert count == 2  # cancelled excluded

    def test_returns_zero_on_exception(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.side_effect = Exception("DB error")
            count = ClassService().get_enrollment_count("sched-001", date(2026, 5, 19))
            assert count == 0

    def test_returns_zero_when_empty(self):
        with patch('src.services.class_service.db_manager') as mock_db:
            mock_db.select.return_value = []
            count = ClassService().get_enrollment_count("sched-001", date(2026, 5, 19))
            assert count == 0
