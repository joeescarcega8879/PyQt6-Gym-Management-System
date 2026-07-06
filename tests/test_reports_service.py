"""
Tests for ReportsService.

Like DashboardService, ReportsService does not touch the database directly —
it composes results from the other service singletons. All tests patch those
singletons as they are imported into `src.services.reports_service`.
"""
import pytest
from unittest.mock import patch
from datetime import date, datetime, timedelta, timezone

from src.services.reports_service import ReportsService
from src.services.result import ServiceResult
from src.models.models import (
    Member, Payment, Attendance, MemberMembership, MembershipPlan,
    ClassSchedule, Class, Equipment, EquipmentMaintenance, Instructor,
)
from src.models.enums import PaymentMethod, PaymentStatus, MembershipStatus, EquipmentCondition, MaintenanceType


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_member(**kwargs) -> Member:
    defaults = dict(id="mem-001", member_code="MEM-0001", first_name="John", last_name="Doe", is_active=True)
    defaults.update(kwargs)
    return Member(**defaults)


def make_payment(**kwargs) -> Payment:
    defaults = dict(
        id="pay-001", member_id="mem-001", amount=50.0,
        payment_method=PaymentMethod.CASH, status=PaymentStatus.COMPLETED,
        payment_date=datetime(2026, 3, 15, 10, 0),
    )
    defaults.update(kwargs)
    return Payment(**defaults)


def make_attendance(**kwargs) -> Attendance:
    defaults = dict(
        id="att-001", member_id="mem-001",
        check_in_time=datetime(2026, 3, 15, 9, 0, tzinfo=timezone.utc),
        member=make_member(),
    )
    defaults.update(kwargs)
    return Attendance(**defaults)


def make_plan(**kwargs) -> MembershipPlan:
    defaults = dict(id="plan-001", name="Gold", duration_days=30, price=50.0)
    defaults.update(kwargs)
    return MembershipPlan(**defaults)


def make_membership(**kwargs) -> MemberMembership:
    defaults = dict(id="ms-001", member_id="mem-001", membership_plan_id="plan-001", status=MembershipStatus.ACTIVE, plan=make_plan())
    defaults.update(kwargs)
    return MemberMembership(**defaults)


def make_class(**kwargs) -> Class:
    defaults = dict(id="class-001", name="Yoga", max_capacity=10)
    defaults.update(kwargs)
    return Class(**defaults)


def make_schedule(**kwargs) -> ClassSchedule:
    defaults = dict(id="sch-001", class_id="class-001", day_of_week=1, instructor_id="inst-001", class_info=make_class())
    defaults.update(kwargs)
    return ClassSchedule(**defaults)


def make_equipment(**kwargs) -> Equipment:
    defaults = dict(id="eq-001", name="Treadmill", condition=EquipmentCondition.GOOD)
    defaults.update(kwargs)
    return Equipment(**defaults)


def make_maintenance(**kwargs) -> EquipmentMaintenance:
    defaults = dict(
        id="maint-001", equipment_id="eq-001",
        maintenance_date=date(2026, 3, 1), maintenance_type=MaintenanceType.PREVENTIVE,
        next_maintenance_date=date(2026, 3, 20),
    )
    defaults.update(kwargs)
    return EquipmentMaintenance(**defaults)


def make_instructor(**kwargs) -> Instructor:
    defaults = dict(id="inst-001", first_name="Jane", last_name="Smith")
    defaults.update(kwargs)
    return Instructor(**defaults)


@pytest.fixture
def service() -> ReportsService:
    return ReportsService()


# ---------------------------------------------------------------------------
# get_financial_report
# ---------------------------------------------------------------------------

