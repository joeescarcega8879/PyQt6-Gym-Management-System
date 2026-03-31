import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize
from PyQt6.QtWidgets import QWidget
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon

class AttendanceView(QWidget):

    # Signals for communication with the presenter
    checkin_requested  = pyqtSignal()
    checkout_requested = pyqtSignal()
    date_changed       = pyqtSignal(object)   # emite QDate
    today_requested    = pyqtSignal()

    def __init__(self) -> None:
        super(AttendanceView, self).__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "attendance_view.ui")
        uic.loadUi(ui_path, self)

        # Buttons
        self.btn_checkin.clicked.connect(self.checkin_requested.emit)
        self.btn_checkout.clicked.connect(self.checkout_requested.emit)
        self.btn_today.clicked.connect(self.today_requested.emit)
        self.btn_close.clicked.connect(self.close)
        
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        # Date filter — start on today and emit on every change
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(
            lambda qdate: self.date_changed.emit(qdate)
        )

    def get_search_term(self) -> str | None:
        return self.input_search.text().strip() or None

    def get_selected_attendance_id(self) -> str | None:
        """Returns the UUID of the selected attendance record, stored in UserRole."""
        current_row = self.attendance_table.currentRow()
        if current_row < 0:
            return None
        first_cell = self.attendance_table.item(current_row, 0)
        return first_cell.data(Qt.ItemDataRole.UserRole) if first_cell else None

    def get_current_date(self) -> object:
        """Returns the currently selected date as a Python date object."""
        return self.date_filter.date().toPyDate()

    def populate_table(self, attendance_data: list) -> None:
        headers = ["Code", "Member Name", "Check-in", "Check-out", "Duration", "Notes"]

        rows = []
        for record in attendance_data:
            code      = record.member.member_code if record.member else ""
            name      = record.member.full_name   if record.member else ""
            check_in  = record.check_in_time.astimezone().strftime("%I:%M %p")
            check_out = record.check_out_time.astimezone().strftime("%I:%M %p") if record.check_out_time else ""

            if record.check_out_time:
                delta   = record.check_out_time - record.check_in_time
                minutes = int(delta.total_seconds() // 60)
                duration = f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{minutes}m"
            else:
                duration = ""

            rows.append((code, name, check_in, check_out, duration, record.notes or ""))

        SetFormat.format_qtablewidget(self.attendance_table, headers, rows)

        # Store the attendance UUID (hidden) in UserRole of column 0
        for row_idx, record in enumerate(attendance_data):
            item = self.attendance_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, record.id)

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    def clear_search(self) -> None:
        self.input_search.clear()