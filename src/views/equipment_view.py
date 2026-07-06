import os
from datetime import date
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize
from PyQt6.QtWidgets import QWidget, QMessageBox
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon


class EquipmentView(QWidget):

    # Tab 1 — Equipment signals
    save_requested           = pyqtSignal()
    new_requested             = pyqtSignal()
    cancel_requested         = pyqtSignal()
    show_inactive_requested  = pyqtSignal(bool)
    search_requested         = pyqtSignal(str)
    clear_action_requested   = pyqtSignal()
    equipment_selected       = pyqtSignal()

    # Tab 2 — Maintenance signals
    filter_maintenance_requested = pyqtSignal()
    log_maintenance_requested    = pyqtSignal()

    def __init__(self) -> None:
        super(EquipmentView, self).__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "equipment_view.ui")
        uic.loadUi(ui_path, self)

        # Equipment tab
        self.btn_save_equipment.clicked.connect(self.save_requested.emit)
        self.btn_new_equipment.clicked.connect(self.new_requested.emit)
        self.btn_cancel_equipment.clicked.connect(self.cancel_requested.emit)
        self.equipment_table.itemSelectionChanged.connect(self.equipment_selected.emit)

        self.btn_search.clicked.connect(lambda: self.search_requested.emit(self.input_search.text()))
        self.input_search.returnPressed.connect(lambda: self.search_requested.emit(self.input_search.text()))
        self.check_show_inactives.stateChanged.connect(lambda state: self.show_inactive_requested.emit(state == Qt.CheckState.Checked))
        self.btn_clear.clicked.connect(self._handle_clear_search)

        # Maintenance tab
        self.btn_filter_maintenance.clicked.connect(self.filter_maintenance_requested.emit)
        self.btn_clear_maintenance_filters.clicked.connect(self._handle_clear_maintenance_filters)
        self.btn_log_maintenance.clicked.connect(self.log_maintenance_requested.emit)

        # Close
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        self.init_combo_boxes()

        # Date bounds/defaults
        for date_edit in (self.date_purchase, self.date_maintenance, self.date_next_maintenance,
                          self.date_maint_from, self.date_maint_to):
            date_edit.setMinimumDate(QDate(1900, 1, 1))
        self.date_maintenance.setDate(QDate.currentDate())
        self.date_maint_to.setDate(QDate.currentDate())

    def _handle_clear_search(self) -> None:
        self.input_search.clear()
        self.cbo_search_options.setCurrentIndex(0)
        self.clear_action_requested.emit()

    def _handle_clear_maintenance_filters(self) -> None:
        self.combo_filter_equipment.setCurrentIndex(0)
        self.date_maint_from.setDate(QDate(2026, 1, 1))
        self.date_maint_to.setDate(QDate.currentDate())
        self.combo_filter_type.setCurrentIndex(0)
        self.filter_maintenance_requested.emit()

    def init_combo_boxes(self) -> None:
        # Condition
        self.cbo_condition.addItem("Excellent", "excellent")
        self.cbo_condition.addItem("Good", "good")
        self.cbo_condition.addItem("Fair", "fair")
        self.cbo_condition.addItem("Poor", "poor")
        self.cbo_condition.addItem("Out of Service", "out_of_service")

        # Is Active
        self.cbo_is_active.addItem("Active", True)
        self.cbo_is_active.addItem("Inactive", False)

        # Search options
        self.cbo_search_options.addItem("Name", "name")
        self.cbo_search_options.addItem("Category", "category")
        self.cbo_search_options.addItem("Brand", "brand")

        # Maintenance type (filter + log)
        self.combo_filter_type.addItem("All", None)
        self.combo_filter_type.addItem("Preventive", "preventive")
        self.combo_filter_type.addItem("Corrective", "corrective")
        self.combo_filter_type.addItem("Inspection", "inspection")

        self.combo_log_type.addItem("Preventive", "preventive")
        self.combo_log_type.addItem("Corrective", "corrective")
        self.combo_log_type.addItem("Inspection", "inspection")

    # ------------------------------------------------------------------ #
    # Getters — Equipment tab
    # ------------------------------------------------------------------ #

    def get_form_data(self) -> dict:
        return {
            "name": self.input_name.text(),
            "category": self.input_category.text(),
            "brand": self.input_brand.text(),
            "model": self.input_model.text(),
            "serial_number": self.input_serial_number.text(),
            "purchase_date": (
                self.date_purchase.date().toPyDate()
                if self.date_purchase.date() != self.date_purchase.minimumDate()
                else None
            ),
            "purchase_price": self.spin_purchase_price.value() or None,
            "condition": self.cbo_condition.currentData(),
            "location": self.input_location.text(),
            "notes": self.input_notes.text(),
            "is_active": self.cbo_is_active.currentData(),
        }

    def get_selected_equipment_id(self) -> str | None:
        current_row = self.equipment_table.currentRow()
        if current_row < 0:
            return None
        item = self.equipment_table.item(current_row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def get_selected_search_option(self) -> str:
        return self.cbo_search_options.currentData()

    # ------------------------------------------------------------------ #
    # Getters — Maintenance tab
    # ------------------------------------------------------------------ #

    def get_filter_equipment_id(self) -> str | None:
        return self.combo_filter_equipment.currentData()

    def get_filter_date_from(self) -> date | None:
        d = self.date_maint_from.date().toPyDate()
        if d.year == 2026 and d.month == 1 and d.day == 1:
            return None
        return d

    def get_filter_date_to(self) -> date:
        return self.date_maint_to.date().toPyDate()

    def get_filter_maintenance_type(self) -> str | None:
        return self.combo_filter_type.currentData()

    def get_log_equipment_id(self) -> str | None:
        return self.combo_log_equipment.currentData()

    def get_log_maintenance_date(self) -> date:
        return self.date_maintenance.date().toPyDate()

    def get_log_maintenance_type(self) -> str:
        return self.combo_log_type.currentData()

    def get_log_description(self) -> str | None:
        return self.input_description.text().strip() or None

    def get_log_cost(self) -> float | None:
        return self.spin_cost.value() or None

    def get_log_performed_by(self) -> str | None:
        return self.input_performed_by.text().strip() or None

    def get_log_next_maintenance_date(self) -> date | None:
        d = self.date_next_maintenance.date()
        return d.toPyDate() if d != self.date_next_maintenance.minimumDate() else None

    # ------------------------------------------------------------------ #
    # Setters / population
    # ------------------------------------------------------------------ #

    def set_form_data(self, data: dict) -> None:
        self.input_name.setText(data.get("name", ""))
        self.input_category.setText(data.get("category") or "")
        self.input_brand.setText(data.get("brand") or "")
        self.input_model.setText(data.get("model") or "")
        self.input_serial_number.setText(data.get("serial_number") or "")
        self.input_location.setText(data.get("location") or "")
        self.input_notes.setText(data.get("notes") or "")

        purchase_date = data.get("purchase_date")
        if purchase_date:
            qDate = QDate.fromString(purchase_date, "yyyy-MM-dd")
            if qDate.isValid():
                self.date_purchase.setDate(qDate)

        self.spin_purchase_price.setValue(data.get("purchase_price") or 0.0)

        index = self.cbo_condition.findData(data.get("condition", "good"))
        if index != -1:
            self.cbo_condition.setCurrentIndex(index)

        self.cbo_is_active.setCurrentText("Active" if data.get("is_active", True) else "Inactive")

    def clear_form(self) -> None:
        self.input_name.clear()
        self.input_category.clear()
        self.input_brand.clear()
        self.input_model.clear()
        self.input_serial_number.clear()
        self.input_location.clear()
        self.input_notes.clear()
        self.date_purchase.setDate(self.date_purchase.minimumDate())
        self.spin_purchase_price.setValue(0.0)
        self.cbo_condition.setCurrentIndex(1)  # Good
        self.cbo_is_active.setCurrentIndex(0)  # Active
        self.equipment_table.clearSelection()

    def clear_log_form(self) -> None:
        self.combo_log_equipment.setCurrentIndex(0)
        self.date_maintenance.setDate(QDate.currentDate())
        self.combo_log_type.setCurrentIndex(0)
        self.input_description.clear()
        self.spin_cost.setValue(0.0)
        self.input_performed_by.clear()
        self.date_next_maintenance.setDate(self.date_next_maintenance.minimumDate())

    def populate_table(self, equipment: list) -> None:
        headers = ["Name", "Category", "Brand", "Model", "Serial Number", "Condition", "Location", "Status"]
        rows = [
            (
                e.name,
                e.category or "",
                e.brand or "",
                e.model or "",
                e.serial_number or "",
                e.condition.value.replace("_", " ").capitalize(),
                e.location or "",
                "Active" if e.is_active else "Inactive",
            )
            for e in equipment
        ]
        SetFormat.format_qtablewidget(self.equipment_table, headers, rows)
        for row, e in enumerate(equipment):
            self.equipment_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, e.id)

    def populate_maintenance_table(self, records: list) -> None:
        headers = ["Equipment", "Date", "Type", "Description", "Cost", "Performed By", "Next Maintenance"]
        rows = []
        for r in records:
            equipment_name = r.equipment.name if r.equipment else ""
            cost_str = f"${r.cost:.2f}" if r.cost is not None else ""
            next_maint = r.next_maintenance_date.strftime("%Y-%m-%d") if r.next_maintenance_date else ""
            rows.append((
                equipment_name,
                r.maintenance_date.strftime("%Y-%m-%d") if r.maintenance_date else "",
                r.maintenance_type.value.capitalize(),
                r.description or "",
                cost_str,
                r.performed_by or "",
                next_maint,
            ))
        SetFormat.format_qtablewidget(self.maintenance_table, headers, rows)

    def populate_equipment_combos(self, equipment: list) -> None:
        """Populates both the maintenance-filter and log-maintenance equipment combo boxes."""
        for combo, include_all in ((self.combo_filter_equipment, True), (self.combo_log_equipment, False)):
            combo.clear()
            if include_all:
                combo.addItem("All Equipment", None)
            else:
                combo.addItem("— Select equipment —", None)
            for e in equipment:
                combo.addItem(e.name, e.id)

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)
