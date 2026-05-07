import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize
from PyQt6.QtWidgets import QWidget
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon

class PaymentView(QWidget):

    # Signals for communication with the presenter
    save_requested = pyqtSignal()
    new_requested = pyqtSignal()
    filter_requested = pyqtSignal()

    def __init__(self) -> None:
        super(PaymentView, self).__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "payment_view.ui")
        uic.loadUi(ui_path, self)

        # Buttons
        self.btn_save.clicked.connect(self.save_requested.emit)
        self.btn_new.clicked.connect(self.new_requested.emit)
        self.btn_filter.clicked.connect(self.filter_requested.emit)
        self.btn_clear_filters.clicked.connect(self._clear_filters)
        self.btn_close.clicked.connect(self.close)

        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        # Date filters
        self.date_to.setDate(QDate.currentDate())

    def _clear_filters(self) -> None:
        self.combo_status.setCurrentIndex(0)
        self.combo_filter_method.setCurrentIndex(0)
        self.date_from.setDate(QDate(2026, 1, 1))
        self.date_to.setDate(QDate.currentDate())
        self.filter_requested.emit()

    # --- Getters ---

    def get_search_term(self) -> str | None:
        return self.input_search.text().strip() or None

    def get_amount(self) -> float:
        return self.spin_amount.value()

    def get_payment_method(self) -> str:
        text = self.combo_method.currentText().lower()
        method_map = {"cash": "cash", "card": "card", "transfer": "transfer"}
        return method_map.get(text, "other")

    def get_selected_payment_id(self) -> str | None:
        current_row = self.payments_table.currentRow()
        if current_row < 0:
            return None
        first_cell = self.payments_table.item(current_row, 0)
        return first_cell.data(Qt.ItemDataRole.UserRole) if first_cell else None

    def get_filter_status(self) -> str | None:
        text = self.combo_status.currentText().lower()
        if text == "all":
            return None
        return text

    def get_filter_method(self) -> str | None:
        text = self.combo_filter_method.currentText().lower()
        if text == "all":
            return None
        return text

    def get_date_from(self) -> object | None:
        d = self.date_from.date().toPyDate()
        if d.year <= 2026 and d.month == 1 and d.day == 1:
            return None
        return d

    def get_date_to(self) -> object:
        return self.date_to.date().toPyDate()

    # --- Setters ---

    def populate_table(self, payment_data: list) -> None:
        headers = ["Code", "Member Name", "Amount", "Method", "Date", "Status", "Notes"]

        rows = []
        for record in payment_data:
            code = record.member.member_code if record.member else ""
            name = record.member.full_name if record.member else ""
            amount = f"${record.amount:.2f}"
            method = record.payment_method.value.capitalize()
            date_str = record.payment_date.strftime("%Y-%m-%d %I:%M %p")
            status = record.status.value.capitalize()
            notes = record.notes or ""

            rows.append((code, name, amount, method, date_str, status, notes))

        SetFormat.format_qtablewidget(self.payments_table, headers, rows)

        for row_idx, record in enumerate(payment_data):
            item = self.payments_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, record.id)

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    def clear_form(self) -> None:
        self.input_search.clear()
        self.spin_amount.setValue(0.0)
        self.combo_method.setCurrentIndex(0)
