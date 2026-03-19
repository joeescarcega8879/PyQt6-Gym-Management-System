import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from PyQt6.QtWidgets import QWidget, QMessageBox, QHeaderView
from src.utils.set_format import SetFormat

class MemberView(QWidget):

    # Signals for communication with the presenter
    create_requested = pyqtSignal()
    update_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    search_requested = pyqtSignal(str)

    def __init__(self):
        super(MemberView, self).__init__()

        # Initialize components
        self.initialize_components()

    def initialize_components(self):
        # Load ui path
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "member_view.ui")
        # Load ui
        uic.loadUi(ui_path, self)

        self.btn_save.clicked.connect(self.create_requested.emit)
        self.btn_update.clicked.connect(self.update_requested.emit)
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        self.btn_search.clicked.connect(lambda: self.on_search_text_changed(self.input_search.text()))
        self.input_search.returnPressed.connect(lambda: self.on_search_text_changed(self.input_search.text()))
        self.btn_close.clicked.connect(self.close)

        self.init_combo_boxes()
        

    def get_form_data(self) -> dict | None:
        return{
            "first_name": self.input_first_name.text(),
            "last_name": self.input_last_name.text(),
            "email": self.input_email.text(),
            "phone": self.input_phone.text(),
            "date_of_birth": self.date_birthday.date().toPyDate(),
            "gender": self.cbo_gender.currentData(),
            "address": self.input_address.text(),
            "emergency_contact_name": self.input_emergency_name.text(),
            "emergency_contact_phone": self.input_emergency_phone.text(),
            "notes": self.input_notes.text(),
            "is_active": self.cbo_is_active.currentData(),
        }
    
    def get_selected_member_id(self) -> str | None:
        selected_items = self.table_members.selectedItems()
        if not selected_items:
            return None
        
        # Assuming the first column contains the member code
        return selected_items[0].text()
    
    def get_selected_member_data(self) -> dict | None:
        selected_items = self.table_members.selectedItems()
        if not selected_items:
            return None

        # The UUID is stored as UserRole data on the first cell (column 0).
        # The visible text of column 0 is the member_code, not the UUID.
        first_cell = self.table_members.item(self.table_members.currentRow(), 0)
        member_uuid = first_cell.data(Qt.ItemDataRole.UserRole) if first_cell else None

        return {
            "id": member_uuid,
            "member_code": selected_items[0].text(),
            "first_name": selected_items[1].text(),
            "last_name": selected_items[2].text(),
            "email": selected_items[3].text(),
            "phone": selected_items[4].text(),
            "date_of_birth": selected_items[5].text(),
            "gender": selected_items[6].text(),
            "address": selected_items[7].text(),
            "emergency_contact_name": selected_items[8].text(),
            "emergency_contact_phone": selected_items[9].text(),
            "notes": selected_items[10].text(),
            "is_active": selected_items[11].text() == "Active"
        }

    def set_form_data(self, data: dict) -> None:

        self.input_first_name.setText(data.get("first_name", ""))
        self.input_last_name.setText(data.get("last_name", ""))
        self.input_email.setText(data.get("email", ""))
        self.input_phone.setText(data.get("phone", ""))
        self.input_address.setText(data.get("address", ""))
        self.input_emergency_name.setText(data.get("emergency_contact_name", ""))
        self.input_emergency_phone.setText(data.get("emergency_contact_phone", ""))
        self.input_notes.setText(data.get("notes", ""))
        date_of_birth = data.get("date_of_birth")

        if date_of_birth:
            qDate = QDate.fromString(date_of_birth, "yyyy-MM-dd")
            if qDate.isValid():
                self.date_birthday.setDate(qDate)
        
        self.cbo_gender.setCurrentText(data.get("gender", ""))
        self.cbo_is_active.setCurrentText("Active" if data.get("is_active", True) else "Inactive")

    def on_search_text_changed(self, text: str) -> None:
        self.search_requested.emit(text)

    def init_combo_boxes(self) -> None:
        # Initialize gender
        self.cbo_gender.addItem("Male", "male")
        self.cbo_gender.addItem("Female", "female")

        # Initialize is_active
        self.cbo_is_active.addItem("Active", True)
        self.cbo_is_active.addItem("Inactive", False)

        # Initialize search options
        self.cbo_search_options.addItem("First Name", "first_name")
        self.cbo_search_options.addItem("Last Name", "last_name")
        self.cbo_search_options.addItem("Email", "email")
        self.cbo_search_options.addItem("By Member Code", "member_code")

    def populate_table(self, members: list) -> None:

        headers = ["Code", "First Name", "Last Name", "Email", "Phone","Date of Birth", "Gender", "Address", "Emergency Contact Name", "Emergency Contact Phone", "Notes", "Status"]
        rows = [
            (
                m.member_code,
                m.first_name,
                m.last_name,
                m.email or "",
                m.phone or "",
                str(m.date_of_birth) if m.date_of_birth else "",
                m.gender.value if m.gender else "",
                m.address or "",
                m.emergency_contact_name or "",
                m.emergency_contact_phone or "",
                m.notes or "",
                "Active" if m.is_active else "Inactive",
            )
            for m in members
        ]
        SetFormat.format_qtablewidget(self.table_members, headers, rows)

        # Store the UUID as hidden UserRole data on column 0 of each row so that
        # get_selected_member_data() can return the real UUID for update/delete.
        for row_index, member in enumerate(members):
            cell = self.table_members.item(row_index, 0)
            if cell:
                cell.setData(Qt.ItemDataRole.UserRole, str(member.id))

        # SetFormat uses ResizeToContents which collapses the Code column.
        # Override it to a fixed readable width.
        self.table_members.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.table_members.setColumnWidth(0, 130)

    def clear_form(self) -> None:
        self.input_first_name.clear()
        self.input_last_name.clear()
        self.input_phone.clear()
        self.input_address.clear()
        self.date_birthday.setDate(self.date_birthday.minimumDate())
        self.input_email.clear()
        self.input_emergency_name.clear()
        self.input_emergency_phone.clear()
        self.input_notes.clear()
        self.cbo_gender.setCurrentIndex(0)
        self.cbo_is_active.setCurrentIndex(0)

    def show_error(self, message: str) -> None:
        """Displays a critical error dialog to the user."""
        QMessageBox.critical(self, "Error", message or "An unexpected error occurred.")