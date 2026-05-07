"""
Tests for MembershipService.

All database interactions are isolated by patching the global `db_manager`
singleton that `membership_service` imports at module level.

Patch target: 'src.services.membership_service.db_manager'
"""
import pytest
from unittest.mock import patch
from datetime import date, timedelta

from src.services.membership_service import MembershipService
from src.models.models import MembershipPlan, MemberMembership
from src.models.enums import MembershipStatus


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_plan_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the membership_plans table schema."""
    defaults = dict(
        id="plan-001",
        name="Monthly Basic",
        description="Basic monthly plan",
        duration_days=30,
        price=50.0,
        has_class_access=True,
        max_classes_per_week=None,
        features=None,
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return defaults


def make_membership_row(**kwargs) -> dict:
    """Factory for a raw DB row matching member_memberships with join columns."""
    defaults = dict(
        id="ms-001",
        member_id="mem-001",
        membership_plan_id="plan-001",
        start_date="2026-04-01",
        end_date="2026-05-01",
        status="active",
        auto_renew=False,
        notes=None,
        created_at=None,
        updated_at=None,
        created_by=None,
        member_code="GYM001",
        first_name="John",
        last_name="Doe",
        plan_name="Monthly Basic",
        duration_days=30,
        price=50.0,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _validate_plan  (pure static)
# ---------------------------------------------------------------------------

class TestValidatePlan:
    def test_valid_plan_returns_none(self):
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=30)
        assert MembershipService._validate_plan(plan) is None

    def test_empty_name_returns_error(self):
        plan = MembershipPlan(name="", price=50.0, duration_days=30)
        result = MembershipService._validate_plan(plan)
        assert result is not None
        assert "name" in result.lower()

    def test_whitespace_only_name_returns_error(self):
        plan = MembershipPlan(name="   ", price=50.0, duration_days=30)
        result = MembershipService._validate_plan(plan)
        assert result is not None

    def test_negative_price_returns_error(self):
        plan = MembershipPlan(name="Basic", price=-1.0, duration_days=30)
        result = MembershipService._validate_plan(plan)
        assert result is not None
        assert "Price" in result

    def test_zero_price_is_accepted(self):
        plan = MembershipPlan(name="Free", price=0.0, duration_days=30)
        assert MembershipService._validate_plan(plan) is None

    def test_duration_less_than_one_returns_error(self):
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=0)
        result = MembershipService._validate_plan(plan)
        assert result is not None
        assert "Duration" in result

    def test_duration_of_one_is_accepted(self):
        plan = MembershipPlan(name="Day Pass", price=10.0, duration_days=1)
        assert MembershipService._validate_plan(plan) is None


# ---------------------------------------------------------------------------
# _plan_to_row  (pure static)
# ---------------------------------------------------------------------------

class TestPlanToRow:
    def test_all_fields_are_included(self):
        plan = MembershipPlan(
            name="  Basic  ",
            description="Desc",
            duration_days=30,
            price=50.0,
            has_class_access=True,
            max_classes_per_week=3,
            is_active=True,
        )
        row = MembershipService._plan_to_row(plan)
        assert row['name'] == "Basic"
        assert row['description'] == "Desc"
        assert row['duration_days'] == 30
        assert row['price'] == 50.0
        assert row['has_class_access'] is True
        assert row['max_classes_per_week'] == 3
        assert row['is_active'] is True

    def test_name_is_stripped(self):
        plan = MembershipPlan(name="  Trimmed  ", price=0.0, duration_days=1)
        assert MembershipService._plan_to_row(plan)['name'] == "Trimmed"

    def test_id_is_not_included(self):
        plan = MembershipPlan(id="plan-001", name="Basic", price=0.0, duration_days=1)
        assert 'id' not in MembershipService._plan_to_row(plan)


# ---------------------------------------------------------------------------
# _row_to_plan  (pure static)
# ---------------------------------------------------------------------------

class TestRowToPlan:
    def test_basic_fields_are_mapped(self):
        plan = MembershipService._row_to_plan(make_plan_row())
        assert plan.id == "plan-001"
        assert plan.name == "Monthly Basic"
        assert plan.duration_days == 30
        assert plan.is_active is True

    def test_price_is_converted_to_float(self):
        plan = MembershipService._row_to_plan(make_plan_row(price=100))
        assert isinstance(plan.price, float)
        assert plan.price == 100.0

    def test_is_active_defaults_to_true_when_missing(self):
        row = make_plan_row()
        row.pop('is_active')
        plan = MembershipService._row_to_plan(row)
        assert plan.is_active is True

    def test_max_classes_per_week_stays_none(self):
        plan = MembershipService._row_to_plan(make_plan_row(max_classes_per_week=None))
        assert plan.max_classes_per_week is None

    def test_max_classes_per_week_is_preserved(self):
        plan = MembershipService._row_to_plan(make_plan_row(max_classes_per_week=5))
        assert plan.max_classes_per_week == 5


# ---------------------------------------------------------------------------
# _row_to_membership  (pure static)
# ---------------------------------------------------------------------------

class TestRowToMembership:
    def test_basic_fields_are_mapped(self):
        ms = MembershipService._row_to_membership(make_membership_row())
        assert ms.id == "ms-001"
        assert ms.member_id == "mem-001"
        assert ms.membership_plan_id == "plan-001"
        assert ms.status == MembershipStatus.ACTIVE

    def test_populates_member_relation(self):
        ms = MembershipService._row_to_membership(make_membership_row())
        assert ms.member is not None
        assert ms.member.member_code == "GYM001"
        assert ms.member.full_name == "John Doe"

    def test_no_member_when_member_code_is_none(self):
        ms = MembershipService._row_to_membership(make_membership_row(member_code=None))
        assert ms.member is None

    def test_populates_plan_relation(self):
        ms = MembershipService._row_to_membership(make_membership_row())
        assert ms.plan is not None
        assert ms.plan.name == "Monthly Basic"
        assert ms.plan.duration_days == 30

    def test_no_plan_when_plan_name_is_none(self):
        ms = MembershipService._row_to_membership(make_membership_row(plan_name=None))
        assert ms.plan is None

    def test_start_date_parsed_from_string(self):
        ms = MembershipService._row_to_membership(make_membership_row())
        assert isinstance(ms.start_date, date)
        assert ms.start_date == date(2026, 4, 1)

    def test_end_date_parsed_from_string(self):
        ms = MembershipService._row_to_membership(make_membership_row())
        assert isinstance(ms.end_date, date)
        assert ms.end_date == date(2026, 5, 1)

    def test_end_date_is_none_when_missing(self):
        ms = MembershipService._row_to_membership(make_membership_row(end_date=None))
        assert ms.end_date is None

    def test_status_converted_to_enum(self):
        ms = MembershipService._row_to_membership(make_membership_row(status="suspended"))
        assert ms.status == MembershipStatus.SUSPENDED

    def test_date_instance_accepted_directly(self):
        d = date(2026, 6, 15)
        ms = MembershipService._row_to_membership(make_membership_row(start_date=d))
        assert ms.start_date == d

    def test_member_id_assigned_to_member_object(self):
        ms = MembershipService._row_to_membership(make_membership_row())
        assert ms.member.id == "mem-001"


# ---------------------------------------------------------------------------
# _validate_status_transition  (pure static)
# ---------------------------------------------------------------------------

class TestValidateStatusTransition:
    def test_active_to_suspended_is_allowed(self):
        assert MembershipService._validate_status_transition(
            MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED
        )

    def test_active_to_cancelled_is_allowed(self):
        assert MembershipService._validate_status_transition(
            MembershipStatus.ACTIVE, MembershipStatus.CANCELLED
        )

    def test_active_to_expired_is_not_allowed(self):
        assert not MembershipService._validate_status_transition(
            MembershipStatus.ACTIVE, MembershipStatus.EXPIRED
        )

    def test_suspended_to_active_is_allowed(self):
        assert MembershipService._validate_status_transition(
            MembershipStatus.SUSPENDED, MembershipStatus.ACTIVE
        )

    def test_suspended_to_cancelled_is_allowed(self):
        assert MembershipService._validate_status_transition(
            MembershipStatus.SUSPENDED, MembershipStatus.CANCELLED
        )

    def test_suspended_to_expired_is_not_allowed(self):
        assert not MembershipService._validate_status_transition(
            MembershipStatus.SUSPENDED, MembershipStatus.EXPIRED
        )

    def test_expired_to_active_is_allowed(self):
        assert MembershipService._validate_status_transition(
            MembershipStatus.EXPIRED, MembershipStatus.ACTIVE
        )

    def test_expired_to_cancelled_is_not_allowed(self):
        assert not MembershipService._validate_status_transition(
            MembershipStatus.EXPIRED, MembershipStatus.CANCELLED
        )

    def test_cancelled_to_active_is_not_allowed(self):
        assert not MembershipService._validate_status_transition(
            MembershipStatus.CANCELLED, MembershipStatus.ACTIVE
        )

    def test_cancelled_to_suspended_is_not_allowed(self):
        assert not MembershipService._validate_status_transition(
            MembershipStatus.CANCELLED, MembershipStatus.SUSPENDED
        )


# ---------------------------------------------------------------------------
# get_all_plans
# ---------------------------------------------------------------------------

class TestGetAllPlans:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_returns_active_plans_by_default(self, mock_db):
        mock_db.select.return_value = [make_plan_row()]
        result = self.svc.get_all_plans()
        assert result.success is True
        assert len(result.data) == 1
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'is_active': True}

    @patch("src.services.membership_service.db_manager")
    def test_include_inactive_passes_no_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_plans(include_inactive=True)
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] is None

    @patch("src.services.membership_service.db_manager")
    def test_returns_list_of_plan_objects(self, mock_db):
        mock_db.select.return_value = [make_plan_row(), make_plan_row(id="plan-002", name="Annual")]
        result = self.svc.get_all_plans()
        assert result.success is True
        assert len(result.data) == 2
        assert all(isinstance(p, MembershipPlan) for p in result.data)

    @patch("src.services.membership_service.db_manager")
    def test_returns_empty_list_when_no_plans(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_all_plans()
        assert result.success is True
        assert result.data == []

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_all_plans()
        assert result.success is False
        assert result.error is not None

    @patch("src.services.membership_service.db_manager")
    def test_orders_by_name(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_plans()
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['order_by'] == 'name'


# ---------------------------------------------------------------------------
# get_plan_by_id
# ---------------------------------------------------------------------------

class TestGetPlanById:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_returns_plan_when_found(self, mock_db):
        mock_db.select.return_value = [make_plan_row()]
        result = self.svc.get_plan_by_id("plan-001")
        assert result.success is True
        assert result.data.id == "plan-001"
        assert result.data.name == "Monthly Basic"

    @patch("src.services.membership_service.db_manager")
    def test_returns_not_found_when_empty(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_plan_by_id("plan-999")
        assert result.success is False
        assert result.is_not_found is True

    @patch("src.services.membership_service.db_manager")
    def test_queries_by_correct_id(self, mock_db):
        mock_db.select.return_value = [make_plan_row()]
        self.svc.get_plan_by_id("plan-001")
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'id': 'plan-001'}

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_plan_by_id("plan-001")
        assert result.success is False
        assert result.is_not_found is False


# ---------------------------------------------------------------------------
# create_plan
# ---------------------------------------------------------------------------

class TestCreatePlan:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_creates_plan_successfully(self, mock_db):
        mock_db.insert.return_value = make_plan_row()
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=30)
        result = self.svc.create_plan(plan)
        assert result.success is True
        assert result.data.id == "plan-001"

    @patch("src.services.membership_service.db_manager")
    def test_empty_name_blocks_db_call(self, mock_db):
        plan = MembershipPlan(name="", price=50.0, duration_days=30)
        result = self.svc.create_plan(plan)
        assert result.success is False
        mock_db.insert.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_negative_price_blocks_db_call(self, mock_db):
        plan = MembershipPlan(name="Basic", price=-10.0, duration_days=30)
        result = self.svc.create_plan(plan)
        assert result.success is False
        mock_db.insert.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_zero_duration_blocks_db_call(self, mock_db):
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=0)
        result = self.svc.create_plan(plan)
        assert result.success is False
        mock_db.insert.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_calls_insert_with_correct_table(self, mock_db):
        mock_db.insert.return_value = make_plan_row()
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=30)
        self.svc.create_plan(plan)
        assert mock_db.insert.call_args.args[0] == "membership_plans"

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.insert.side_effect = Exception("insert error")
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=30)
        result = self.svc.create_plan(plan)
        assert result.success is False


# ---------------------------------------------------------------------------
# update_plan
# ---------------------------------------------------------------------------

class TestUpdatePlan:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_updates_plan_successfully(self, mock_db):
        mock_db.select.return_value = [make_plan_row()]
        mock_db.update.return_value = [make_plan_row(name="Updated")]
        plan = MembershipPlan(id="plan-001", name="Updated", price=60.0, duration_days=30)
        result = self.svc.update_plan(plan)
        assert result.success is True
        assert result.data.name == "Updated"

    @patch("src.services.membership_service.db_manager")
    def test_missing_id_returns_failure(self, mock_db):
        plan = MembershipPlan(name="Basic", price=50.0, duration_days=30)
        result = self.svc.update_plan(plan)
        assert result.success is False
        assert "ID" in result.error
        mock_db.update.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_validation_error_blocks_update(self, mock_db):
        plan = MembershipPlan(id="plan-001", name="", price=50.0, duration_days=30)
        result = self.svc.update_plan(plan)
        assert result.success is False
        mock_db.update.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_plan_not_found_returns_failure(self, mock_db):
        mock_db.select.return_value = []
        plan = MembershipPlan(id="plan-999", name="Basic", price=50.0, duration_days=30)
        result = self.svc.update_plan(plan)
        assert result.success is False
        assert "not found" in result.error.lower()
        mock_db.update.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_updated_at_is_included_in_payload(self, mock_db):
        mock_db.select.return_value = [make_plan_row()]
        mock_db.update.return_value = [make_plan_row()]
        plan = MembershipPlan(id="plan-001", name="Basic", price=50.0, duration_days=30)
        self.svc.update_plan(plan)
        payload = mock_db.update.call_args.args[1]
        assert 'updated_at' in payload

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.return_value = [make_plan_row()]
        mock_db.update.side_effect = Exception("update error")
        plan = MembershipPlan(id="plan-001", name="Basic", price=50.0, duration_days=30)
        result = self.svc.update_plan(plan)
        assert result.success is False


# ---------------------------------------------------------------------------
# toggle_plan_status
# ---------------------------------------------------------------------------

class TestTogglePlanStatus:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_activates_plan(self, mock_db):
        mock_db.update.return_value = [make_plan_row(is_active=True)]
        result = self.svc.toggle_plan_status("plan-001", is_active=True)
        assert result.success is True
        payload = mock_db.update.call_args.args[1]
        assert payload == {'is_active': True}

    @patch("src.services.membership_service.db_manager")
    def test_deactivates_plan(self, mock_db):
        mock_db.update.return_value = [make_plan_row(is_active=False)]
        result = self.svc.toggle_plan_status("plan-001", is_active=False)
        assert result.success is True
        payload = mock_db.update.call_args.args[1]
        assert payload == {'is_active': False}

    @patch("src.services.membership_service.db_manager")
    def test_calls_correct_table(self, mock_db):
        mock_db.update.return_value = []
        self.svc.toggle_plan_status("plan-001", is_active=True)
        assert mock_db.update.call_args.args[0] == "membership_plans"

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.update.side_effect = Exception("db error")
        result = self.svc.toggle_plan_status("plan-001", is_active=True)
        assert result.success is False


# ---------------------------------------------------------------------------
# get_memberships
# ---------------------------------------------------------------------------

class TestGetMemberships:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_no_filters_calls_select(self, mock_db):
        mock_db.select.return_value = [make_membership_row()]
        result = self.svc.get_memberships()
        assert result.success is True
        mock_db.select.assert_called_once()
        mock_db.select_range.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_filters_by_status(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_memberships(status=MembershipStatus.ACTIVE)
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'status': 'active'}

    @patch("src.services.membership_service.db_manager")
    def test_no_status_passes_no_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_memberships()
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] is None

    @patch("src.services.membership_service.db_manager")
    def test_date_range_uses_select_range_on_start_date(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_memberships(date_from=date(2026, 4, 1), date_to=date(2026, 4, 30))
        mock_db.select_range.assert_called_once()
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs['column'] == 'start_date'
        assert call_kwargs['start'] == '2026-04-01'
        assert call_kwargs['end'] == '2026-04-30'

    @patch("src.services.membership_service.db_manager")
    def test_date_range_with_status_passes_status_as_extra_filter(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_memberships(
            status=MembershipStatus.ACTIVE,
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
        )
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs['filters'] == {'status': 'active'}

    @patch("src.services.membership_service.db_manager")
    def test_expiring_days_uses_select_range_on_end_date(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_memberships(expiring_days=7)
        mock_db.select_range.assert_called_once()
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs['column'] == 'end_date'
        assert call_kwargs['start'] == date.today().isoformat()
        assert call_kwargs['end'] == (date.today() + timedelta(days=7)).isoformat()

    @patch("src.services.membership_service.db_manager")
    def test_expiring_days_always_filters_active_status(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_memberships(expiring_days=7)
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs['filters'] == {'status': 'active'}

    @patch("src.services.membership_service.db_manager")
    def test_expiring_days_takes_priority_over_date_range(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_memberships(
            expiring_days=7,
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
        )
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs['column'] == 'end_date'

    @patch("src.services.membership_service.db_manager")
    def test_search_term_filters_by_member_name_in_python(self, mock_db):
        mock_db.select.return_value = [
            make_membership_row(id="ms-001", first_name="John", last_name="Doe"),
            make_membership_row(id="ms-002", member_id="mem-002", member_code="GYM002", first_name="Jane", last_name="Smith"),
        ]
        result = self.svc.get_memberships(search_term="Jane")
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].id == "ms-002"

    @patch("src.services.membership_service.db_manager")
    def test_search_term_filters_by_member_code_in_python(self, mock_db):
        mock_db.select.return_value = [make_membership_row()]
        result = self.svc.get_memberships(search_term="GYM001")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.membership_service.db_manager")
    def test_returns_empty_list_when_no_records(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_memberships()
        assert result.success is True
        assert result.data == []

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_memberships()
        assert result.success is False


# ---------------------------------------------------------------------------
# get_memberships_by_member
# ---------------------------------------------------------------------------

class TestGetMembershipsByMember:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_returns_memberships_for_member(self, mock_db):
        mock_db.select.return_value = [make_membership_row()]
        result = self.svc.get_memberships_by_member("mem-001")
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].member_id == "mem-001"

    @patch("src.services.membership_service.db_manager")
    def test_filters_by_member_id(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_memberships_by_member("mem-001")
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'member_id': 'mem-001'}

    @patch("src.services.membership_service.db_manager")
    def test_orders_by_start_date(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_memberships_by_member("mem-001")
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['order_by'] == 'start_date'

    @patch("src.services.membership_service.db_manager")
    def test_returns_empty_list_when_no_memberships(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_memberships_by_member("mem-999")
        assert result.success is True
        assert result.data == []

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_memberships_by_member("mem-001")
        assert result.success is False


# ---------------------------------------------------------------------------
# assign_membership
# ---------------------------------------------------------------------------

class TestAssignMembership:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_assigns_membership_successfully(self, mock_db):
        mock_db.select.side_effect = [
            [],                   # no active membership found
            [make_plan_row()],    # get_plan_by_id
        ]
        mock_db.insert.return_value = make_membership_row()
        result = self.svc.assign_membership("mem-001", "plan-001", date(2026, 4, 1))
        assert result.success is True
        assert result.data.id == "ms-001"

    @patch("src.services.membership_service.db_manager")
    def test_end_date_calculated_from_plan_duration(self, mock_db):
        mock_db.select.side_effect = [[], [make_plan_row(duration_days=30)]]
        mock_db.insert.return_value = make_membership_row()
        start = date(2026, 4, 1)
        self.svc.assign_membership("mem-001", "plan-001", start)
        payload = mock_db.insert.call_args.args[1]
        assert payload['end_date'] == date(2026, 5, 1).isoformat()

    @patch("src.services.membership_service.db_manager")
    def test_fails_if_active_membership_exists(self, mock_db):
        mock_db.select.return_value = [make_membership_row()]
        result = self.svc.assign_membership("mem-001", "plan-001", date(2026, 4, 1))
        assert result.success is False
        assert "active" in result.error.lower()
        mock_db.insert.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_fails_if_plan_not_found(self, mock_db):
        mock_db.select.side_effect = [[], []]  # no active ms; plan not found
        result = self.svc.assign_membership("mem-001", "plan-999", date(2026, 4, 1))
        assert result.success is False
        assert "plan" in result.error.lower()
        mock_db.insert.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_payload_contains_required_fields(self, mock_db):
        mock_db.select.side_effect = [[], [make_plan_row()]]
        mock_db.insert.return_value = make_membership_row()
        self.svc.assign_membership("mem-001", "plan-001", date(2026, 4, 1), notes="Test", created_by="user-001")
        payload = mock_db.insert.call_args.args[1]
        assert payload['member_id'] == "mem-001"
        assert payload['membership_plan_id'] == "plan-001"
        assert payload['start_date'] == "2026-04-01"
        assert payload['status'] == "active"
        assert payload['notes'] == "Test"
        assert payload['created_by'] == "user-001"

    @patch("src.services.membership_service.db_manager")
    def test_calls_insert_with_correct_table(self, mock_db):
        mock_db.select.side_effect = [[], [make_plan_row()]]
        mock_db.insert.return_value = make_membership_row()
        self.svc.assign_membership("mem-001", "plan-001", date(2026, 4, 1))
        assert mock_db.insert.call_args.args[0] == "member_memberships"

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = [[], [make_plan_row()]]
        mock_db.insert.side_effect = Exception("insert error")
        result = self.svc.assign_membership("mem-001", "plan-001", date(2026, 4, 1))
        assert result.success is False


# ---------------------------------------------------------------------------
# change_status
# ---------------------------------------------------------------------------

class TestChangeStatus:
    def setup_method(self):
        self.svc = MembershipService()

    @patch("src.services.membership_service.db_manager")
    def test_active_to_suspended_succeeds(self, mock_db):
        mock_db.select.return_value = [make_membership_row(status="active")]
        result = self.svc.change_status("ms-001", MembershipStatus.SUSPENDED)
        assert result.success is True
        payload = mock_db.update.call_args.args[1]
        assert payload == {'status': 'suspended'}

    @patch("src.services.membership_service.db_manager")
    def test_suspended_to_active_succeeds(self, mock_db):
        mock_db.select.return_value = [make_membership_row(status="suspended")]
        result = self.svc.change_status("ms-001", MembershipStatus.ACTIVE)
        assert result.success is True

    @patch("src.services.membership_service.db_manager")
    def test_expired_to_active_succeeds(self, mock_db):
        mock_db.select.return_value = [make_membership_row(status="expired")]
        result = self.svc.change_status("ms-001", MembershipStatus.ACTIVE)
        assert result.success is True

    @patch("src.services.membership_service.db_manager")
    def test_invalid_transition_returns_failure(self, mock_db):
        mock_db.select.return_value = [make_membership_row(status="active")]
        result = self.svc.change_status("ms-001", MembershipStatus.EXPIRED)
        assert result.success is False
        assert "Cannot transition" in result.error
        mock_db.update.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_cancelled_to_any_returns_failure(self, mock_db):
        mock_db.select.return_value = [make_membership_row(status="cancelled")]
        result = self.svc.change_status("ms-001", MembershipStatus.ACTIVE)
        assert result.success is False
        mock_db.update.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_membership_not_found_returns_not_found(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.change_status("ms-999", MembershipStatus.SUSPENDED)
        assert result.success is False
        assert result.is_not_found is True
        mock_db.update.assert_not_called()

    @patch("src.services.membership_service.db_manager")
    def test_filters_update_by_membership_id(self, mock_db):
        mock_db.select.return_value = [make_membership_row(status="active")]
        self.svc.change_status("ms-001", MembershipStatus.SUSPENDED)
        update_filters = mock_db.update.call_args.kwargs['filters']
        assert update_filters == {'id': 'ms-001'}

    @patch("src.services.membership_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.change_status("ms-001", MembershipStatus.SUSPENDED)
        assert result.success is False
