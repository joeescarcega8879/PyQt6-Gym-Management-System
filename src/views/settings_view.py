import os
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QWidget, QListWidgetItem

from src.assets.resources_rc import get_icon


class SettingsView(QWidget):

    # ------------------------------------------------------------------ #
    # Signals
    # ------------------------------------------------------------------ #
    save_settings_requested   = pyqtSignal()
    discard_requested         = pyqtSignal()
    theme_selected            = pyqtSignal(str)   # emits theme key on selection change

    def __init__(self) -> None:
        super().__init__()
        self.initialize_components()

    def initialize_components(self) -> None:
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "settings_view.ui")
        uic.loadUi(ui_path, self)

        # Close icon
        self.btn_close.setIcon(get_icon(":/icons/IMG-Close.png"))
        self.btn_close.setIconSize(QSize(20, 20))

        # Wire buttons
        self.btn_save_settings.clicked.connect(self.save_settings_requested.emit)
        self.btn_discard.clicked.connect(self.discard_requested.emit)

        # Wire list selection → preview signal
        self.list_themes.currentRowChanged.connect(self._on_theme_row_changed)

        # Style the sample primary button so it reacts to the accent
        self.btn_sample_primary.setObjectName("btn_save")

    # ------------------------------------------------------------------ #
    # Shared
    # ------------------------------------------------------------------ #

    def set_user_info(self, user_info: dict) -> None:
        self.label_user_name.setText(f"Username: {user_info.get('username', 'Unknown')}")
        self.label_user_role.setText(f"Role: {user_info.get('role', 'Unknown')}")

    # ------------------------------------------------------------------ #
    # Theme list
    # ------------------------------------------------------------------ #

    def populate_theme_list(self, themes: list[tuple[str, str, str]]) -> None:
        """
        Fills the list widget with one item per theme.

        Args:
            themes: List of (key, display_name, accent_hex) tuples.
        """
        self.list_themes.clear()
        for key, display_name, accent_hex in themes:
            icon = self._make_color_icon(accent_hex, size=24)
            item = QListWidgetItem(icon, f"  {display_name}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setSizeHint(QSize(0, 40))
            self.list_themes.addItem(item)

    def set_current_theme(self, theme_key: str) -> None:
        """Selects the row that matches theme_key. Blocks the signal to avoid recursion."""
        self.list_themes.blockSignals(True)
        for i in range(self.list_themes.count()):
            item = self.list_themes.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == theme_key:
                self.list_themes.setCurrentRow(i)
                break
        self.list_themes.blockSignals(False)

    def get_selected_theme_key(self) -> Optional[str]:
        """Returns the key of the currently selected theme, or None."""
        item = self.list_themes.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    # ------------------------------------------------------------------ #
    # Preview panel
    # ------------------------------------------------------------------ #

    def update_preview(self, display_name: str, accent_hex: str) -> None:
        """Updates the right-side preview panel label and color swatch."""
        self.label_selected_theme.setText(display_name)
        self.frame_color_swatch.setStyleSheet(
            f"background-color: {accent_hex}; border-radius: 6px; border: none;"
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _on_theme_row_changed(self, row: int) -> None:
        """Translates a list row change into a theme_selected(key) signal."""
        item = self.list_themes.item(row)
        if item:
            key = item.data(Qt.ItemDataRole.UserRole)
            if key:
                self.theme_selected.emit(key)

    @staticmethod
    def _make_color_icon(hex_color: str, size: int = 24) -> QIcon:
        """Creates a solid-color square QIcon from a hex color string."""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(hex_color))
        return QIcon(pixmap)
