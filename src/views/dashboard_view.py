import os
from datetime import date
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtWidgets import QWidget

from src.assets.resources_rc import get_icon
from src.utils.set_format import SetFormat
from src.models import DashboardSummary


class DashboardView(QWidget):
    """UI for the Dashboard module — KPI cards + detail tables. No business logic."""

    # ------------------------------------------------------------------ #
    # Signals
    # ------------------------------------------------------------------ #
    refresh_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "dashboard_view.ui")
        uic.loadUi(ui_path, self)

        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        self.btn_refresh.clicked.connect(self.refresh_requested.emit)

    # ------------------------------------------------------------------ #
    # Shared
    # ------------------------------------------------------------------ #

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    # ------------------------------------------------------------------ #
    # KPI cards
    # ------------------------------------------------------------------ #

    def set_summary(self, summary: DashboardSummary) -> None:
        """Populates KPI cards and detail tables from a DashboardSummary."""
        self.label_card_members_value.setText(str(summary.active_members))
        self.label_card_revenue_value.setText(f"${summary.monthly_revenue:.2f}")
        self.label_card_checkins_value.setText(str(summary.today_checkins))
        self.label_card_expiring_value.setText(str(summary.expiring_memberships_count))

        self.populate_today_schedules_table(summary.today_schedules)
        self.populate_expiring_memberships_table(summary.expiring_memberships)

    # ------------------------------------------------------------------ #
    # Detail tables
    # ------------------------------------------------------------------ #

    def populate_today_schedules_table(self, schedules: list) -> None:
        headers = ["Class", "Start", "End", "Room"]
        rows = []
        for s in schedules:
            class_name = s.class_info.name if s.class_info else ""
            rows.append((
                class_name,
                str(s.start_time)[:5],
                str(s.end_time)[:5],
                s.room or "",
            ))
        SetFormat.format_qtablewidget(self.today_schedules_table, headers, rows)

    def populate_expiring_memberships_table(self, memberships: list) -> None:
        headers = ["Member Code", "Member Name", "Plan", "End Date", "Days Left"]
        today = date.today()
        rows = []
        for ms in memberships:
            code      = ms.member.member_code if ms.member else ""
            name      = ms.member.full_name    if ms.member else ""
            plan_name = ms.plan.name           if ms.plan   else ""
            end       = ms.end_date.strftime("%Y-%m-%d") if ms.end_date else ""
            if ms.end_date:
                days_left = (ms.end_date - today).days
                days_str  = str(days_left) if days_left >= 0 else "Expired"
            else:
                days_str = ""
            rows.append((code, name, plan_name, end, days_str))
        SetFormat.format_qtablewidget(self.expiring_memberships_table, headers, rows)
