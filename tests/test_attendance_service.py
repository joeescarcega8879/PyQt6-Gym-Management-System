"""
Tests for AttendanceService.

All database interactions are isolated by patching the global `db_manager`
singleton that `attendance_service` imports at module level.

Patch target: 'src.services.attendance_service.db_manager'
"""
import pytest
from unittest.mock import patch
from datetime import datetime, date, timezone

from src.services.attendance_service import AttendanceService


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_attendance_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the attendance table schema (with member join columns)."""
    defaults = dict(
        id="att-001",
        member_id="mem-001",
        check_in_time="2026-03-25T09:00:00+00:00",
        check_out_time=None,
        notes=None,
        created_by="user-001",
        member_code="GYM001",
        first_name="John",
        last_name="Doe",
    )
    defaults.update(kwargs)
    return defaults


def make_closed_row(**kwargs) -> dict:
    """Factory for a completed attendance row (check-out already set)."""
    return make_attendance_row(check_out_time="2026-03-25T11:00:00+00:00", **kwargs)


def make_member_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the members table schema."""
    defaults = dict(
        id="mem-001",
        member_code="GYM001",
        first_name="John",
        last_name="Doe",
        is_active=True,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _row_to_attendance  (pure static)
# ---------------------------------------------------------------------------

class TestRowToAttendance:
    def setup_method(self):
        self.svc = AttendanceService()

    def test_basic_fields_are_mapped(self):
        att = self.svc._row_to_attendance(make_attendance_row())
        assert att.id == "att-001"
        assert att.member_id == "mem-001"
        assert att.created_by == "user-001"

    def test_check_out_time_is_none_when_missing(self):
        att = self.svc._row_to_attendance(make_attendance_row())
        assert att.check_out_time is None

    def test_check_out_time_is_parsed_when_present(self):
        att = self.svc._row_to_attendance(make_closed_row())
        assert att.check_out_time is not None
        assert isinstance(att.check_out_time, datetime)

    def test_check_in_time_is_parsed_correctly(self):
        att = self.svc._row_to_attendance(make_attendance_row())
        assert att.check_in_time.year == 2026
        assert att.check_in_time.month == 3
        assert att.check_in_time.day == 25

    def test_populates_member_relation(self):
        att = self.svc._row_to_attendance(make_attendance_row())
        assert att.member is not None
        assert att.member.member_code == "GYM001"
        assert att.member.full_name == "John Doe"

    def test_member_id_assigned_to_member_object(self):
        att = self.svc._row_to_attendance(make_attendance_row())
        assert att.member.id == "mem-001"

    def test_no_member_relation_stays_none(self):
        row = make_attendance_row(member_code=None)
        att = self.svc._row_to_attendance(row)
        assert att.member is None

    def test_invalid_check_in_time_falls_back_to_now(self):
        row = make_attendance_row(check_in_time="not-a-date")
        att = self.svc._row_to_attendance(row)
        # Falls back to datetime.now() — just check it's a datetime
        assert isinstance(att.check_in_time, datetime)

    def test_datetime_instance_is_accepted_directly(self):
        dt = datetime(2026, 3, 25, 9, 0, 0)
        row = make_attendance_row(check_in_time=dt)
        att = self.svc._row_to_attendance(row)
        assert att.check_in_time == dt


# ---------------------------------------------------------------------------
# _row_to_member  (pure static)
# ---------------------------------------------------------------------------

class TestRowToMember:
    def test_basic_fields_are_mapped(self):
        member = AttendanceService._row_to_member(make_member_row())
        assert member.id == "mem-001"
        assert member.member_code == "GYM001"
        assert member.first_name == "John"
        assert member.last_name == "Doe"

    def test_full_name_property_works(self):
        member = AttendanceService._row_to_member(make_member_row())
        assert member.full_name == "John Doe"

    def test_is_active_true_is_preserved(self):
        member = AttendanceService._row_to_member(make_member_row())
        assert member.is_active is True

    def test_is_active_defaults_to_true_when_missing(self):
        row = make_member_row()
        row.pop("is_active")
        member = AttendanceService._row_to_member(row)
        assert member.is_active is True


# ---------------------------------------------------------------------------
# get_attendance_by_date
# ---------------------------------------------------------------------------

class TestGetAttendanceByDate:
    def setup_method(self):
        self.svc = AttendanceService()

    @patch("src.services.attendance_service.db_manager")
    def test_returns_records_matching_the_date(self, mock_db):
        mock_db.select_range.return_value = [make_attendance_row()]
        result = self.svc.get_attendance_by_date(date(2026, 3, 25))
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.attendance_service.db_manager")
    def test_returns_empty_list_when_no_records(self, mock_db):
        mock_db.select_range.return_value = []
        result = self.svc.get_attendance_by_date(date(2026, 3, 25))
        assert result.success is True
        assert result.data == []

    @patch("src.services.attendance_service.db_manager")
    def test_returns_multiple_records_for_same_day(self, mock_db):
        row2 = make_attendance_row(id="att-002", member_id="mem-002")
        mock_db.select_range.return_value = [make_attendance_row(), row2]
        result = self.svc.get_attendance_by_date(date(2026, 3, 25))
        assert result.success is True
        assert len(result.data) == 2

    @patch("src.services.attendance_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select_range.side_effect = Exception("connection lost")
        result = self.svc.get_attendance_by_date(date(2026, 3, 25))
        assert result.success is False
        assert result.error is not None

    @patch("src.services.attendance_service.db_manager")
    def test_queries_attendance_table_with_member_join(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_attendance_by_date(date(2026, 3, 25))
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs["table"] == "attendance"
        assert "members.first_name" in call_kwargs["columns"]
        assert call_kwargs["joins"] is not None

    @patch("src.services.attendance_service.db_manager")
    def test_filters_by_check_in_time_column(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_attendance_by_date(date(2026, 3, 25))
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs["column"] == "check_in_time"
        assert "+00:00" in call_kwargs["start"]
        assert "+00:00" in call_kwargs["end"]


# ---------------------------------------------------------------------------
# search_member_for_checkin
# ---------------------------------------------------------------------------

class TestSearchMemberForCheckin:
    def setup_method(self):
        self.svc = AttendanceService()

    @patch("src.services.attendance_service.db_manager")
    def test_finds_member_by_code(self, mock_db):
        mock_db.search.side_effect = [[make_member_row()], []]
        result = self.svc.search_member_for_checkin("GYM001")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.attendance_service.db_manager")
    def test_finds_member_by_name(self, mock_db):
        mock_db.search.side_effect = [[], [make_member_row()]]
        result = self.svc.search_member_for_checkin("John")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.attendance_service.db_manager")
    def test_deduplicates_when_member_appears_in_both_searches(self, mock_db):
        row = make_member_row()
        mock_db.search.side_effect = [[row], [row]]
        result = self.svc.search_member_for_checkin("John")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.attendance_service.db_manager")
    def test_returns_not_found_when_no_match(self, mock_db):
        mock_db.search.side_effect = [[], []]
        result = self.svc.search_member_for_checkin("UNKNOWN")
        assert result.success is False
        assert result.is_not_found is True

    @patch("src.services.attendance_service.db_manager")
    def test_passes_is_active_filter_to_both_searches(self, mock_db):
        mock_db.search.side_effect = [[], []]
        self.svc.search_member_for_checkin("John")
        for call in mock_db.search.call_args_list:
            assert call.kwargs["filters"] == {"is_active": True}

    @patch("src.services.attendance_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.search.side_effect = Exception("db error")
        result = self.svc.search_member_for_checkin("GYM001")
        assert result.success is False
        assert result.is_not_found is False


# ---------------------------------------------------------------------------
# check_in
# ---------------------------------------------------------------------------

class TestCheckIn:
    def setup_method(self):
        self.svc = AttendanceService()

    @patch("src.services.attendance_service.db_manager")
    def test_successful_checkin_returns_attendance(self, mock_db):
        mock_db.select_range.return_value = []          # no open check-ins today
        mock_db.insert.return_value = make_attendance_row()
        result = self.svc.check_in("mem-001", "user-001")
        assert result.success is True
        assert result.data.member_id == "mem-001"

    @patch("src.services.attendance_service.db_manager")
    def test_checkin_calls_insert_with_correct_table(self, mock_db):
        mock_db.select_range.return_value = []
        mock_db.insert.return_value = make_attendance_row()
        self.svc.check_in("mem-001")
        assert mock_db.insert.call_args.args[0] == "attendance"

    @patch("src.services.attendance_service.db_manager")
    def test_checkin_payload_contains_member_id_and_check_in_time(self, mock_db):
        mock_db.select_range.return_value = []
        mock_db.insert.return_value = make_attendance_row()
        self.svc.check_in("mem-001", "user-001")
        payload = mock_db.insert.call_args.args[1]
        assert payload["member_id"] == "mem-001"
        assert "check_in_time" in payload
        assert payload["created_by"] == "user-001"

    @patch("src.services.attendance_service.db_manager")
    def test_blocks_duplicate_open_checkin_today(self, mock_db):
        # Simulate an open check-in for today (UTC-aware timestamp)
        today_row = make_attendance_row(
            check_in_time=datetime.now(timezone.utc).replace(hour=9, minute=0, second=0).isoformat(),
            check_out_time=None,
        )
        mock_db.select_range.return_value = [today_row]
        result = self.svc.check_in("mem-001")
        assert result.success is False
        mock_db.insert.assert_not_called()

    @patch("src.services.attendance_service.db_manager")
    def test_allows_checkin_if_previous_was_checked_out(self, mock_db):
        # Closed check-in from today → new check-in is allowed
        closed_today = make_attendance_row(
            check_in_time=datetime.now(timezone.utc).replace(hour=9, minute=0, second=0).isoformat(),
            check_out_time=datetime.now(timezone.utc).replace(hour=11, minute=0, second=0).isoformat(),
        )
        mock_db.select_range.return_value = [closed_today]
        mock_db.insert.return_value = make_attendance_row()
        result = self.svc.check_in("mem-001")
        assert result.success is True

    @patch("src.services.attendance_service.db_manager")
    def test_created_by_is_none_when_not_provided(self, mock_db):
        mock_db.select_range.return_value = []
        mock_db.insert.return_value = make_attendance_row(created_by=None)
        self.svc.check_in("mem-001")
        payload = mock_db.insert.call_args.args[1]
        assert payload["created_by"] is None

    @patch("src.services.attendance_service.db_manager")
    def test_db_insert_exception_returns_failure(self, mock_db):
        mock_db.select_range.return_value = []
        mock_db.insert.side_effect = Exception("insert failed")
        result = self.svc.check_in("mem-001")
        assert result.success is False

    @patch("src.services.attendance_service.db_manager")
    def test_db_select_exception_during_validation_returns_failure(self, mock_db):
        mock_db.select_range.side_effect = Exception("select failed")
        result = self.svc.check_in("mem-001")
        assert result.success is False


# ---------------------------------------------------------------------------
# check_out
# ---------------------------------------------------------------------------

class TestCheckOut:
    def setup_method(self):
        self.svc = AttendanceService()

    @patch("src.services.attendance_service.db_manager")
    def test_successful_checkout_returns_attendance(self, mock_db):
        mock_db.update.return_value = [make_closed_row()]
        result = self.svc.check_out("att-001")
        assert result.success is True
        assert result.data.check_out_time is not None

    @patch("src.services.attendance_service.db_manager")
    def test_checkout_calls_update_on_correct_table(self, mock_db):
        mock_db.update.return_value = [make_closed_row()]
        self.svc.check_out("att-001")
        assert mock_db.update.call_args.kwargs["table"] == "attendance"

    @patch("src.services.attendance_service.db_manager")
    def test_checkout_filters_by_attendance_id(self, mock_db):
        mock_db.update.return_value = [make_closed_row()]
        self.svc.check_out("att-001")
        assert mock_db.update.call_args.kwargs["filters"] == {"id": "att-001"}

    @patch("src.services.attendance_service.db_manager")
    def test_checkout_sets_check_out_time(self, mock_db):
        mock_db.update.return_value = [make_closed_row()]
        self.svc.check_out("att-001")
        update_data = mock_db.update.call_args.kwargs["data"]
        assert "check_out_time" in update_data

    @patch("src.services.attendance_service.db_manager")
    def test_returns_failure_when_record_not_found(self, mock_db):
        mock_db.update.return_value = []
        result = self.svc.check_out("att-999")
        assert result.success is False
        assert "not found" in result.error.lower()

    @patch("src.services.attendance_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.update.side_effect = Exception("update failed")
        result = self.svc.check_out("att-001")
        assert result.success is False


# ---------------------------------------------------------------------------
# find_open_checkin_for_member
# ---------------------------------------------------------------------------

class TestFindOpenCheckinForMember:
    def setup_method(self):
        self.svc = AttendanceService()

    @patch("src.services.attendance_service.db_manager")
    def test_returns_open_record_when_found(self, mock_db):
        mock_db.select_range.return_value = [make_attendance_row()]  # check_out_time=None
        result = self.svc.find_open_checkin_for_member("mem-001")
        assert result.success is True
        assert result.data.id == "att-001"
        assert result.data.check_out_time is None

    @patch("src.services.attendance_service.db_manager")
    def test_returns_not_found_when_no_records_today(self, mock_db):
        mock_db.select_range.return_value = []
        result = self.svc.find_open_checkin_for_member("mem-001")
        assert result.success is False
        assert result.is_not_found is True

    @patch("src.services.attendance_service.db_manager")
    def test_returns_not_found_when_all_records_are_closed(self, mock_db):
        mock_db.select_range.return_value = [make_closed_row()]
        result = self.svc.find_open_checkin_for_member("mem-001")
        assert result.success is False
        assert result.is_not_found is True

    @patch("src.services.attendance_service.db_manager")
    def test_filters_by_member_id(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.find_open_checkin_for_member("mem-001")
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs["filters"] == {"member_id": "mem-001"}

    @patch("src.services.attendance_service.db_manager")
    def test_ignores_closed_records_and_returns_open_one(self, mock_db):
        open_row   = make_attendance_row(id="att-002", check_out_time=None)
        closed_row = make_closed_row(id="att-001")
        mock_db.select_range.return_value = [closed_row, open_row]
        result = self.svc.find_open_checkin_for_member("mem-001")
        assert result.success is True
        assert result.data.id == "att-002"

    @patch("src.services.attendance_service.db_manager")
    def test_queries_with_utc_aware_timestamps(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.find_open_checkin_for_member("mem-001")
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert "+00:00" in call_kwargs["start"]
        assert "+00:00" in call_kwargs["end"]

    @patch("src.services.attendance_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select_range.side_effect = Exception("db error")
        result = self.svc.find_open_checkin_for_member("mem-001")
        assert result.success is False
        assert result.is_not_found is False
