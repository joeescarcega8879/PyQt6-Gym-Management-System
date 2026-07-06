import os
from datetime import date, timedelta
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize
from PyQt6.QtWidgets import QWidget, QMessageBox, QFileDialog
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon
from src.config.settings import config


class ReportsView(QWidget):

    # Tab 1 — Financial
    filter_financial_requested = pyqtSignal()
    export_financial_requested = pyqtSignal()

    # Tab 2 — Memberships
    refresh_memberships_requested = pyqtSignal()
    export_memberships_requested  = pyqtSignal()

    # Tab 3 — Attendance
    filter_attendance_requested = pyqtSignal()
    export_attendance_requested = pyqtSignal()

    # Tab 4 — Operational
    refresh_operational_requested = pyqtSignal()
    export_operational_requested  = pyqtSignal()

    def __init__(self) -> None:
        super(ReportsView, self).__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "reports_view.ui")
        uic.loadUi(ui_path, self)

        # Financial tab
        self.btn_filter_financial.clicked.connect(self.filter_financial_requested.emit)
        self.btn_export_financial.clicked.connect(self.export_financial_requested.emit)

        # Memberships tab
        self.btn_refresh_memberships.clicked.connect(self.refresh_memberships_requested.emit)
        self.btn_export_memberships.clicked.connect(self.export_memberships_requested.emit)

        # Attendance tab
        self.btn_filter_attendance.clicked.connect(self.filter_attendance_requested.emit)
        self.btn_export_attendance.clicked.connect(self.export_attendance_requested.emit)

        # Operational tab
        self.btn_refresh_operational.clicked.connect(self.refresh_operational_requested.emit)
        self.btn_export_operational.clicked.connect(self.export_operational_requested.emit)

        # Close
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        self.init_combo_boxes()

        # Date defaults: Financial = current month, Attendance = last 7 days
        today = QDate.currentDate()
        for date_edit in (self.date_financial_from, self.date_financial_to,
                          self.date_attendance_from, self.date_attendance_to):
            date_edit.setMinimumDate(QDate(1900, 1, 1))

        self.date_financial_from.setDate(QDate(today.year(), today.month(), 1))
        self.date_financial_to.setDate(today)
        self.date_attendance_from.setDate(today.addDays(-7))
        self.date_attendance_to.setDate(today)

    def init_combo_boxes(self) -> None:
        self.combo_financial_method.addItem("All", None)
        self.combo_financial_method.addItem("Cash", "cash")
        self.combo_financial_method.addItem("Card", "card")
        self.combo_financial_method.addItem("Transfer", "transfer")
        self.combo_financial_method.addItem("Other", "other")

        self.combo_financial_status.addItem("All", None)
        self.combo_financial_status.addItem("Completed", "completed")
        self.combo_financial_status.addItem("Pending", "pending")
        self.combo_financial_status.addItem("Cancelled", "cancelled")
        self.combo_financial_status.addItem("Refunded", "refunded")

    # ------------------------------------------------------------------ #
    # Getters — Financial tab
    # ------------------------------------------------------------------ #

    def get_financial_date_from(self) -> date:
        return self.date_financial_from.date().toPyDate()

    def get_financial_date_to(self) -> date:
        return self.date_financial_to.date().toPyDate()

    def get_financial_method(self) -> str | None:
        return self.combo_financial_method.currentData()

    def get_financial_status(self) -> str | None:
        return self.combo_financial_status.currentData()

    # ------------------------------------------------------------------ #
    # Getters — Attendance tab
    # ------------------------------------------------------------------ #

    def get_attendance_date_from(self) -> date:
        return self.date_attendance_from.date().toPyDate()

    def get_attendance_date_to(self) -> date:
        return self.date_attendance_to.date().toPyDate()

    # ------------------------------------------------------------------ #
    # Setters / population — Financial tab
    # ------------------------------------------------------------------ #

    def set_financial_summary(self, total_revenue: float, transaction_count: int, revenue_change_pct: float | None) -> None:
        self.label_total_revenue.setText(f"Total Revenue: ${total_revenue:.2f}")
        self.label_transaction_count.setText(f"Transactions: {transaction_count}")
        if revenue_change_pct is None:
            self.label_revenue_change.setText("vs Previous Period: —")
        else:
            sign = "+" if revenue_change_pct >= 0 else ""
            self.label_revenue_change.setText(f"vs Previous Period: {sign}{revenue_change_pct:.1f}%")

    def populate_financial_table(self, payments: list) -> None:
        headers = ["Member", "Amount", "Method", "Date", "Status"]
        rows = [
            (
                p.member.full_name if p.member else "",
                f"${p.amount:.2f}",
                p.payment_method.value.capitalize(),
                p.payment_date.strftime("%Y-%m-%d %I:%M %p"),
                p.status.value.capitalize(),
            )
            for p in payments
        ]
        SetFormat.format_qtablewidget(self.financial_table, headers, rows)

    # ------------------------------------------------------------------ #
    # Setters / population — Memberships tab
    # ------------------------------------------------------------------ #

    def set_membership_summary(self, retention_rate_pct: float | None) -> None:
        text = "—" if retention_rate_pct is None else f"{retention_rate_pct:.1f}%"
        self.label_retention_rate.setText(f"Retention Rate: {text}")

    def populate_membership_status_table(self, counts_by_status: dict) -> None:
        headers = ["Status", "Count"]
        rows = [(status.capitalize(), str(count)) for status, count in counts_by_status.items()]
        SetFormat.format_qtablewidget(self.membership_status_table, headers, rows)

    def populate_membership_plan_table(self, counts_by_plan: dict) -> None:
        headers = ["Plan", "Count"]
        rows = [(plan, str(count)) for plan, count in counts_by_plan.items()]
        SetFormat.format_qtablewidget(self.membership_plan_table, headers, rows)

    def populate_memberships_expiring_table(self, memberships: list) -> None:
        headers = ["Member Code", "Member Name", "Plan", "End Date", "Days Left"]
        rows = []
        for m in memberships:
            days_left = (m.end_date - date.today()).days if m.end_date else None
            rows.append((
                m.member.member_code if m.member else "",
                m.member.full_name if m.member else "",
                m.plan.name if m.plan else "",
                m.end_date.strftime("%Y-%m-%d") if m.end_date else "",
                str(days_left) if days_left is not None and days_left >= 0 else "Expired",
            ))
        SetFormat.format_qtablewidget(self.memberships_expiring_table, headers, rows)

    # ------------------------------------------------------------------ #
    # Setters / population — Attendance tab
    # ------------------------------------------------------------------ #

    def set_attendance_summary(self, total_checkins: int) -> None:
        self.label_total_checkins.setText(f"Total Check-ins: {total_checkins}")

    def populate_attendance_hour_table(self, checkins_by_hour: dict) -> None:
        headers = ["Hour", "Check-ins"]
        rows = [
            (f"{hour:02d}:00", str(count))
            for hour, count in sorted(checkins_by_hour.items())
        ]
        SetFormat.format_qtablewidget(self.attendance_hour_table, headers, rows)

    def populate_attendance_top_members_table(self, top_members: list) -> None:
        headers = ["Member", "Check-ins"]
        rows = [(name, str(count)) for name, count in top_members]
        SetFormat.format_qtablewidget(self.attendance_top_members_table, headers, rows)

    # ------------------------------------------------------------------ #
    # Setters / population — Operational tab
    # ------------------------------------------------------------------ #

    def populate_equipment_condition_table(self, counts_by_condition: dict) -> None:
        headers = ["Condition", "Count"]
        rows = [(condition.replace("_", " ").capitalize(), str(count)) for condition, count in counts_by_condition.items()]
        SetFormat.format_qtablewidget(self.equipment_condition_table, headers, rows)

    def populate_equipment_maintenance_due_table(self, equipment: list) -> None:
        headers = ["Equipment", "Category", "Condition"]
        rows = [
            (e.name, e.category or "", e.condition.value.replace("_", " ").capitalize())
            for e in equipment
        ]
        SetFormat.format_qtablewidget(self.equipment_maintenance_due_table, headers, rows)

    def populate_class_occupancy_table(self, occupancy: list) -> None:
        headers = ["Class", "Room", "Enrolled", "Capacity", "Occupancy"]
        rows = []
        for schedule, enrolled, capacity, pct in occupancy:
            class_name = schedule.class_info.name if schedule.class_info else ""
            capacity_str = str(capacity) if capacity is not None else "Unlimited"
            pct_str = f"{pct:.1f}%" if pct is not None else "—"
            rows.append((class_name, schedule.room or "", str(enrolled), capacity_str, pct_str))
        SetFormat.format_qtablewidget(self.class_occupancy_table, headers, rows)

    def populate_instructor_workload_table(self, workload: dict) -> None:
        headers = ["Instructor", "Scheduled Classes"]
        rows = [(name, str(count)) for name, count in workload.items()]
        SetFormat.format_qtablewidget(self.instructor_workload_table, headers, rows)

    # ------------------------------------------------------------------ #
    # Shared
    # ------------------------------------------------------------------ #

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def show_export_success(self, file_path: str) -> None:
        QMessageBox.information(self, "Export Successful", f"Report saved to:\n{file_path}")

    def prompt_save_pdf_path(self, default_filename: str) -> str | None:
        default_path = str(config.EXPORTS_DIR / default_filename)
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_path, "PDF Files (*.pdf)")
        return file_path or None