class TestGetFinancialReport:

    @patch("src.services.reports_service.payment_service")
    def test_aggregates_revenue_and_method_breakdown(self, mock_payment_service, service):
        current_payments = [
            make_payment(amount=50.0, payment_method=PaymentMethod.CASH),
            make_payment(amount=25.0, payment_method=PaymentMethod.CARD),
        ]
        mock_payment_service.get_payments.side_effect = [
            ServiceResult.ok(current_payments),  # detail list (filtered)
            ServiceResult.ok(current_payments),  # completed-only, current period
            ServiceResult.ok([]),                # completed-only, previous period
        ]

        result = service.get_financial_report(date(2026, 3, 1), date(2026, 3, 31))

        assert result.success is True
        report = result.data
        assert report.total_revenue == 75.0
        assert report.transaction_count == 2
        assert report.revenue_by_method == {"cash": 50.0, "card": 25.0}
        assert report.previous_period_revenue == 0.0
        assert report.revenue_change_pct is None

    @patch("src.services.reports_service.payment_service")
    def test_computes_revenue_change_pct_against_previous_period(self, mock_payment_service, service):
        mock_payment_service.get_payments.side_effect = [
            ServiceResult.ok([make_payment(amount=150.0)]),
            ServiceResult.ok([make_payment(amount=150.0)]),
            ServiceResult.ok([make_payment(amount=100.0)]),
        ]

        result = service.get_financial_report(date(2026, 3, 1), date(2026, 3, 31))

        assert result.data.revenue_change_pct == 50.0

    @patch("src.services.reports_service.payment_service")
    def test_previous_period_has_same_length_as_current(self, mock_payment_service, service):
        mock_payment_service.get_payments.return_value = ServiceResult.ok([])

        service.get_financial_report(date(2026, 3, 10), date(2026, 3, 19))

        # 3 calls: detail, completed-current, completed-previous
        assert mock_payment_service.get_payments.call_count == 3
        previous_call_kwargs = mock_payment_service.get_payments.call_args_list[2].kwargs
        assert previous_call_kwargs["date_from"] == date(2026, 2, 28)
        assert previous_call_kwargs["date_to"] == date(2026, 3, 9)
        assert previous_call_kwargs["status"] == PaymentStatus.COMPLETED

    @patch("src.services.reports_service.payment_service")
    def test_sub_service_failure_defaults_to_empty(self, mock_payment_service, service):
        mock_payment_service.get_payments.return_value = ServiceResult.fail("db down")

        result = service.get_financial_report(date(2026, 3, 1), date(2026, 3, 31))

        assert result.success is True
        assert result.data.total_revenue == 0.0
        assert result.data.transaction_count == 0
        assert result.data.payments == []

    @patch("src.services.reports_service.payment_service")
    def test_detail_list_respects_status_filter_independent_of_revenue(self, mock_payment_service, service):
        pending_payments = [make_payment(status=PaymentStatus.PENDING, amount=30.0)]
        mock_payment_service.get_payments.side_effect = [
            ServiceResult.ok(pending_payments),  # detail respects status=PENDING
            ServiceResult.ok([]),                # completed-only current: none
            ServiceResult.ok([]),                # completed-only previous: none
        ]

        result = service.get_financial_report(
            date(2026, 3, 1), date(2026, 3, 31), status=PaymentStatus.PENDING,
        )

        assert result.data.payments == pending_payments
        assert result.data.total_revenue == 0.0

    @patch("src.services.reports_service.payment_service")
    def test_unexpected_exception_returns_failure(self, mock_payment_service, service):
        mock_payment_service.get_payments.side_effect = Exception("boom")

        result = service.get_financial_report(date(2026, 3, 1), date(2026, 3, 31))

        assert result.success is False
        assert "boom" in result.error


# ---------------------------------------------------------------------------
# get_membership_report
# ---------------------------------------------------------------------------

