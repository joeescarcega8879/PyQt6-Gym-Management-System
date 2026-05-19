import os
from datetime import date

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, QDate, Qt, QSize, QTime
from PyQt6.QtWidgets import QWidget

from src.assets.resources_rc import get_icon
from src.models.enums import DifficultyLevel
from src.utils.set_format import SetFormat


# Maps DifficultyLevel enum values to combo box indices
_DIFFICULTY_INDEX = {
    DifficultyLevel.ALL:          0,
    DifficultyLevel.BEGINNER:     1,
    DifficultyLevel.INTERMEDIATE: 2,
    DifficultyLevel.ADVANCED:     3,
}
_INDEX_DIFFICULTY = {v: k for k, v in _DIFFICULTY_INDEX.items()}

# Days of week: combo index → (display, day_of_week int)
_DAY_LABELS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


class ClassView(QWidget):

    # ------------------------------------------------------------------ #
    # Tab 1 — Classes signals
    # ------------------------------------------------------------------ #
    save_class_requested        = pyqtSignal()
    new_class_requested         = pyqtSignal()
    cancel_class_requested      = pyqtSignal()
    toggle_class_status_requested = pyqtSignal()
    class_selected              = pyqtSignal()

    # ------------------------------------------------------------------ #
    # Tab 2 — Schedules signals
    # ------------------------------------------------------------------ #
    filter_schedules_requested       = pyqtSignal()
    clear_schedule_filters_requested = pyqtSignal()
    save_schedule_requested          = pyqtSignal()
    new_schedule_requested           = pyqtSignal()
    toggle_schedule_status_requested = pyqtSignal()
    schedule_selected                = pyqtSignal()

    # ------------------------------------------------------------------ #
    # Tab 3 — Enrollments signals
    # ------------------------------------------------------------------ #
    filter_enrollments_requested       = pyqtSignal()
    clear_enrollment_filters_requested = pyqtSignal()
    enroll_requested                   = pyqtSignal()
    mark_attended_requested            = pyqtSignal()
    mark_absent_requested              = pyqtSignal()
    cancel_enrollment_requested        = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "class_view.ui")
        uic.loadUi(ui_path, self)

        # Close button icon
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        # ---- Tab 1 — Classes ----
        self.btn_save_class.clicked.connect(self.save_class_requested.emit)
        self.btn_new_class.clicked.connect(self.new_class_requested.emit)
        self.btn_cancel_class.clicked.connect(self.cancel_class_requested.emit)
        self.btn_toggle_class_status.clicked.connect(self.toggle_class_status_requested.emit)
        self.classes_table.itemSelectionChanged.connect(self.class_selected.emit)

        # ---- Tab 2 — Schedules ----
        self.btn_filter_schedules.clicked.connect(self.filter_schedules_requested.emit)
        self.btn_clear_schedule_filters.clicked.connect(self.clear_schedule_filters_requested.emit)
        self.btn_save_schedule.clicked.connect(self.save_schedule_requested.emit)
        self.btn_new_schedule.clicked.connect(self.new_schedule_requested.emit)
        self.btn_toggle_schedule_status.clicked.connect(self.toggle_schedule_status_requested.emit)
        self.schedules_table.itemSelectionChanged.connect(self.schedule_selected.emit)

        # ---- Tab 3 — Enrollments ----
        self.btn_filter_enrollments.clicked.connect(self.filter_enrollments_requested.emit)
        self.btn_clear_enrollment_filters.clicked.connect(self.clear_enrollment_filters_requested.emit)
        self.btn_enroll.clicked.connect(self.enroll_requested.emit)
        self.btn_mark_attended.clicked.connect(self.mark_attended_requested.emit)
        self.btn_mark_absent.clicked.connect(self.mark_absent_requested.emit)
        self.btn_cancel_enrollment.clicked.connect(self.cancel_enrollment_requested.emit)

        # Default dates
        today = QDate.currentDate()
        self.date_enroll_class.setDate(today)
        self.date_enroll_filter.setDate(today)

    # ================================================================== #
    # Shared
    # ================================================================== #

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    # ================================================================== #
    # Tab 1 — Classes getters / setters
    # ================================================================== #

    def get_class_name(self) -> str:
        return self.input_class_name.text().strip()

    def get_class_description(self) -> str | None:
        text = self.input_class_description.text().strip()
        return text or None

    def get_duration_minutes(self) -> int:
        return self.spin_duration_minutes.value()

    def get_max_capacity(self) -> int | None:
        value = self.spin_max_capacity.value()
        return None if value == 0 else value

    def get_difficulty_level(self) -> DifficultyLevel:
        return _INDEX_DIFFICULTY.get(self.combo_difficulty.currentIndex(), DifficultyLevel.ALL)

    def get_class_is_active(self) -> bool:
        return self.check_class_active.isChecked()

    def get_selected_class_id(self) -> str | None:
        current_row = self.classes_table.currentRow()
        if current_row < 0:
            return None
        item = self.classes_table.item(current_row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def set_class_form_data(self, data: dict) -> None:
        """Populates the class form fields from a dict."""
        self.input_class_name.setText(data.get("name", ""))
        self.input_class_description.setText(data.get("description") or "")
        self.spin_duration_minutes.setValue(data.get("duration_minutes", 60))
        capacity = data.get("max_capacity")
        self.spin_max_capacity.setValue(capacity if capacity is not None else 0)
        difficulty = data.get("difficulty_level", DifficultyLevel.ALL)
        self.combo_difficulty.setCurrentIndex(_DIFFICULTY_INDEX.get(difficulty, 0))
        self.check_class_active.setChecked(data.get("is_active", True))

    def clear_class_form(self) -> None:
        self.input_class_name.clear()
        self.input_class_description.clear()
        self.spin_duration_minutes.setValue(60)
        self.spin_max_capacity.setValue(0)
        self.combo_difficulty.setCurrentIndex(0)
        self.check_class_active.setChecked(True)

    def populate_classes_table(self, classes: list) -> None:
        headers = ["Name", "Duration", "Capacity", "Difficulty", "Status"]
        rows = []
        for c in classes:
            capacity = str(c.max_capacity) if c.max_capacity is not None else "Unlimited"
            rows.append([
                c.name,
                f"{c.duration_minutes} min",
                capacity,
                c.difficulty_level.value.capitalize(),
                "Active" if c.is_active else "Inactive",
            ])
        SetFormat.format_qtablewidget(self.classes_table, headers, rows)
        # Store UUID in UserRole of column 0
        for row_idx, c in enumerate(classes):
            item = self.classes_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, c.id)

    # ================================================================== #
    # Tab 2 — Schedules getters / setters
    # ================================================================== #

    def get_schedule_filter_class_id(self) -> str | None:
        return self.combo_filter_class.currentData()

    def get_schedule_filter_day(self) -> int | None:
        """Returns day_of_week (0–6) or None if 'All Days' is selected (index 0)."""
        idx = self.combo_filter_day.currentIndex()
        return None if idx == 0 else idx - 1  # index 1 = Sunday = 0

    def get_show_inactive_schedules(self) -> bool:
        return self.check_show_inactive_schedules.isChecked()

    def get_sched_class_id(self) -> str | None:
        return self.combo_sched_class.currentData()

    def get_sched_day_of_week(self) -> int:
        """Returns day_of_week integer (0=Sunday, 6=Saturday)."""
        return self.combo_sched_day.currentIndex()

    def get_sched_start_time(self) -> str:
        return self.time_sched_start.time().toString("HH:mm")

    def get_sched_end_time(self) -> str:
        return self.time_sched_end.time().toString("HH:mm")

    def get_sched_room(self) -> str | None:
        text = self.input_sched_room.text().strip()
        return text or None

    def get_selected_schedule_id(self) -> str | None:
        current_row = self.schedules_table.currentRow()
        if current_row < 0:
            return None
        item = self.schedules_table.item(current_row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def set_schedule_form_data(self, data: dict) -> None:
        """Populates the schedule form from a dict."""
        # Set class combo by stored ID
        class_id = data.get("class_id", "")
        for i in range(self.combo_sched_class.count()):
            if self.combo_sched_class.itemData(i) == class_id:
                self.combo_sched_class.setCurrentIndex(i)
                break
        self.combo_sched_day.setCurrentIndex(data.get("day_of_week", 1))
        start = data.get("start_time", "08:00")
        end   = data.get("end_time",   "09:00")
        self.time_sched_start.setTime(QTime.fromString(str(start)[:5], "HH:mm"))
        self.time_sched_end.setTime(QTime.fromString(str(end)[:5], "HH:mm"))
        self.input_sched_room.setText(data.get("room") or "")

    def clear_schedule_form(self) -> None:
        if self.combo_sched_class.count():
            self.combo_sched_class.setCurrentIndex(0)
        self.combo_sched_day.setCurrentIndex(1)  # Monday default
        self.time_sched_start.setTime(QTime(8, 0))
        self.time_sched_end.setTime(QTime(9, 0))
        self.input_sched_room.clear()

    def populate_schedules_table(self, schedules: list) -> None:
        headers = ["Class", "Day", "Start", "End", "Room", "Status"]
        rows = []
        for s in schedules:
            class_name = s.class_info.name if s.class_info else ""
            day_name   = _DAY_LABELS[s.day_of_week] if 0 <= s.day_of_week <= 6 else str(s.day_of_week)
            rows.append([
                class_name,
                day_name,
                str(s.start_time)[:5],
                str(s.end_time)[:5],
                s.room or "",
                "Active" if s.is_active else "Inactive",
            ])
        SetFormat.format_qtablewidget(self.schedules_table, headers, rows)
        for row_idx, s in enumerate(schedules):
            item = self.schedules_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, s.id)

    def populate_class_combos(self, classes: list) -> None:
        """Populates class combo boxes (filter + form) with active classes."""
        # Filter combo: first item is "All Classes"
        self.combo_filter_class.clear()
        self.combo_filter_class.addItem("All Classes", None)
        for c in classes:
            self.combo_filter_class.addItem(c.name, c.id)

        # Schedule form combo
        self.combo_sched_class.clear()
        for c in classes:
            self.combo_sched_class.addItem(c.name, c.id)

    # ================================================================== #
    # Tab 3 — Enrollments getters / setters
    # ================================================================== #

    def get_enrollment_search_term(self) -> str | None:
        text = self.input_enroll_search.text().strip()
        return text or None

    def get_enrollment_status_filter(self) -> str | None:
        """Returns the status value string, or None if 'All' is selected."""
        text = self.combo_enroll_status.currentText()
        return None if text == "All" else text.lower()

    def get_enrollment_date_filter(self) -> date | None:
        """Returns the selected date or None if the special 'Any date' value is shown."""
        q = self.date_enroll_filter.date()
        # QDateEdit returns minimum date when cleared; treat as None
        if q == self.date_enroll_filter.minimumDate():
            return None
        return q.toPyDate()

    def get_enroll_member_search(self) -> str | None:
        text = self.input_enroll_member_search.text().strip()
        return text or None

    def get_enroll_schedule_id(self) -> str | None:
        return self.combo_enroll_schedule.currentData()

    def get_enroll_class_date(self) -> date:
        return self.date_enroll_class.date().toPyDate()

    def get_enroll_notes(self) -> str | None:
        text = self.input_enroll_notes.text().strip()
        return text or None

    def get_selected_enrollment_id(self) -> str | None:
        current_row = self.enrollments_table.currentRow()
        if current_row < 0:
            return None
        item = self.enrollments_table.item(current_row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def clear_enrollment_filters(self) -> None:
        self.input_enroll_search.clear()
        self.combo_enroll_status.setCurrentIndex(0)
        self.date_enroll_filter.setDate(QDate.currentDate())

    def populate_enrollments_table(self, enrollments: list) -> None:
        headers = ["Member Code", "Member Name", "Class", "Date", "Start", "Room", "Status"]
        rows = []
        for e in enrollments:
            member_code = e.member.member_code if e.member else ""
            member_name = e.member.full_name if e.member else ""
            class_name  = e.schedule.class_info.name if (e.schedule and e.schedule.class_info) else ""
            start_time  = str(e.schedule.start_time)[:5] if e.schedule else ""
            room        = e.schedule.room if e.schedule else ""
            rows.append([
                member_code,
                member_name,
                class_name,
                e.class_date.strftime("%Y-%m-%d") if e.class_date else "",
                start_time,
                room or "",
                e.status.value.capitalize(),
            ])
        SetFormat.format_qtablewidget(self.enrollments_table, headers, rows)
        for row_idx, e in enumerate(enrollments):
            item = self.enrollments_table.item(row_idx, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, e.id)

    def populate_schedule_combo_for_enrollment(self, schedules: list) -> None:
        """Populates the schedule combo in the enroll form with active schedules."""
        self.combo_enroll_schedule.clear()
        for s in schedules:
            class_name = s.class_info.name if s.class_info else "?"
            day_name   = _DAY_LABELS[s.day_of_week] if 0 <= s.day_of_week <= 6 else ""
            label = f"{class_name} — {day_name} {str(s.start_time)[:5]}"
            self.combo_enroll_schedule.addItem(label, s.id)
