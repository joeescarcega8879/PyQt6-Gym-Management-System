"""
Dashboard aggregation service.

Unlike the other services, DashboardService does not talk to the database
directly. It composes data already exposed by the other service layers
(member/payment/attendance/membership/class) into a single summary object,
avoiding duplicated SQL/query logic.
"""
from __future__ import annotations
import logging
from datetime import date

from src.models import DashboardSummary
from src.services import ServiceResult
from src.services.member_service import member_service
from src.services.payment_service import payment_service
from src.services.attendance_service import attendance_service
from src.services.membership_service import membership_service
from src.services.class_service import class_service
from src.models.enums import PaymentStatus

logger = logging.getLogger(__name__)

# Number of days ahead considered "expiring soon" for memberships
_EXPIRING_DAYS_THRESHOLD = 7


class DashboardService:
    """Aggregates KPI data from the other service layers for the Dashboard view."""

    def get_summary(self) -> ServiceResult[DashboardSummary]:
        """
        Builds a DashboardSummary with:
        - active_members: count of active members
        - monthly_revenue: sum of completed payments in the current calendar month
        - today_checkins: count of attendance records for today
        - expiring_memberships / expiring_memberships_count: active memberships
          expiring within the next _EXPIRING_DAYS_THRESHOLD days
        - today_schedules: active class schedules for today's day of week

        If any sub-query fails, the error is logged and that section falls
        back to an empty/zero value rather than failing the whole summary,
        so a single broken feature doesn't take down the entire dashboard.
        """
        try:
            summary = DashboardSummary(
                active_members=self._get_active_members_count(),
                monthly_revenue=self._get_monthly_revenue(),
                today_checkins=self._get_today_checkins_count(),
            )

            expiring = self._get_expiring_memberships()
            summary.expiring_memberships = expiring
            summary.expiring_memberships_count = len(expiring)

            summary.today_schedules = self._get_today_schedules()

            return ServiceResult.ok(summary)
        except Exception as e:
            logger.error(f"Error building dashboard summary: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Private helpers — each is resilient to its own sub-service failing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_active_members_count() -> int:
        result = member_service.get_all_members(include_inactive=False)
        if result.success and result.data is not None:
            return len(result.data)
        logger.warning(f"Dashboard: failed to fetch active members: {result.error}")
        return 0

    @staticmethod
    def _get_monthly_revenue() -> float:
        today = date.today()
        month_start = today.replace(day=1)
        result = payment_service.get_payments(
            status=PaymentStatus.COMPLETED,
            date_from=month_start,
            date_to=today,
        )
        if result.success and result.data is not None:
            return sum(p.amount for p in result.data)
        logger.warning(f"Dashboard: failed to fetch monthly revenue: {result.error}")
        return 0.0

    @staticmethod
    def _get_today_checkins_count() -> int:
        result = attendance_service.get_attendance_by_date(date.today())
        if result.success and result.data is not None:
            return len(result.data)
        logger.warning(f"Dashboard: failed to fetch today's check-ins: {result.error}")
        return 0

    @staticmethod
    def _get_expiring_memberships() -> list:
        result = membership_service.get_memberships(expiring_days=_EXPIRING_DAYS_THRESHOLD)
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Dashboard: failed to fetch expiring memberships: {result.error}")
        return []

    @staticmethod
    def _get_today_schedules() -> list:
        # ClassSchedule.day_of_week: 0 = Sunday, 6 = Saturday.
        # date.weekday(): 0 = Monday, 6 = Sunday.
        today_day_of_week = (date.today().weekday() + 1) % 7
        result = class_service.get_schedules(day_of_week=today_day_of_week, include_inactive=False)
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Dashboard: failed to fetch today's schedules: {result.error}")
        return []


dashboard_service = DashboardService()
