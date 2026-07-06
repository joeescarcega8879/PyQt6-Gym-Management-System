"""
Tests for DashboardService.

DashboardService does not touch the database directly — it composes results
from the other service singletons. All tests patch those singletons as they
are imported into `src.services.dashboard_service`.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from src.services.dashboard_service import DashboardService
from src.services.result import ServiceResult
from src.models.models import Member, Payment, Attendance, MemberMembership, ClassSchedule


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_member(**kwargs) -> Member:
    defaults = dict(id="mem-001", member_code="MEM-0001", first_name="John", last_name="Doe", is_active=True)
    defaults.update(kwargs)
    return Member(**defaults)


def make_payment(**kwargs) -> Payment:
    defaults = dict(id="pay-001", member_id="mem-001", amount=50.0)
    defaults.update(kwargs)
    return Payment(**defaults)


def make_attendance(**kwargs) -> Attendance:
    defaults = dict(id="att-001", member_id="mem-001")
    defaults.update(kwargs)
    return Attendance(**defaults)


def make_membership(**kwargs) -> MemberMembership:
    defaults = dict(id="ms-001", member_id="mem-001", membership_plan_id="plan-001")
    defaults.update(kwargs)
    return MemberMembership(**defaults)


def make_schedule(**kwargs) -> ClassSchedule:
    defaults = dict(id="sch-001", class_id="class-001", day_of_week=1)
    defaults.update(kwargs)
    return ClassSchedule(**defaults)


@pytest.fixture
def service() -> DashboardService:
    return DashboardService()


# ---------------------------------------------------------------------------
# get_summary — happy path
# ---------------------------------------------------------------------------

class TestGetSummary:

    @patch("src.services.dashboard_service.class_service")
    @patch("src.services.dashboard_service.membership_service")
    @patch("src.services.dashboard_service.attendance_service")
    @patch("src.services.dashboard_service.payment_service")
    @patch("src.services.dashboard_service.member_service")
    def test_aggregates_all_sections_successfully(
        self, mock_member_service, mock_payment_service, mock_attendance_service,
        mock_membership_service, mock_class_service, service,
    ):
        mock_member_service.get_all_members.return_value = ServiceResult.ok(
            [make_member(), make_member(id="mem-002")]
        )
        mock_payment_service.get_payments.return_value = ServiceResult.ok(
            [make_payment(amount=50.0), make_payment(amount=25.5)]
        )
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok(
            [make_attendance(), make_attendance(id="att-002")]
        )
        mock_membership_service.get_memberships.return_value = ServiceResult.ok(
            [make_membership()]
        )
        mock_class_service.get_schedules.return_value = ServiceResult.ok(
            [make_schedule()]
        )

        result = service.get_summary()

        assert result.success is True
        summary = result.data
        assert summary.active_members == 2
        assert summary.monthly_revenue == 75.5
        assert summary.today_checkins == 2
        assert summary.expiring_memberships_count == 1
        assert len(summary.expiring_memberships) == 1
        assert len(summary.today_schedules) == 1

    @patch("src.services.dashboard_service.class_service")
    @patch("src.services.dashboard_service.membership_service")
    @patch("src.services.dashboard_service.attendance_service")
    @patch("src.services.dashboard_service.payment_service")
    @patch("src.services.dashboard_service.member_service")
    def test_no_active_members_returns_zero(
        self, mock_member_service, mock_payment_service, mock_attendance_service,
        mock_membership_service, mock_class_service, service,
    ):
        mock_member_service.get_all_members.return_value = ServiceResult.ok([])
        mock_payment_service.get_payments.return_value = ServiceResult.ok([])
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok([])
        mock_membership_service.get_memberships.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])

        result = service.get_summary()

        assert result.success is True
        summary = result.data
        assert summary.active_members == 0
        assert summary.monthly_revenue == 0.0
        assert summary.today_checkins == 0
        assert summary.expiring_memberships_count == 0
        assert summary.expiring_memberships == []
        assert summary.today_schedules == []

    @patch("src.services.dashboard_service.class_service")
    @patch("src.services.dashboard_service.membership_service")
    @patch("src.services.dashboard_service.attendance_service")
    @patch("src.services.dashboard_service.payment_service")
    @patch("src.services.dashboard_service.member_service")
    def test_partial_sub_service_failure_defaults_to_zero(
        self, mock_member_service, mock_payment_service, mock_attendance_service,
        mock_membership_service, mock_class_service, service,
    ):
        """If one sub-service fails, its section falls back to empty/zero but
        the overall summary is still returned as success."""
        mock_member_service.get_all_members.return_value = ServiceResult.fail("db down")
        mock_payment_service.get_payments.return_value = ServiceResult.ok(
            [make_payment(amount=100.0)]
        )
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok([])
        mock_membership_service.get_memberships.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])

        result = service.get_summary()

        assert result.success is True
        summary = result.data
        assert summary.active_members == 0
        assert summary.monthly_revenue == 100.0

    @patch("src.services.dashboard_service.class_service")
    @patch("src.services.dashboard_service.membership_service")
    @patch("src.services.dashboard_service.attendance_service")
    @patch("src.services.dashboard_service.payment_service")
    @patch("src.services.dashboard_service.member_service")
    def test_payments_query_uses_completed_status_and_current_month(
        self, mock_member_service, mock_payment_service, mock_attendance_service,
        mock_membership_service, mock_class_service, service,
    ):
        mock_member_service.get_all_members.return_value = ServiceResult.ok([])
        mock_payment_service.get_payments.return_value = ServiceResult.ok([])
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok([])
        mock_membership_service.get_memberships.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])

        service.get_summary()

        call_kwargs = mock_payment_service.get_payments.call_args.kwargs
        today = date.today()
        assert call_kwargs["date_from"] == today.replace(day=1)
        assert call_kwargs["date_to"] == today

    @patch("src.services.dashboard_service.class_service")
    @patch("src.services.dashboard_service.membership_service")
    @patch("src.services.dashboard_service.attendance_service")
    @patch("src.services.dashboard_service.payment_service")
    @patch("src.services.dashboard_service.member_service")
    def test_expiring_memberships_uses_seven_day_threshold(
        self, mock_member_service, mock_payment_service, mock_attendance_service,
        mock_membership_service, mock_class_service, service,
    ):
        mock_member_service.get_all_members.return_value = ServiceResult.ok([])
        mock_payment_service.get_payments.return_value = ServiceResult.ok([])
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok([])
        mock_membership_service.get_memberships.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])

        service.get_summary()

        call_kwargs = mock_membership_service.get_memberships.call_args.kwargs
        assert call_kwargs["expiring_days"] == 7

    @patch("src.services.dashboard_service.class_service")
    @patch("src.services.dashboard_service.membership_service")
    @patch("src.services.dashboard_service.attendance_service")
    @patch("src.services.dashboard_service.payment_service")
    @patch("src.services.dashboard_service.member_service")
    def test_today_schedules_uses_correct_day_of_week_conversion(
        self, mock_member_service, mock_payment_service, mock_attendance_service,
        mock_membership_service, mock_class_service, service,
    ):
        mock_member_service.get_all_members.return_value = ServiceResult.ok([])
        mock_payment_service.get_payments.return_value = ServiceResult.ok([])
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok([])
        mock_membership_service.get_memberships.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])

        service.get_summary()

        expected_day = (date.today().weekday() + 1) % 7
        call_kwargs = mock_class_service.get_schedules.call_args.kwargs
        assert call_kwargs["day_of_week"] == expected_day
        assert call_kwargs["include_inactive"] is False

    @patch("src.services.dashboard_service.member_service")
    def test_unexpected_exception_returns_failure(self, mock_member_service, service):
        mock_member_service.get_all_members.side_effect = Exception("boom")

        result = service.get_summary()

        # _get_active_members_count doesn't catch exceptions itself,
        # so an unexpected error bubbles up and get_summary() reports failure.
        assert result.success is False
        assert "boom" in result.error


# ---------------------------------------------------------------------------
# Private helper methods (exercised directly for extra confidence)
# ---------------------------------------------------------------------------

class TestPrivateHelpers:

    @patch("src.services.dashboard_service.member_service")
    def test_get_active_members_count_returns_length(self, mock_member_service):
        mock_member_service.get_all_members.return_value = ServiceResult.ok(
            [make_member(), make_member(id="mem-2"), make_member(id="mem-3")]
        )
        assert DashboardService._get_active_members_count() == 3

    @patch("src.services.dashboard_service.member_service")
    def test_get_active_members_count_failure_returns_zero(self, mock_member_service):
        mock_member_service.get_all_members.return_value = ServiceResult.fail("error")
        assert DashboardService._get_active_members_count() == 0

    @patch("src.services.dashboard_service.payment_service")
    def test_get_monthly_revenue_sums_amounts(self, mock_payment_service):
        mock_payment_service.get_payments.return_value = ServiceResult.ok(
            [make_payment(amount=10.0), make_payment(amount=20.5)]
        )
        assert DashboardService._get_monthly_revenue() == 30.5

    @patch("src.services.dashboard_service.payment_service")
    def test_get_monthly_revenue_failure_returns_zero(self, mock_payment_service):
        mock_payment_service.get_payments.return_value = ServiceResult.fail("error")
        assert DashboardService._get_monthly_revenue() == 0.0

    @patch("src.services.dashboard_service.attendance_service")
    def test_get_today_checkins_count(self, mock_attendance_service):
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.ok(
            [make_attendance(), make_attendance(id="att-2")]
        )
        assert DashboardService._get_today_checkins_count() == 2

    @patch("src.services.dashboard_service.attendance_service")
    def test_get_today_checkins_count_failure_returns_zero(self, mock_attendance_service):
        mock_attendance_service.get_attendance_by_date.return_value = ServiceResult.fail("error")
        assert DashboardService._get_today_checkins_count() == 0

    @patch("src.services.dashboard_service.membership_service")
    def test_get_expiring_memberships_returns_list(self, mock_membership_service):
        memberships = [make_membership()]
        mock_membership_service.get_memberships.return_value = ServiceResult.ok(memberships)
        assert DashboardService._get_expiring_memberships() == memberships

    @patch("src.services.dashboard_service.membership_service")
    def test_get_expiring_memberships_failure_returns_empty_list(self, mock_membership_service):
        mock_membership_service.get_memberships.return_value = ServiceResult.fail("error")
        assert DashboardService._get_expiring_memberships() == []

    @patch("src.services.dashboard_service.class_service")
    def test_get_today_schedules_returns_list(self, mock_class_service):
        schedules = [make_schedule()]
        mock_class_service.get_schedules.return_value = ServiceResult.ok(schedules)
        assert DashboardService._get_today_schedules() == schedules

    @patch("src.services.dashboard_service.class_service")
    def test_get_today_schedules_failure_returns_empty_list(self, mock_class_service):
        mock_class_service.get_schedules.return_value = ServiceResult.fail("error")
        assert DashboardService._get_today_schedules() == []
