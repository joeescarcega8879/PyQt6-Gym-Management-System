from __future__ import annotations

import logging
from typing import Optional

from src.utils.status_type import StatusType
from src.utils.error_messages import ErrorMessages
from src.utils.pdf_exporter import export_table_report
from src.models import User, FinancialReport, MembershipReport, AttendanceReport, OperationalReport
from src.models.enums import PaymentMethod, PaymentStatus
from src.services.reports_service import reports_service

from src.domain.permissions import Permissions
from src.domain.permissions_service import PermissionService

logger = logging.getLogger(__name__)


class ReportsPresenter:
    """Presenter for the ReportsView, coordinating the 4 read-only report tabs and PDF export."""

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view = view
        self.main_app = main_app
        self.status_handler = status_handler
        self._current_user: Optional[User] = current_user

        self._last_financial_report: Optional[FinancialReport] = None
        self._last_membership_report: Optional[MembershipReport] = None
        self._last_attendance_report: Optional[AttendanceReport] = None
        self._last_operational_report: Optional[OperationalReport] = None

        self._connect_signals()
        self._load_user_information()
        self._handle_filter_financial()
        self._handle_refresh_memberships()
        self._handle_filter_attendance()
        self._handle_refresh_operational()

    def _connect_signals(self) -> None:
        self.view.filter_financial_requested.connect(self._handle_filter_financial)
        self.view.export_financial_requested.connect(self._handle_export_financial)

        self.view.refresh_memberships_requested.connect(self._handle_refresh_memberships)
        self.view.export_memberships_requested.connect(self._handle_export_memberships)

        self.view.filter_attendance_requested.connect(self._handle_filter_attendance)
        self.view.export_attendance_requested.connect(self._handle_export_attendance)

        self.view.refresh_operational_requested.connect(self._handle_refresh_operational)
        self.view.export_operational_requested.connect(self._handle_export_operational)

    # ------------------------------------------------------------------ #
    # Financial tab
    # ------------------------------------------------------------------ #

    def _handle_filter_financial(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return

        result = reports_service.get_financial_report(
            date_from=self.view.get_financial_date_from(),
            date_to=self.view.get_financial_date_to(),
            payment_method=self._parse_payment_method(self.view.get_financial_method()),
            status=self._parse_payment_status(self.view.get_financial_status()),
        )

        if result.success:
            self._last_financial_report = result.data
            self.view.set_financial_summary(result.data.total_revenue, result.data.transaction_count, result.data.revenue_change_pct)
            self.view.populate_financial_table(result.data.payments)
        else:
            logger.error(f"Load financial report failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_export_financial(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return
        if self._last_financial_report is None:
            self._emit_error(ErrorMessages.REPORTS_NO_DATA_TO_EXPORT)
            return

        file_path = self.view.prompt_save_pdf_path("financial_report.pdf")
        if not file_path:
            return

        report = self._last_financial_report
        summary_lines = [
            f"Total Revenue: ${report.total_revenue:.2f}",
            f"Transactions: {report.transaction_count}",
            f"Previous Period Revenue: ${report.previous_period_revenue:.2f}",
        ]
        headers = ["Member", "Amount", "Method", "Date", "Status"]
        rows = [
            [
                p.member.full_name if p.member else "",
                f"${p.amount:.2f}",
                p.payment_method.value.capitalize(),
                p.payment_date.strftime("%Y-%m-%d %I:%M %p"),
                p.status.value.capitalize(),
            ]
            for p in report.payments
        ]
        self._export_pdf(file_path, "Financial Report", summary_lines, headers, rows)

    # ------------------------------------------------------------------ #
    # Memberships tab
    # ------------------------------------------------------------------ #

    def _handle_refresh_memberships(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return

        result = reports_service.get_membership_report()

        if result.success:
            self._last_membership_report = result.data
            self.view.set_membership_summary(result.data.retention_rate_pct)
            self.view.populate_membership_status_table(result.data.counts_by_status)
            self.view.populate_membership_plan_table(result.data.counts_by_plan)
            self.view.populate_memberships_expiring_table(result.data.expiring_soon)
        else:
            logger.error(f"Load membership report failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_export_memberships(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return
        if self._last_membership_report is None:
            self._emit_error(ErrorMessages.REPORTS_NO_DATA_TO_EXPORT)
            return

        report = self._last_membership_report
        retention_str = "—" if report.retention_rate_pct is None else f"{report.retention_rate_pct:.1f}%"
        summary_lines = [f"Retention Rate: {retention_str}", f"Expiring Soon (7 days): {report.expiring_soon_count}"]
        headers = ["Status", "Count"]
        rows = [[status.capitalize(), str(count)] for status, count in report.counts_by_status.items()]

        file_path = self.view.prompt_save_pdf_path("membership_report.pdf")
        if not file_path:
            return
        self._export_pdf(file_path, "Membership Report", summary_lines, headers, rows)

    # ------------------------------------------------------------------ #
    # Attendance tab
    # ------------------------------------------------------------------ #

    def _handle_filter_attendance(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return

        result = reports_service.get_attendance_report(
            date_from=self.view.get_attendance_date_from(),
            date_to=self.view.get_attendance_date_to(),
        )

        if result.success:
            self._last_attendance_report = result.data
            self.view.set_attendance_summary(result.data.total_checkins)
            self.view.populate_attendance_hour_table(result.data.checkins_by_hour)
            self.view.populate_attendance_top_members_table(result.data.top_members)
        else:
            logger.error(f"Load attendance report failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_export_attendance(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return
        if self._last_attendance_report is None:
            self._emit_error(ErrorMessages.REPORTS_NO_DATA_TO_EXPORT)
            return

        report = self._last_attendance_report
        summary_lines = [f"Total Check-ins: {report.total_checkins}"]
        headers = ["Member", "Check-ins"]
        rows = [[name, str(count)] for name, count in report.top_members]

        file_path = self.view.prompt_save_pdf_path("attendance_report.pdf")
        if not file_path:
            return
        self._export_pdf(file_path, "Attendance Report", summary_lines, headers, rows)

    # ------------------------------------------------------------------ #
    # Operational tab
    # ------------------------------------------------------------------ #

    def _handle_refresh_operational(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return

        result = reports_service.get_operational_report()

        if result.success:
            self._last_operational_report = result.data
            self.view.populate_equipment_condition_table(result.data.equipment_by_condition)
            self.view.populate_equipment_maintenance_due_table(result.data.equipment_due_maintenance)
            self.view.populate_class_occupancy_table(result.data.class_occupancy)
            self.view.populate_instructor_workload_table(result.data.instructor_workload)
        else:
            logger.error(f"Load operational report failed: {result.error}")
            self.view.show_error(result.error)

    def _handle_export_operational(self) -> None:
        if not PermissionService.has_permission(self._current_user, Permissions.REPORTS_READ):
            self._emit_error(ErrorMessages.REPORTS_NO_PERMISSION_READ)
            return
        if self._last_operational_report is None:
            self._emit_error(ErrorMessages.REPORTS_NO_DATA_TO_EXPORT)
            return

        report = self._last_operational_report
        summary_lines = [f"Equipment Due for Maintenance: {len(report.equipment_due_maintenance)}"]
        headers = ["Condition", "Count"]
        rows = [[condition.replace("_", " ").capitalize(), str(count)] for condition, count in report.equipment_by_condition.items()]

        file_path = self.view.prompt_save_pdf_path("operational_report.pdf")
        if not file_path:
            return
        self._export_pdf(file_path, "Operational Report", summary_lines, headers, rows)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _export_pdf(self, file_path: str, title: str, summary_lines: list[str], headers: list[str], rows: list[list[str]]) -> None:
        try:
            export_table_report(file_path, title, summary_lines, headers, rows)
            self.view.show_export_success(file_path)
            self._emit_success(ErrorMessages.REPORTS_EXPORT_SUCCESS)
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            self._emit_error(ErrorMessages.REPORTS_EXPORT_FAILED)

    @staticmethod
    def _parse_payment_method(value: Optional[str]) -> Optional[PaymentMethod]:
        if not value:
            return None
        try:
            return PaymentMethod(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_payment_status(value: Optional[str]) -> Optional[PaymentStatus]:
        if not value:
            return None
        try:
            return PaymentStatus(value)
        except ValueError:
            return None

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role": self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_info(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.INFO)
