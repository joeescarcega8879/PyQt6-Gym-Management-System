import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize
from PyQt6.QtWidgets import QWidget, QMessageBox
from src.utils.set_format import SetFormat
from src.assets.resources_rc import get_icon


class InstructorView(QWidget):

    # Signals for communication with the presenter
    create_requested = pyqtSignal()
    update_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    show_inactive_requested = pyqtSignal(bool)
    search_requested = pyqtSignal(str)
    clear_action_requested = pyqtSignal()
    no_selection_error = pyqtSignal()

    def __init__(self) -> None:
        super(InstructorView, self).__init__()

        # Initialize components
        self.initialize_components()

    def initialize_components(self) -> None:
        # Load ui path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "instructor_view.ui")
        # Load ui
        uic.loadUi(ui_path, self)

        self.btn_save.clicked.connect(self.create_requested.emit)
        self.btn_update.clicked.connect(self.show_message_update_confirmation)
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        self.btn_clear.clicked.connect(self.clear_action_requested.emit)

        self.btn_search.clicked.connect(lambda: self.on_search_text_changed(self.input_search.text()))
        self.input_search.returnPressed.connect(lambda: self.on_search_text_changed(self.input_search.text()))
        self.check_show_inactives.stateChanged.connect(lambda state: self.show_inactive_requested.emit(state == Qt.CheckState.Checked))

        self.btn_close.clicked.connect(self.close)
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        self.init_combo_boxes()

        self.date_hire.setMinimumDate(QDate(1900, 1, 1))
        self.date_hire.setMaximumDate(QDate.currentDate())

    def get_form_data(self) -> dict | None:
        return {
            "first_name": self.input_first_name.text(),
            "last_name": self.input_last_name.text(),
            "email": self.input_email.text(),
            "phone": self.input_phone.text(),
            "specialties": self._parse_specialties(self.input_specialties.text()),
            "certifications": self.input_certifications.text(),
            "hire_date": (
                self.date_hire.date().toPyDate()
                if self.date_hire.date() != self.date_hire.minimumDate()
                else None
            ),
            "is_active": self.cbo_is_active.currentData(),
        }

    def get_selected_instructor_data(self) -> dict | None:
        selected_items = self.table_instructors.selectedItems()
        if not selected_items:
            return None

        # The UUID is stored as UserRole data on the first cell (column 0).
        first_cell = self.table_instructors.item(self.table_instructors.currentRow(), 0)
        instructor_uuid = first_cell.data(Qt.ItemDataRole.UserRole) if first_cell else None

        return {
            "id": instructor_uuid,
            "first_name": selected_items[0].text(),
            "last_name": selected_items[1].text(),
            "email": selected_items[2].text(),
            "phone": selected_items[3].text(),
            "specialties": selected_items[4].text(),
            "certifications": selected_items[5].text(),
            "hire_date": selected_items[6].text(),
            "is_active": selected_items[7].text() == "Active",
        }

    def set_form_data(self, data: dict) -> None:
        self.input_first_name.setText(data.get("first_name", ""))
        self.input_last_name.setText(data.get("last_name", ""))
        self.input_email.setText(data.get("email", ""))
        self.input_phone.setText(data.get("phone", ""))
        self.input_certifications.setText(data.get("certifications", ""))

        specialties = data.get("specialties", "")
        self.input_specialties.setText(
            ", ".join(specialties) if isinstance(specialties, list) else specialties
        )

        hire_date = data.get("hire_date")
        if hire_date:
            qDate = QDate.fromString(hire_date, "yyyy-MM-dd")
            if qDate.isValid():
                self.date_hire.setDate(qDate)

        self.cbo_is_active.setCurrentText("Active" if data.get("is_active", True) else "Inactive")

    def get_selected_search_option(self) -> str:
        return self.cbo_search_options.currentData()

    def on_search_text_changed(self, text: str) -> None:
        self.search_requested.emit(text)

    def init_combo_boxes(self) -> None:
        # Initialize is_active
        self.cbo_is_active.addItem("Active", True)
        self.cbo_is_active.addItem("Inactive", False)

        # Initialize search options
        self.cbo_search_options.addItem("First Name", "first_name")
        self.cbo_search_options.addItem("Last Name", "last_name")
        self.cbo_search_options.addItem("Email", "email")

    def populate_table(self, instructors: list) -> None:
        headers = ["First Name", "Last Name", "Email", "Phone", "Specialties", "Certifications", "Hire Date", "Status"]
        rows = [
            (
                i.first_name,
                i.last_name,
                i.email or "",
                i.phone or "",
                ", ".join(i.specialties) if i.specialties else "",
                i.certifications or "",
                str(i.hire_date) if i.hire_date else "",
                "Active" if i.is_active else "Inactive",
            )
            for i in instructors
        ]
        SetFormat.format_qtablewidget(self.table_instructors, headers, rows)

        # Store the UUID (not shown as text) on column 0 of each row for later retrieval
        for row, i in enumerate(instructors):
            self.table_instructors.item(row, 0).setData(Qt.ItemDataRole.UserRole, i.id)

    def clear_form(self) -> None:
        self.input_first_name.clear()
        self.input_last_name.clear()
        self.input_phone.clear()
        self.input_email.clear()
        self.input_specialties.clear()
        self.input_certifications.clear()
        self.date_hire.setDate(self.date_hire.minimumDate())
        self.cbo_is_active.setCurrentIndex(0)

    def clear_search(self) -> None:
        self.input_search.clear()
        self.cbo_search_options.setCurrentIndex(0)

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def show_message_update_confirmation(self) -> None:

        if not self.get_selected_instructor_data():
            self.no_selection_error.emit()
            return

        reply = QMessageBox.question(
            self,
            "Confirm Update",
            "Are you sure you want to update this instructor's information?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.update_requested.emit()

    @staticmethod
    def _parse_specialties(text: str) -> list:
        return [s.strip() for s in text.split(",") if s.strip()]
