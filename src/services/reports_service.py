"""
Reports aggregation service.

Like DashboardService, ReportsService does not talk to the database
directly. It composes data already exposed by the other service layers
(payment/membership/attendance/class/equipment/instructor) into report
objects for the Reports module, avoiding duplicated SQL/query logic.
"""
from __future__ import annotations
import logging
from datetime import date, timedelta
from typing import Optional

from src.models import (
    FinancialReport,
    MembershipReport,
    AttendanceReport,
    OperationalReport,
    Payment,
    MemberMembership,
    Equipment,
)
from src.models.enums import PaymentMethod, PaymentStatus, MembershipStatus
from src.services import ServiceResult
from src.services.payment_service import payment_service
from src.services.membership_service import membership_service
from src.services.attendance_service import attendance_service
from src.services.class_service import class_service
from src.services.equipment_service import equipment_service
from src.services.instructor_service import instructor_service

logger = logging.getLogger(__name__)

# Number of days ahead considered "expiring soon" for memberships / "due soon" for maintenance
_EXPIRING_DAYS_THRESHOLD = 7
_MAINTENANCE_DUE_THRESHOLD_DAYS = 7


class ReportsService:
    """Aggregates data from the other service layers into report objects for the Reports view."""

    # ------------------------------------------------------------------ #
    # Financial report
    # ------------------------------------------------------------------ #

    def get_financial_report(
        self,
        date_from: date,
        date_to: date,
        payment_method: Optional[PaymentMethod] = None,
        status: Optional[PaymentStatus] = None,
    ) -> ServiceResult[FinancialReport]:
        """
        Builds a FinancialReport for the given date range.

        `total_revenue`/`revenue_by_method` always reflect COMPLETED payments only
        (regardless of the `status` filter), matching the "revenue" convention
        already used by DashboardService. `payments` (the detail table) respects
        whatever `status`/`payment_method` filters were passed in.
        """
        try:
            payments = self._get_payments_for_range(date_from, date_to, payment_method, status)
            completed = self._get_completed_payments_for_range(date_from, date_to, payment_method)

            total_revenue = sum(p.amount for p in completed)
            revenue_by_method: dict = {}
            for p in completed:
                revenue_by_method[p.payment_method.value] = revenue_by_method.get(p.payment_method.value, 0.0) + p.amount

            period_days = (date_to - date_from).days + 1
            previous_date_to = date_from - timedelta(days=1)
            previous_date_from = previous_date_to - timedelta(days=period_days - 1)
            previous_completed = self._get_completed_payments_for_range(previous_date_from, previous_date_to, payment_method)
            previous_revenue = sum(p.amount for p in previous_completed)

            revenue_change_pct = None
            if previous_revenue > 0:
                revenue_change_pct = round(((total_revenue - previous_revenue) / previous_revenue) * 100, 1)

            report = FinancialReport(
                total_revenue=total_revenue,
                transaction_count=len(payments),
                revenue_by_method=revenue_by_method,
                previous_period_revenue=previous_revenue,
                revenue_change_pct=revenue_change_pct,
                payments=payments,
            )
            return ServiceResult.ok(report)
        except Exception as e:
            logger.error(f"Error building financial report: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Membership report
    # ------------------------------------------------------------------ #

    def get_membership_report(self) -> ServiceResult[MembershipReport]:
        """
        Builds a MembershipReport with status/plan distribution and a retention
        proxy. `retention_rate_pct` = active / (active + expired) — an
        approximation, not a true renewal rate (the schema has no flag
        distinguishing a renewal from a fresh signup).
        """
        try:
            memberships = self._get_all_memberships()

            counts_by_status: dict = {}
            counts_by_plan: dict = {}
            for m in memberships:
                counts_by_status[m.status.value] = counts_by_status.get(m.status.value, 0) + 1
                if m.plan:
                    counts_by_plan[m.plan.name] = counts_by_plan.get(m.plan.name, 0) + 1

            active_count = counts_by_status.get(MembershipStatus.ACTIVE.value, 0)
            expired_count = counts_by_status.get(MembershipStatus.EXPIRED.value, 0)
            retention_rate_pct = None
            if (active_count + expired_count) > 0:
                retention_rate_pct = round((active_count / (active_count + expired_count)) * 100, 1)

            expiring_soon = self._get_expiring_memberships()

            report = MembershipReport(
                counts_by_status=counts_by_status,
                counts_by_plan=counts_by_plan,
                retention_rate_pct=retention_rate_pct,
                expiring_soon_count=len(expiring_soon),
                expiring_soon=expiring_soon,
            )
            return ServiceResult.ok(report)
        except Exception as e:
            logger.error(f"Error building membership report: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Attendance report
    # ------------------------------------------------------------------ #

    def get_attendance_report(self, date_from: date, date_to: date) -> ServiceResult[AttendanceReport]:
        """Builds an AttendanceReport: totals, peak hours, top members, daily counts."""
        try:
            records = self._get_attendance_for_range(date_from, date_to)

            checkins_by_hour: dict = {}
            daily_counts: dict = {}
            member_counts: dict = {}

            for r in records:
                local_check_in = r.check_in_time.astimezone()
                hour = local_check_in.hour
                checkins_by_hour[hour] = checkins_by_hour.get(hour, 0) + 1

                day_key = local_check_in.date().isoformat()
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

                if r.member:
                    name = r.member.full_name
                    member_counts[name] = member_counts.get(name, 0) + 1

            top_members = sorted(member_counts.items(), key=lambda item: item[1], reverse=True)[:10]

            report = AttendanceReport(
                total_checkins=len(records),
                checkins_by_hour=checkins_by_hour,
                top_members=top_members,
                daily_counts=daily_counts,
            )
            return ServiceResult.ok(report)
        except Exception as e:
            logger.error(f"Error building attendance report: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Operational report
    # ------------------------------------------------------------------ #

    def get_operational_report(self) -> ServiceResult[OperationalReport]:
        """Builds an OperationalReport: equipment condition/maintenance, class occupancy, instructor workload."""
        try:
            report = OperationalReport(
                equipment_by_condition=self._get_equipment_by_condition(),
                equipment_due_maintenance=self._get_equipment_due_maintenance(),
                class_occupancy=self._get_class_occupancy_today(),
                instructor_workload=self._get_instructor_workload(),
            )
            return ServiceResult.ok(report)
        except Exception as e:
            logger.error(f"Error building operational report: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Private helpers — each is resilient to its own sub-service failing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_payments_for_range(
        date_from: date, date_to: date,
        payment_method: Optional[PaymentMethod],
        status: Optional[PaymentStatus],
    ) -> list[Payment]:
        result = payment_service.get_payments(status=status, payment_method=payment_method, date_from=date_from, date_to=date_to)
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Reports: failed to fetch payments: {result.error}")
        return []

    @staticmethod
    def _get_completed_payments_for_range(
        date_from: date, date_to: date, payment_method: Optional[PaymentMethod],
    ) -> list[Payment]:
        result = payment_service.get_payments(
            status=PaymentStatus.COMPLETED, payment_method=payment_method, date_from=date_from, date_to=date_to,
        )
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Reports: failed to fetch completed payments: {result.error}")
        return []

    @staticmethod
    def _get_all_memberships() -> list[MemberMembership]:
        result = membership_service.get_memberships()
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Reports: failed to fetch memberships: {result.error}")
        return []

    @staticmethod
    def _get_expiring_memberships() -> list[MemberMembership]:
        result = membership_service.get_memberships(expiring_days=_EXPIRING_DAYS_THRESHOLD)
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Reports: failed to fetch expiring memberships: {result.error}")
        return []

    @staticmethod
    def _get_attendance_for_range(date_from: date, date_to: date) -> list:
        result = attendance_service.get_attendance_by_range(date_from, date_to)
        if result.success and result.data is not None:
            return result.data
        logger.warning(f"Reports: failed to fetch attendance: {result.error}")
        return []

    @staticmethod
    def _get_equipment_by_condition() -> dict:
        result = equipment_service.get_all_equipment()
        if not (result.success and result.data is not None):
            logger.warning(f"Reports: failed to fetch equipment: {result.error}")
            return {}
        counts: dict = {}
        for e in result.data:
            counts[e.condition.value] = counts.get(e.condition.value, 0) + 1
        return counts

    @staticmethod
    def _get_equipment_due_maintenance() -> list[Equipment]:
        maintenance_result = equipment_service.get_maintenance_records()
        if not (maintenance_result.success and maintenance_result.data is not None):
            logger.warning(f"Reports: failed to fetch maintenance records: {maintenance_result.error}")
            return []

        equipment_result = equipment_service.get_all_equipment()
        if not (equipment_result.success and equipment_result.data is not None):
            logger.warning(f"Reports: failed to fetch equipment: {equipment_result.error}")
            return []

        # Keep only the most recent maintenance record per equipment item
        latest_by_equipment: dict = {}
        for record in maintenance_result.data:
            existing = latest_by_equipment.get(record.equipment_id)
            if existing is None or record.maintenance_date > existing.maintenance_date:
                latest_by_equipment[record.equipment_id] = record

        threshold = date.today() + timedelta(days=_MAINTENANCE_DUE_THRESHOLD_DAYS)
        due_ids = {
            equipment_id for equipment_id, record in latest_by_equipment.items()
            if record.next_maintenance_date and record.next_maintenance_date <= threshold
        }

        return [e for e in equipment_result.data if e.id in due_ids]

    @staticmethod
    def _get_class_occupancy_today() -> list[tuple]:
        today = date.today()
        # ClassSchedule.day_of_week: 0=Sunday..6=Saturday. date.weekday(): 0=Monday..6=Sunday.
        today_day_of_week = (today.weekday() + 1) % 7

        result = class_service.get_schedules(day_of_week=today_day_of_week, include_inactive=False)
        if not (result.success and result.data is not None):
            logger.warning(f"Reports: failed to fetch today's schedules: {result.error}")
            return []

        occupancy = []
        for schedule in result.data:
            enrolled = class_service.get_enrollment_count(schedule.id, today)
            capacity = schedule.class_info.max_capacity if schedule.class_info else None
            pct = round((enrolled / capacity) * 100, 1) if capacity else None
            occupancy.append((schedule, enrolled, capacity, pct))
        return occupancy

    @staticmethod
    def _get_instructor_workload() -> dict:
        schedules_result = class_service.get_schedules(include_inactive=False)
        if not (schedules_result.success and schedules_result.data is not None):
            logger.warning(f"Reports: failed to fetch schedules: {schedules_result.error}")
            return {}

        instructors_result = instructor_service.get_all_instructors()
        if not (instructors_result.success and instructors_result.data is not None):
            logger.warning(f"Reports: failed to fetch instructors: {instructors_result.error}")
            return {}

        id_to_name = {i.id: i.full_name for i in instructors_result.data}

        workload: dict = {}
        for schedule in schedules_result.data:
            if not schedule.instructor_id:
                continue
            name = id_to_name.get(schedule.instructor_id, "Unknown")
            workload[name] = workload.get(name, 0) + 1
        return workload


reports_service = ReportsService()
