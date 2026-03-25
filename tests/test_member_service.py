"""
Tests for MemberService.

All Supabase interactions are isolated by patching the global `db_manager`
singleton that `member_service` imports at module level.

Patch target: 'src.services.member_service.db_manager'
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date

from src.services.member_service import MemberService
from src.models.models import Member
from src.models.enums import Gender


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_member(**kwargs) -> Member:
    """Factory for a valid Member with sensible defaults."""
    defaults = dict(
        id="uuid-001",
        member_code="MEM-AABBCCDD",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="555-1234",
        gender=Gender.MALE,
        is_active=True,
    )
    defaults.update(kwargs)
    return Member(**defaults)


def make_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the member table schema."""
    defaults = dict(
        id="uuid-001",
        member_code="MEM-AABBCCDD",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="555-1234",
        gender="male",
        address=None,
        emergency_contact_name=None,
        emergency_contact_phone=None,
        photo_url=None,
        notes=None,
        is_active=True,
        created_at=None,
        updated_at=None,
        created_by=None,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _validate_member  (pure static — no mocks required)
# ---------------------------------------------------------------------------

class TestValidateMember:
    def setup_method(self):
        self.svc = MemberService()

    def test_valid_member_returns_none(self):
        assert self.svc._validate_member(make_member()) is None

    def test_missing_first_name_returns_error(self):
        m = make_member(first_name="")
        assert self.svc._validate_member(m) == "First name is required"

    def test_whitespace_only_first_name_returns_error(self):
        m = make_member(first_name="   ")
        assert self.svc._validate_member(m) == "First name is required"

    def test_missing_last_name_returns_error(self):
        m = make_member(last_name="")
        assert self.svc._validate_member(m) == "Last name is required"

    def test_whitespace_only_last_name_returns_error(self):
        m = make_member(last_name="   ")
        assert self.svc._validate_member(m) == "Last name is required"

    def test_invalid_email_returns_error(self):
        m = make_member(email="not-an-email")
        error = self.svc._validate_member(m)
        assert error is not None
        assert "not a valid email address" in error

    def test_email_without_at_sign_returns_error(self):
        m = make_member(email="bademail.com")
        assert self.svc._validate_member(m) is not None

    def test_none_email_is_accepted(self):
        m = make_member(email=None)
        assert self.svc._validate_member(m) is None


# ---------------------------------------------------------------------------
# _generate_member_code  (pure static)
# ---------------------------------------------------------------------------

class TestGenerateMemberCode:
    def test_code_starts_with_MEM_prefix(self):
        code = MemberService._generate_member_code()
        assert code.startswith("MEM-")

    def test_code_has_correct_length(self):
        # "MEM-" (4) + 8 hex chars = 12 total
        code = MemberService._generate_member_code()
        assert len(code) == 12

    def test_code_suffix_is_uppercase(self):
        code = MemberService._generate_member_code()
        suffix = code[4:]
        assert suffix == suffix.upper()

    def test_two_codes_are_unique(self):
        assert MemberService._generate_member_code() != MemberService._generate_member_code()


# ---------------------------------------------------------------------------
# _row_to_member  (pure static)
# ---------------------------------------------------------------------------

class TestRowToMember:
    def test_basic_fields_are_mapped(self):
        row = make_row()
        member = MemberService._row_to_member(row)
        assert member.id == "uuid-001"
        assert member.first_name == "John"
        assert member.last_name == "Doe"
        assert member.email == "john@example.com"

    def test_gender_string_is_converted_to_enum(self):
        row = make_row(gender="female")
        member = MemberService._row_to_member(row)
        assert member.gender == Gender.FEMALE

    def test_null_gender_stays_none(self):
        row = make_row(gender=None)
        member = MemberService._row_to_member(row)
        assert member.gender is None

    def test_is_active_defaults_to_true_when_missing(self):
        row = make_row()
        row.pop("is_active")
        member = MemberService._row_to_member(row)
        assert member.is_active is True

    def test_is_active_false_is_preserved(self):
        row = make_row(is_active=False)
        member = MemberService._row_to_member(row)
        assert member.is_active is False


# ---------------------------------------------------------------------------
# _member_to_row  (pure static)
# ---------------------------------------------------------------------------

class TestMemberToRow:
    def test_basic_string_fields_are_present(self):
        m = make_member()
        row = MemberService._member_to_row(m)
        assert row["first_name"] == "John"
        assert row["last_name"] == "Doe"
        assert row["email"] == "john@example.com"

    def test_first_and_last_name_are_stripped(self):
        m = make_member(first_name="  Jane  ", last_name="  Smith  ")
        row = MemberService._member_to_row(m)
        assert row["first_name"] == "Jane"
        assert row["last_name"] == "Smith"

    def test_gender_enum_is_converted_to_string(self):
        m = make_member(gender=Gender.MALE)
        row = MemberService._member_to_row(m)
        assert row["gender"] == "male"

    def test_none_gender_is_none_in_row(self):
        m = make_member(gender=None)
        row = MemberService._member_to_row(m)
        assert row["gender"] is None

    def test_date_of_birth_is_isoformatted(self):
        m = make_member(date_of_birth=date(1990, 6, 15))
        row = MemberService._member_to_row(m)
        assert row["date_of_birth"] == "1990-06-15"

    def test_null_date_of_birth_stays_none(self):
        m = make_member(date_of_birth=None)
        row = MemberService._member_to_row(m)
        assert row["date_of_birth"] is None

    def test_member_code_is_included_when_present(self):
        m = make_member(member_code="MEM-AABB1122")
        row = MemberService._member_to_row(m)
        assert row["member_code"] == "MEM-AABB1122"

    def test_member_code_is_excluded_when_empty(self):
        m = make_member(member_code="")
        row = MemberService._member_to_row(m)
        assert "member_code" not in row


# ---------------------------------------------------------------------------
# get_all_members
# ---------------------------------------------------------------------------

class TestGetAllMembers:
    def setup_method(self):
        self.svc = MemberService()

    @patch("src.services.member_service.db_manager")
    def test_returns_list_of_members_on_success(self, mock_db):
        mock_db.select.return_value = [make_row(), make_row(id="uuid-002", first_name="Jane")]
        result = self.svc.get_all_members()
        assert result.success is True
        assert len(result.data) == 2

    @patch("src.services.member_service.db_manager")
    def test_active_only_passes_is_active_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_members(include_inactive=False)
        mock_db.select.assert_called_once_with(
            table="members",
            order_by="last_name",
            filters={"is_active": True},
        )

    @patch("src.services.member_service.db_manager")
    def test_include_inactive_passes_no_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_members(include_inactive=True)
        mock_db.select.assert_called_once_with(
            table="members",
            order_by="last_name",
            filters=None,
        )

    @patch("src.services.member_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("connection lost")
        result = self.svc.get_all_members()
        assert result.success is False
        assert "Could not retrieve members" in result.error

    @patch("src.services.member_service.db_manager")
    def test_empty_db_returns_empty_list(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_all_members()
        assert result.success is True
        assert result.data == []


# ---------------------------------------------------------------------------
# get_member_by_id
# ---------------------------------------------------------------------------

class TestGetMemberById:
    def setup_method(self):
        self.svc = MemberService()

    @patch("src.services.member_service.db_manager")
    def test_returns_member_when_found(self, mock_db):
        mock_db.select.return_value = [make_row()]
        result = self.svc.get_member_by_id("uuid-001")
        assert result.success is True
        assert result.data.id == "uuid-001"

    @patch("src.services.member_service.db_manager")
    def test_returns_fail_when_not_found(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_member_by_id("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    @patch("src.services.member_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("timeout")
        result = self.svc.get_member_by_id("uuid-001")
        assert result.success is False

    @patch("src.services.member_service.db_manager")
    def test_queries_by_correct_id(self, mock_db):
        mock_db.select.return_value = [make_row()]
        self.svc.get_member_by_id("uuid-999")
        mock_db.select.assert_called_once_with(table="members", filters={"id": "uuid-999"})


# ---------------------------------------------------------------------------
# get_member_by_code
# ---------------------------------------------------------------------------

class TestGetMemberByCode:
    def setup_method(self):
        self.svc = MemberService()

    @patch("src.services.member_service.db_manager")
    def test_returns_member_when_found(self, mock_db):
        mock_db.select.return_value = [make_row()]
        result = self.svc.get_member_by_code("MEM-AABBCCDD")
        assert result.success is True

    @patch("src.services.member_service.db_manager")
    def test_returns_not_found_when_missing(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_member_by_code("MEM-XXXXXXXX")
        assert result.success is False
        assert result.is_not_found is True

    @patch("src.services.member_service.db_manager")
    def test_not_found_error_contains_code(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_member_by_code("MEM-XXXXXXXX")
        assert "MEM-XXXXXXXX" in result.error

    @patch("src.services.member_service.db_manager")
    def test_db_exception_returns_fail_not_not_found(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_member_by_code("MEM-AABBCCDD")
        assert result.success is False
        assert result.is_not_found is False


# ---------------------------------------------------------------------------
# search_members
# ---------------------------------------------------------------------------

class TestSearchMembers:
    def setup_method(self):
        self.svc = MemberService()

    def test_empty_term_returns_fail(self):
        result = self.svc.search_members("")
        assert result.success is False
        assert "empty" in result.error.lower()

    def test_whitespace_only_term_returns_fail(self):
        result = self.svc.search_members("   ")
        assert result.success is False

    @patch("src.services.member_service.db_manager")
    def test_searches_all_three_columns_by_default(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_members("john")
        assert mock_db.search.call_count == 3
        called_columns = {c.kwargs["column"] for c in mock_db.search.call_args_list}
        assert called_columns == {"first_name", "last_name", "email"}

    @patch("src.services.member_service.db_manager")
    def test_single_column_search_calls_db_once(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_members("john", column="first_name")
        assert mock_db.search.call_count == 1
        mock_db.search.assert_called_once_with(
            table="members",
            column="first_name",
            search_term="john",
            filters={"is_active": True},
        )

    @patch("src.services.member_service.db_manager")
    def test_invalid_column_falls_back_to_all_columns(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_members("john", column="member_code")
        assert mock_db.search.call_count == 3

    @patch("src.services.member_service.db_manager")
    def test_deduplicates_results_across_columns(self, mock_db):
        row = make_row()  # same id appears in two column results
        mock_db.search.return_value = [row]
        result = self.svc.search_members("john")
        assert result.success is True
        assert len(result.data) == 1  # deduplicated from 3 calls → 1 unique

    @patch("src.services.member_service.db_manager")
    def test_term_is_stripped_before_search(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_members("  john  ", column="first_name")
        mock_db.search.assert_called_once_with(
            table="members",
            column="first_name",
            search_term="john",
            filters={"is_active": True},
        )

    @patch("src.services.member_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.search.side_effect = Exception("db error")
        result = self.svc.search_members("john")
        assert result.success is False
        assert "Search failed" in result.error


# ---------------------------------------------------------------------------
# create_member
# ---------------------------------------------------------------------------

class TestCreateMember:
    def setup_method(self):
        self.svc = MemberService()

    @patch("src.services.member_service.db_manager")
    def test_creates_member_successfully(self, mock_db):
        mock_db.select.return_value = []   # no duplicate email
        mock_db.insert.return_value = make_row()
        result = self.svc.create_member(make_member(id=None, member_code=""))
        assert result.success is True
        assert result.data is not None

    @patch("src.services.member_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        result = self.svc.create_member(make_member(first_name=""))
        mock_db.insert.assert_not_called()
        assert result.success is False

    @patch("src.services.member_service.db_manager")
    def test_duplicate_email_returns_fail(self, mock_db):
        mock_db.select.return_value = [make_row()]   # email already exists
        result = self.svc.create_member(make_member())
        assert result.success is False
        assert "already registered" in result.error

    @patch("src.services.member_service.db_manager")
    def test_auto_generates_member_code_when_empty(self, mock_db):
        mock_db.select.return_value = []
        mock_db.insert.return_value = make_row()
        member = make_member(member_code="")
        self.svc.create_member(member)
        # After the call, member_code should have been set
        assert member.member_code.startswith("MEM-")

    @patch("src.services.member_service.db_manager")
    def test_existing_member_code_is_preserved(self, mock_db):
        mock_db.select.return_value = []
        mock_db.insert.return_value = make_row()
        member = make_member(member_code="MEM-CUSTOM01")
        self.svc.create_member(member)
        assert member.member_code == "MEM-CUSTOM01"

    @patch("src.services.member_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.return_value = []
        mock_db.insert.side_effect = Exception("insert failed")
        result = self.svc.create_member(make_member())
        assert result.success is False
        assert "Could not create member" in result.error

    @patch("src.services.member_service.db_manager")
    def test_no_email_skips_duplicate_check(self, mock_db):
        mock_db.insert.return_value = make_row(email=None)
        result = self.svc.create_member(make_member(email=None))
        # select should NOT be called for duplicate email check when email is None
        mock_db.select.assert_not_called()
        assert result.success is True


# ---------------------------------------------------------------------------
# update_member
# ---------------------------------------------------------------------------

class TestUpdateMember:
    def setup_method(self):
        self.svc = MemberService()

    @patch("src.services.member_service.db_manager")
    def test_updates_member_successfully(self, mock_db):
        mock_db.select.side_effect = [
            [make_row()],   # existence check
            [],             # email uniqueness: no conflict
        ]
        mock_db.update.return_value = [make_row(first_name="Updated")]
        result = self.svc.update_member(make_member())
        assert result.success is True
        assert result.data.first_name == "Updated"

    def test_missing_id_returns_fail(self):
        result = self.svc.update_member(make_member(id=None))
        assert result.success is False
        assert "id is required" in result.error

    @patch("src.services.member_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        result = self.svc.update_member(make_member(first_name=""))
        mock_db.update.assert_not_called()
        assert result.success is False

    @patch("src.services.member_service.db_manager")
    def test_member_not_in_db_returns_fail(self, mock_db):
        mock_db.select.return_value = []   # existence check: not found
        result = self.svc.update_member(make_member())
        assert result.success is False
        assert "not found" in result.error

    @patch("src.services.member_service.db_manager")
    def test_email_conflict_with_another_member_returns_fail(self, mock_db):
        mock_db.select.side_effect = [
            [make_row()],                           # existence check OK
            [make_row(id="uuid-OTHER")],            # email used by different member
        ]
        result = self.svc.update_member(make_member())
        assert result.success is False
        assert "already in use" in result.error

    @patch("src.services.member_service.db_manager")
    def test_same_email_on_same_member_is_allowed(self, mock_db):
        """Updating a member with their own email should not trigger conflict."""
        mock_db.select.side_effect = [
            [make_row()],              # existence check
            [make_row(id="uuid-001")], # email check: same member id → no conflict
        ]
        mock_db.update.return_value = [make_row()]
        result = self.svc.update_member(make_member())
        assert result.success is True

    @patch("src.services.member_service.db_manager")
    def test_immutable_fields_are_stripped_from_update_payload(self, mock_db):
        mock_db.select.side_effect = [[make_row()], []]
        mock_db.update.return_value = [make_row()]
        self.svc.update_member(make_member())
        update_data = mock_db.update.call_args.kwargs["data"]
        assert "created_at" not in update_data
        assert "created_by" not in update_data
        assert "member_code" not in update_data

    @patch("src.services.member_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = [[make_row()], []]
        mock_db.update.side_effect = Exception("update failed")
        result = self.svc.update_member(make_member())
        assert result.success is False
        assert "Could not update member" in result.error
