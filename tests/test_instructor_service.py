"""
Tests for InstructorService.

All database interactions are isolated by patching the global `db_manager`
singleton that `instructor_service` imports at module level.

Patch target: 'src.services.instructor_service.db_manager'
"""
from unittest.mock import patch
from datetime import date

from src.services.instructor_service import InstructorService
from src.models.models import Instructor


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_instructor(**kwargs) -> Instructor:
    """Factory for a valid Instructor with sensible defaults."""
    defaults = dict(
        id="uuid-001",
        first_name="Jane",
        last_name="Fit",
        email="jane@example.com",
        phone="555-1234",
        specialties=["Yoga", "Pilates"],
        certifications="RYT-200",
        hire_date=date(2022, 1, 10),
        is_active=True,
    )
    defaults.update(kwargs)
    return Instructor(**defaults)


def make_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the instructors table schema."""
    defaults = dict(
        id="uuid-001",
        user_id=None,
        first_name="Jane",
        last_name="Fit",
        email="jane@example.com",
        phone="555-1234",
        specialties=["Yoga", "Pilates"],
        certifications="RYT-200",
        hire_date=date(2022, 1, 10),
        photo_url=None,
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _validate_instructor  (pure static — no mocks required)
# ---------------------------------------------------------------------------

class TestValidateInstructor:
    def setup_method(self):
        self.svc = InstructorService()

    def test_valid_instructor_returns_none(self):
        assert self.svc._validate_instructor(make_instructor()) is None

    def test_missing_first_name_returns_error(self):
        i = make_instructor(first_name="")
        assert self.svc._validate_instructor(i) == "First name is required"

    def test_whitespace_only_first_name_returns_error(self):
        i = make_instructor(first_name="   ")
        assert self.svc._validate_instructor(i) == "First name is required"

    def test_missing_last_name_returns_error(self):
        i = make_instructor(last_name="")
        assert self.svc._validate_instructor(i) == "Last name is required"

    def test_whitespace_only_last_name_returns_error(self):
        i = make_instructor(last_name="   ")
        assert self.svc._validate_instructor(i) == "Last name is required"

    def test_invalid_email_returns_error(self):
        i = make_instructor(email="not-an-email")
        error = self.svc._validate_instructor(i)
        assert error is not None
        assert "not a valid email address" in error

    def test_email_without_at_sign_returns_error(self):
        i = make_instructor(email="bademail.com")
        assert self.svc._validate_instructor(i) is not None

    def test_none_email_is_accepted(self):
        i = make_instructor(email=None)
        assert self.svc._validate_instructor(i) is None


# ---------------------------------------------------------------------------
# _row_to_instructor  (pure static)
# ---------------------------------------------------------------------------

class TestRowToInstructor:
    def test_basic_fields_are_mapped(self):
        row = make_row()
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.id == "uuid-001"
        assert instructor.first_name == "Jane"
        assert instructor.last_name == "Fit"
        assert instructor.email == "jane@example.com"

    def test_specialties_list_is_preserved(self):
        row = make_row(specialties=["CrossFit", "HIIT"])
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.specialties == ["CrossFit", "HIIT"]

    def test_null_specialties_becomes_empty_list(self):
        row = make_row(specialties=None)
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.specialties == []

    def test_empty_specialties_becomes_empty_list(self):
        row = make_row(specialties=[])
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.specialties == []

    def test_is_active_defaults_to_true_when_missing(self):
        row = make_row()
        row.pop("is_active")
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.is_active is True

    def test_is_active_false_is_preserved(self):
        row = make_row(is_active=False)
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.is_active is False

    def test_full_name_property(self):
        row = make_row(first_name="John", last_name="Doe")
        instructor = InstructorService._row_to_instructor(row)
        assert instructor.full_name == "John Doe"


# ---------------------------------------------------------------------------
# _instructor_to_row  (pure static)
# ---------------------------------------------------------------------------

class TestInstructorToRow:
    def test_basic_string_fields_are_present(self):
        i = make_instructor()
        row = InstructorService._instructor_to_row(i)
        assert row["first_name"] == "Jane"
        assert row["last_name"] == "Fit"
        assert row["email"] == "jane@example.com"

    def test_first_and_last_name_are_stripped(self):
        i = make_instructor(first_name="  Jane  ", last_name="  Fit  ")
        row = InstructorService._instructor_to_row(i)
        assert row["first_name"] == "Jane"
        assert row["last_name"] == "Fit"

    def test_specialties_list_is_present(self):
        i = make_instructor(specialties=["Yoga"])
        row = InstructorService._instructor_to_row(i)
        assert row["specialties"] == ["Yoga"]

    def test_none_specialties_becomes_empty_list(self):
        i = make_instructor(specialties=None)
        row = InstructorService._instructor_to_row(i)
        assert row["specialties"] == []

    def test_hire_date_is_isoformatted(self):
        i = make_instructor(hire_date=date(2021, 5, 20))
        row = InstructorService._instructor_to_row(i)
        assert row["hire_date"] == "2021-05-20"

    def test_null_hire_date_stays_none(self):
        i = make_instructor(hire_date=None)
        row = InstructorService._instructor_to_row(i)
        assert row["hire_date"] is None


# ---------------------------------------------------------------------------
# get_all_instructors
# ---------------------------------------------------------------------------

class TestGetAllInstructors:
    def setup_method(self):
        self.svc = InstructorService()

    @patch("src.services.instructor_service.db_manager")
    def test_returns_list_of_instructors_on_success(self, mock_db):
        mock_db.select.return_value = [make_row(), make_row(id="uuid-002", first_name="Mark")]
        result = self.svc.get_all_instructors()
        assert result.success is True
        assert len(result.data) == 2

    @patch("src.services.instructor_service.db_manager")
    def test_active_only_passes_is_active_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_instructors(include_inactive=False)
        mock_db.select.assert_called_once_with(
            table="instructors",
            order_by="last_name",
            filters={"is_active": True},
        )

    @patch("src.services.instructor_service.db_manager")
    def test_include_inactive_passes_no_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_instructors(include_inactive=True)
        mock_db.select.assert_called_once_with(
            table="instructors",
            order_by="last_name",
            filters=None,
        )

    @patch("src.services.instructor_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("connection lost")
        result = self.svc.get_all_instructors()
        assert result.success is False
        assert "Could not retrieve instructors" in result.error

    @patch("src.services.instructor_service.db_manager")
    def test_empty_db_returns_empty_list(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_all_instructors()
        assert result.success is True
        assert result.data == []


# ---------------------------------------------------------------------------
# get_instructor_by_id
# ---------------------------------------------------------------------------

class TestGetInstructorById:
    def setup_method(self):
        self.svc = InstructorService()

    @patch("src.services.instructor_service.db_manager")
    def test_returns_instructor_when_found(self, mock_db):
        mock_db.select.return_value = [make_row()]
        result = self.svc.get_instructor_by_id("uuid-001")
        assert result.success is True
        assert result.data.id == "uuid-001"

    @patch("src.services.instructor_service.db_manager")
    def test_returns_fail_when_not_found(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_instructor_by_id("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    @patch("src.services.instructor_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("timeout")
        result = self.svc.get_instructor_by_id("uuid-001")
        assert result.success is False

    @patch("src.services.instructor_service.db_manager")
    def test_queries_by_correct_id(self, mock_db):
        mock_db.select.return_value = [make_row()]
        self.svc.get_instructor_by_id("uuid-999")
        mock_db.select.assert_called_once_with(table="instructors", filters={"id": "uuid-999"})


# ---------------------------------------------------------------------------
# search_instructors
# ---------------------------------------------------------------------------

class TestSearchInstructors:
    def setup_method(self):
        self.svc = InstructorService()

    def test_empty_term_returns_fail(self):
        result = self.svc.search_instructors("")
        assert result.success is False
        assert "empty" in result.error.lower()

    def test_whitespace_only_term_returns_fail(self):
        result = self.svc.search_instructors("   ")
        assert result.success is False

    @patch("src.services.instructor_service.db_manager")
    def test_searches_all_three_columns_by_default(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_instructors("jane")
        assert mock_db.search.call_count == 3
        called_columns = {c.kwargs["column"] for c in mock_db.search.call_args_list}
        assert called_columns == {"first_name", "last_name", "email"}

    @patch("src.services.instructor_service.db_manager")
    def test_single_column_search_calls_db_once(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_instructors("jane", column="first_name")
        assert mock_db.search.call_count == 1
        mock_db.search.assert_called_once_with(
            table="instructors",
            column="first_name",
            search_term="jane",
            filters={"is_active": True},
        )

    @patch("src.services.instructor_service.db_manager")
    def test_invalid_column_falls_back_to_all_columns(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_instructors("jane", column="specialties")
        assert mock_db.search.call_count == 3

    @patch("src.services.instructor_service.db_manager")
    def test_deduplicates_results_across_columns(self, mock_db):
        row = make_row()  # same id appears in two column results
        mock_db.search.return_value = [row]
        result = self.svc.search_instructors("jane")
        assert result.success is True
        assert len(result.data) == 1  # deduplicated from 3 calls -> 1 unique

    @patch("src.services.instructor_service.db_manager")
    def test_term_is_stripped_before_search(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_instructors("  jane  ", column="first_name")
        mock_db.search.assert_called_once_with(
            table="instructors",
            column="first_name",
            search_term="jane",
            filters={"is_active": True},
        )

    @patch("src.services.instructor_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.search.side_effect = Exception("db error")
        result = self.svc.search_instructors("jane")
        assert result.success is False
        assert "Search failed" in result.error


# ---------------------------------------------------------------------------
# create_instructor
# ---------------------------------------------------------------------------

class TestCreateInstructor:
    def setup_method(self):
        self.svc = InstructorService()

    @patch("src.services.instructor_service.db_manager")
    def test_creates_instructor_successfully(self, mock_db):
        mock_db.select.return_value = []  # no duplicate email
        mock_db.insert.return_value = make_row()
        result = self.svc.create_instructor(make_instructor(id=None))
        assert result.success is True
        assert result.data is not None

    @patch("src.services.instructor_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        result = self.svc.create_instructor(make_instructor(first_name=""))
        mock_db.insert.assert_not_called()
        assert result.success is False

    @patch("src.services.instructor_service.db_manager")
    def test_duplicate_email_returns_fail(self, mock_db):
        mock_db.select.return_value = [make_row()]  # email already exists
        result = self.svc.create_instructor(make_instructor())
        assert result.success is False
        assert "already registered" in result.error

    @patch("src.services.instructor_service.db_manager")
    def test_no_email_skips_duplicate_check(self, mock_db):
        mock_db.insert.return_value = make_row(email=None)
        result = self.svc.create_instructor(make_instructor(email=None))
        mock_db.select.assert_not_called()
        assert result.success is True

    @patch("src.services.instructor_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.return_value = []
        mock_db.insert.side_effect = Exception("insert failed")
        result = self.svc.create_instructor(make_instructor())
        assert result.success is False
        assert "Could not create instructor" in result.error


# ---------------------------------------------------------------------------
# update_instructor
# ---------------------------------------------------------------------------

class TestUpdateInstructor:
    def setup_method(self):
        self.svc = InstructorService()

    @patch("src.services.instructor_service.db_manager")
    def test_updates_instructor_successfully(self, mock_db):
        mock_db.select.side_effect = [
            [make_row()],   # existence check
            [],             # email uniqueness: no conflict
        ]
        mock_db.update.return_value = [make_row(first_name="Updated")]
        result = self.svc.update_instructor(make_instructor())
        assert result.success is True
        assert result.data.first_name == "Updated"

    def test_missing_id_returns_fail(self):
        result = self.svc.update_instructor(make_instructor(id=None))
        assert result.success is False
        assert "id is required" in result.error

    @patch("src.services.instructor_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        result = self.svc.update_instructor(make_instructor(first_name=""))
        mock_db.update.assert_not_called()
        assert result.success is False

    @patch("src.services.instructor_service.db_manager")
    def test_instructor_not_in_db_returns_fail(self, mock_db):
        mock_db.select.return_value = []  # existence check: not found
        result = self.svc.update_instructor(make_instructor())
        assert result.success is False
        assert "not found" in result.error

    @patch("src.services.instructor_service.db_manager")
    def test_email_conflict_with_another_instructor_returns_fail(self, mock_db):
        mock_db.select.side_effect = [
            [make_row()],                  # existence check OK
            [make_row(id="uuid-OTHER")],   # email used by different instructor
        ]
        result = self.svc.update_instructor(make_instructor())
        assert result.success is False
        assert "already in use" in result.error

    @patch("src.services.instructor_service.db_manager")
    def test_same_email_on_same_instructor_is_allowed(self, mock_db):
        """Updating an instructor with their own email should not trigger conflict."""
        mock_db.select.side_effect = [
            [make_row()],               # existence check
            [make_row(id="uuid-001")],  # email check: same instructor id -> no conflict
        ]
        mock_db.update.return_value = [make_row()]
        result = self.svc.update_instructor(make_instructor())
        assert result.success is True

    @patch("src.services.instructor_service.db_manager")
    def test_immutable_fields_are_stripped_from_update_payload(self, mock_db):
        mock_db.select.side_effect = [[make_row()], []]
        mock_db.update.return_value = [make_row()]
        self.svc.update_instructor(make_instructor())
        update_data = mock_db.update.call_args.kwargs["data"]
        assert "created_at" not in update_data

    @patch("src.services.instructor_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = [[make_row()], []]
        mock_db.update.side_effect = Exception("update failed")
        result = self.svc.update_instructor(make_instructor())
        assert result.success is False
        assert "Could not update instructor" in result.error
