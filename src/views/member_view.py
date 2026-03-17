import os
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from PyQt6.QtWidgets import QWidget, QHeaderView
from datetime import datetime

from src.utils.set_format import SetFormat

class MemberView(QWidget):

    # Signals for communication with the presenter
    create_requested = pyqtSignal()
    update_requested = pyqtSignal()
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

        print(selected_items[0].text())
        print(member_uuid)

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

    def init_combo_boxes(self) -> None:
        # Initialize gender
        self.cbo_gender.addItem("Male", "male")
        self.cbo_gender.addItem("Female", "female")

        # Initialize is_active
        self.cbo_is_active.addItem("Active", True)
        self.cbo_is_active.addItem("Inactive", False)

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

        # Ensure the Code column is always visible with a reasonable minimum width.
        self.table_members.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_members.setColumnWidth(0, 130)

        # Attach the UUID (member.id) as hidden data on the first cell of each
        # row so get_selected_member_data() can retrieve it for update/delete
        # operations without exposing it in the visible table columns.
        for row_index, member in enumerate(members):
            first_cell = self.table_members.item(row_index, 0)
            if first_cell is not None:
                first_cell.setData(Qt.ItemDataRole.UserRole, member.id)

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