class TestGetMembershipReport:

    @patch("src.services.reports_service.membership_service")
    def test_aggregates_counts_by_status_and_plan(self, mock_membership_service, service):
        memberships = [
            make_membership(status=MembershipStatus.ACTIVE, plan=make_plan(name="Gold")),
            make_membership(id="ms-002", status=MembershipStatus.ACTIVE, plan=make_plan(name="Gold")),
            make_membership(id="ms-003", status=MembershipStatus.EXPIRED, plan=make_plan(name="Silver")),
        ]
        mock_membership_service.get_memberships.side_effect = [
            ServiceResult.ok(memberships),
            ServiceResult.ok([]),
        ]

        result = service.get_membership_report()

        assert result.success is True
        report = result.data
        assert report.counts_by_status == {"active": 2, "expired": 1}
        assert report.counts_by_plan == {"Gold": 2, "Silver": 1}

    @patch("src.services.reports_service.membership_service")
    def test_retention_rate_is_active_over_active_plus_expired(self, mock_membership_service, service):
        memberships = [
            make_membership(status=MembershipStatus.ACTIVE),
            make_membership(id="ms-002", status=MembershipStatus.ACTIVE),
            make_membership(id="ms-003", status=MembershipStatus.ACTIVE),
            make_membership(id="ms-004", status=MembershipStatus.EXPIRED),
        ]
        mock_membership_service.get_memberships.side_effect = [
            ServiceResult.ok(memberships),
            ServiceResult.ok([]),
        ]

        result = service.get_membership_report()

        assert result.data.retention_rate_pct == 75.0

    @patch("src.services.reports_service.membership_service")
    def test_retention_rate_none_when_no_active_or_expired(self, mock_membership_service, service):
        memberships = [make_membership(status=MembershipStatus.CANCELLED)]
        mock_membership_service.get_memberships.side_effect = [
            ServiceResult.ok(memberships),
            ServiceResult.ok([]),
        ]

        result = service.get_membership_report()

        assert result.data.retention_rate_pct is None

    @patch("src.services.reports_service.membership_service")
    def test_expiring_soon_uses_seven_day_threshold(self, mock_membership_service, service):
        mock_membership_service.get_memberships.side_effect = [
            ServiceResult.ok([]),
            ServiceResult.ok([make_membership()]),
        ]

        result = service.get_membership_report()

        assert result.data.expiring_soon_count == 1
        expiring_call_kwargs = mock_membership_service.get_memberships.call_args_list[1].kwargs
        assert expiring_call_kwargs["expiring_days"] == 7

    @patch("src.services.reports_service.membership_service")
    def test_sub_service_failure_defaults_to_empty(self, mock_membership_service, service):
        mock_membership_service.get_memberships.return_value = ServiceResult.fail("db down")

        result = service.get_membership_report()

        assert result.success is True
        assert result.data.counts_by_status == {}
        assert result.data.expiring_soon == []

    @patch("src.services.reports_service.membership_service")
    def test_unexpected_exception_returns_failure(self, mock_membership_service, service):
        mock_membership_service.get_memberships.side_effect = Exception("boom")

        result = service.get_membership_report()

        assert result.success is False
        assert "boom" in result.error


# ---------------------------------------------------------------------------
# get_attendance_report
# ---------------------------------------------------------------------------

class TestGetAttendanceReport:

    @patch("src.services.reports_service.attendance_service")
    def test_aggregates_totals_hours_and_top_members(self, mock_attendance_service, service):
        records = [
            make_attendance(member=make_member(id="mem-001", first_name="John", last_name="Doe"),
                             check_in_time=datetime(2026, 3, 15, 9, 0, tzinfo=timezone.utc)),
            make_attendance(id="att-002", member=make_member(id="mem-001", first_name="John", last_name="Doe"),
                             check_in_time=datetime(2026, 3, 15, 9, 30, tzinfo=timezone.utc)),
            make_attendance(id="att-003", member=make_member(id="mem-002", first_name="Jane", last_name="Roe"),
                             check_in_time=datetime(2026, 3, 16, 18, 0, tzinfo=timezone.utc)),
        ]
        mock_attendance_service.get_attendance_by_range.return_value = ServiceResult.ok(records)

        result = service.get_attendance_report(date(2026, 3, 15), date(2026, 3, 16))

        assert result.success is True
        report = result.data
        assert report.total_checkins == 3
        assert report.top_members[0] == ("John Doe", 2)
        assert sum(report.checkins_by_hour.values()) == 3
        assert sum(report.daily_counts.values()) == 3

    @patch("src.services.reports_service.attendance_service")
    def test_top_members_capped_at_ten(self, mock_attendance_service, service):
        records = [
            make_attendance(id=f"att-{i}", member=make_member(id=f"mem-{i}", first_name=f"Member{i}", last_name="X"))
            for i in range(15)
        ]
        mock_attendance_service.get_attendance_by_range.return_value = ServiceResult.ok(records)

        result = service.get_attendance_report(date(2026, 3, 1), date(2026, 3, 31))

        assert len(result.data.top_members) == 10

    @patch("src.services.reports_service.attendance_service")
    def test_sub_service_failure_defaults_to_empty(self, mock_attendance_service, service):
        mock_attendance_service.get_attendance_by_range.return_value = ServiceResult.fail("db down")

        result = service.get_attendance_report(date(2026, 3, 1), date(2026, 3, 31))

        assert result.success is True
        assert result.data.total_checkins == 0
        assert result.data.top_members == []

    @patch("src.services.reports_service.attendance_service")
    def test_unexpected_exception_returns_failure(self, mock_attendance_service, service):
        mock_attendance_service.get_attendance_by_range.side_effect = Exception("boom")

        result = service.get_attendance_report(date(2026, 3, 1), date(2026, 3, 31))

        assert result.success is False
        assert "boom" in result.error


# ---------------------------------------------------------------------------
# get_operational_report
# ---------------------------------------------------------------------------

