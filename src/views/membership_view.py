import os
from datetime import date
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize
from PyQt6.QtWidgets import QWidget
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon


class MembershipView(QWidget):

    # Tab 1 — Plans signals
    save_plan_requested     = pyqtSignal()
    new_plan_requested      = pyqtSignal()
    cancel_plan_requested   = pyqtSignal()
    toggle_status_requested = pyqtSignal()
    plan_selected           = pyqtSignal()

    # Tab 2 — Memberships signals
    filter_requested            = pyqtSignal()
    assign_requested            = pyqtSignal()
    suspend_requested           = pyqtSignal()
    cancel_membership_requested = pyqtSignal()
    reactivate_requested        = pyqtSignal()

    def __init__(self) -> None:
        super(MembershipView, self).__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "membership_view.ui")
        uic.loadUi(ui_path, self)

        # Plans tab
        self.btn_save_plan.clicked.connect(self.save_plan_requested.emit)
        self.btn_new_plan.clicked.connect(self.new_plan_requested.emit)
        self.btn_cancel_plan.clicked.connect(self.cancel_plan_requested.emit)
        self.btn_toggle_status.clicked.connect(self.toggle_status_requested.emit)
        self.plans_table.itemSelectionChanged.connect(self.plan_selected.emit)

        # Memberships tab
        self.btn_filter.clicked.connect(self.filter_requested.emit)
        self.btn_clear_filters.clicked.connect(self._clear_filters)
        self.btn_assign.clicked.connect(self.assign_requested.emit)
        self.btn_suspend.clicked.connect(self.suspend_requested.emit)
        self.btn_cancel_membership.clicked.connect(self.cancel_membership_requested.emit)
        self.btn_reactivate.clicked.connect(self.reactivate_requested.emit)

        # Close
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        # Date defaults
        self.date_to.setDate(QDate.currentDate())
        self.date_start.setDate(QDate.currentDate())

    def _clear_filters(self) -> None:
        self.input_search_member.clear()
        self.combo_status.setCurrentIndex(0)
        self.date_from.setDate(QDate(2026, 1, 1))
        self.date_to.setDate(QDate.currentDate())
        self.combo_expiring.setCurrentIndex(0)
        self.filter_requested.emit()

    # ------------------------------------------------------------------ #
    # Getters — Plans tab
    # ------------------------------------------------------------------ #

    def get_plan_name(self) -> str:
        return self.input_plan_name.text().strip()

    def get_plan_description(self) -> str | None:
        return self.input_description.text().strip() or None

    def get_duration_days(self) -> int:
        return self.spin_duration_days.value()

    def get_price(self) -> float:
        return self.spin_price.value()

    def get_has_class_access(self) -> bool:
        return self.check_has_class_access.isChecked()

    def get_max_classes(self) -> int | None:
        value = self.spin_max_classes.value()
        return None if value == 0 else value

    def get_is_active(self) -> bool:
        return self.check_is_active.isChecked()

    def get_selected_plan_id(self) -> str | None:
        current_row = self.plans_table.currentRow()
        if current_row < 0:
            return None
        item = self.plans_table.item(current_row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    # ------------------------------------------------------------------ #
    # Getters — Memberships tab
    # ------------------------------------------------------------------ #

    def get_filter_search_term(self) -> str | None:
        return self.input_search_member.text().strip() or None

    def get_filter_status(self) -> str | None:
        text = self.combo_status.currentText().lower()
        return None if text == "all" else text

    def get_date_from(self) -> date | None:
        d = self.date_from.date().toPyDate()
        if d.year <= 2026 and d.month == 1 and d.day == 1:
            return None
        return d

    def get_date_to(self) -> date:
        return self.date_to.date().toPyDate()

    def get_expiring_days(self) -> int | None:
        text = self.combo_expiring.currentText()
        if text == "All":
            return None
        try:
            return int(text.split()[0])
        except (ValueError, IndexError):
            return None

    def get_assign_search_term(self) -> str | None:
        return self.input_assign_search.text().strip() or None

    def get_assign_plan_id(self) -> str | None:
        return self.combo_plan.currentData()

    def get_start_date(self) -> date:
        return self.date_start.date().toPyDate()

    def get_assign_notes(self) -> str | None:
        return self.input_notes.text().strip() or None

    def get_selected_membership_id(self) -> str | None:
        current_row = self.memberships_table.currentRow()
        if current_row < 0:
            return None
        item = self.memberships_table.item(current_row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    # ------------------------------------------------------------------ #
    # Setters
    # ------------------------------------------------------------------ #

    def populate_plans_table(self, plans: list) -> None:
        headers = ["Name", "Duration", "Price", "Class Access", "Max Classes/Week", "Status"]
        rows = []
        for plan in plans:
            max_cls = str(plan.max_classes_per_week) if plan.max_classes_per_week else "Unlimited"
            rows.append((
                plan.name,
                f"{plan.duration_days} days",
                f"${plan.price:.2f}",
                "Yes" if plan.has_class_access else "No",
                max_cls,
                "Active" if plan.is_active else "Inactive",
            ))
        SetFormat.format_qtablewidget(self.plans_table, headers, rows)
        for row_idx, plan in enumerate(plans):
            item = self.plans_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, plan.id)

    def populate_memberships_table(self, memberships: list) -> None:
        headers = ["Member Code", "Member Name", "Plan", "Start Date", "End Date", "Status", "Days Left"]
        today = date.today()
        rows = []
        for ms in memberships:
            code      = ms.member.member_code if ms.member else ""
            name      = ms.member.full_name   if ms.member else ""
            plan_name = ms.plan.name          if ms.plan   else ""
            start     = ms.start_date.strftime("%Y-%m-%d") if ms.start_date else ""
            end       = ms.end_date.strftime("%Y-%m-%d")   if ms.end_date   else ""
            status    = ms.status.value.capitalize()
            if ms.end_date:
                days_left = (ms.end_date - today).days
                days_str  = str(days_left) if days_left >= 0 else "Expired"
            else:
                days_str = ""
            rows.append((code, name, plan_name, start, end, status, days_str))
        SetFormat.format_qtablewidget(self.memberships_table, headers, rows)
        for row_idx, ms in enumerate(memberships):
            item = self.memberships_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, ms.id)

    def populate_plan_combo(self, plans: list) -> None:
        self.combo_plan.clear()
        self.combo_plan.addItem("— Select plan —", None)
        for plan in plans:
            self.combo_plan.addItem(plan.name, plan.id)

    def set_plan_form_data(self, plan) -> None:
        self.input_plan_name.setText(plan.name)
        self.input_description.setText(plan.description or "")
        self.spin_duration_days.setValue(plan.duration_days)
        self.spin_price.setValue(plan.price)
        self.check_has_class_access.setChecked(plan.has_class_access)
        self.spin_max_classes.setValue(plan.max_classes_per_week or 0)
        self.check_is_active.setChecked(plan.is_active)

    def clear_plan_form(self) -> None:
        self.input_plan_name.clear()
        self.input_description.clear()
        self.spin_duration_days.setValue(30)
        self.spin_price.setValue(0.0)
        self.check_has_class_access.setChecked(True)
        self.spin_max_classes.setValue(0)
        self.check_is_active.setChecked(True)
        self.plans_table.clearSelection()

    def clear_assign_form(self) -> None:
        self.input_assign_search.clear()
        self.combo_plan.setCurrentIndex(0)
        self.date_start.setDate(QDate.currentDate())
        self.input_notes.clear()

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")