class TestGetOperationalReport:

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_aggregates_all_sections_successfully(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.ok(
            [make_equipment(condition=EquipmentCondition.GOOD), make_equipment(id="eq-002", condition=EquipmentCondition.POOR)]
        )
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.ok(
            [make_maintenance(next_maintenance_date=date.today() + timedelta(days=3))]
        )
        mock_class_service.get_schedules.return_value = ServiceResult.ok([make_schedule()])
        mock_class_service.get_enrollment_count.return_value = 5
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.ok([make_instructor()])

        result = service.get_operational_report()

        assert result.success is True
        report = result.data
        assert report.equipment_by_condition == {"good": 1, "poor": 1}
        assert len(report.equipment_due_maintenance) == 1
        assert report.equipment_due_maintenance[0].id == "eq-001"
        assert len(report.class_occupancy) == 1
        schedule, enrolled, capacity, pct = report.class_occupancy[0]
        assert enrolled == 5
        assert capacity == 10
        assert pct == 50.0
        assert report.instructor_workload == {"Jane Smith": 1}

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_equipment_not_due_soon_is_excluded(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.ok([make_equipment()])
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.ok(
            [make_maintenance(next_maintenance_date=date.today() + timedelta(days=60))]
        )
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.ok([])

        result = service.get_operational_report()

        assert result.data.equipment_due_maintenance == []

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_only_most_recent_maintenance_record_counts_per_equipment(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.ok([make_equipment()])
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.ok([
            make_maintenance(id="maint-old", maintenance_date=date(2026, 1, 1), next_maintenance_date=date.today() + timedelta(days=2)),
            make_maintenance(id="maint-new", maintenance_date=date(2026, 3, 1), next_maintenance_date=date.today() + timedelta(days=90)),
        ])
        mock_class_service.get_schedules.return_value = ServiceResult.ok([])
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.ok([])

        result = service.get_operational_report()

        # Most recent record (maint-new) points 90 days out — not due soon
        assert result.data.equipment_due_maintenance == []

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_class_occupancy_none_when_unlimited_capacity(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.ok([])
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok(
            [make_schedule(class_info=make_class(max_capacity=None))]
        )
        mock_class_service.get_enrollment_count.return_value = 3
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.ok([])

        result = service.get_operational_report()

        _, enrolled, capacity, pct = result.data.class_occupancy[0]
        assert capacity is None
        assert pct is None

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_instructor_workload_counts_all_schedules_not_just_today(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.ok([])
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.side_effect = [
            ServiceResult.ok([make_schedule()]),  # today's schedules (for occupancy)
            ServiceResult.ok([make_schedule(), make_schedule(id="sch-002")]),  # all schedules (for workload)
        ]
        mock_class_service.get_enrollment_count.return_value = 0
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.ok([make_instructor()])

        result = service.get_operational_report()

        assert result.data.instructor_workload == {"Jane Smith": 2}
        # second get_schedules call should have been made with no day_of_week filter (all schedules)
        all_schedules_call_kwargs = mock_class_service.get_schedules.call_args_list[1].kwargs
        assert all_schedules_call_kwargs.get("day_of_week") is None

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_schedule_without_instructor_is_skipped(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.ok([])
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.ok([])
        mock_class_service.get_schedules.return_value = ServiceResult.ok(
            [make_schedule(instructor_id=None)]
        )
        mock_class_service.get_enrollment_count.return_value = 0
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.ok([make_instructor()])

        result = service.get_operational_report()

        assert result.data.instructor_workload == {}

    @patch("src.services.reports_service.instructor_service")
    @patch("src.services.reports_service.class_service")
    @patch("src.services.reports_service.equipment_service")
    def test_sub_service_failures_default_to_empty(
        self, mock_equipment_service, mock_class_service, mock_instructor_service, service,
    ):
        mock_equipment_service.get_all_equipment.return_value = ServiceResult.fail("db down")
        mock_equipment_service.get_maintenance_records.return_value = ServiceResult.fail("db down")
        mock_class_service.get_schedules.return_value = ServiceResult.fail("db down")
        mock_instructor_service.get_all_instructors.return_value = ServiceResult.fail("db down")

        result = service.get_operational_report()

        assert result.success is True
        assert result.data.equipment_by_condition == {}
        assert result.data.equipment_due_maintenance == []
        assert result.data.class_occupancy == []
        assert result.data.instructor_workload == {}

    @patch("src.services.reports_service.equipment_service")
    def test_unexpected_exception_returns_failure(self, mock_equipment_service, service):
        mock_equipment_service.get_all_equipment.side_effect = Exception("boom")

        result = service.get_operational_report()

        assert result.success is False
        assert "boom" in result.error
