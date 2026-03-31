from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from src.models.models import Member


class MemberSelectDialog(QDialog):
    """
    Modal dialog that lets the user pick one member from a list.

    Usage::

        dialog = MemberSelectDialog(members, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            member = dialog.selected_member()
    """

    def __init__(self, members: list[Member], parent=None) -> None:
        super().__init__(parent)
        self._members = members
        self._selected: Optional[Member] = None

        self._build_ui()
        self._populate_list()

    def selected_member(self) -> Optional[Member]:
        """Returns the member chosen by the user, or None if cancelled."""
        return self._selected

    def _build_ui(self) -> None:
        self.setWindowTitle("Select Member")
        self.setMinimumWidth(360)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        label = QLabel("Multiple members found. Select one:")
        layout.addWidget(label)

        self._list_widget = QListWidget()
        self._list_widget.setAlternatingRowColors(True)
        self._list_widget.itemDoubleClicked.connect(self._accept_selection)
        layout.addWidget(self._list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Select")
        button_box.accepted.connect(self._accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_list(self) -> None:
        for member in self._members:
            label = f"{member.member_code} — {member.full_name}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, member)
            self._list_widget.addItem(item)

        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)

    def _accept_selection(self) -> None:
        current = self._list_widget.currentItem()
        if current is None:
            return
        self._selected = current.data(Qt.ItemDataRole.UserRole)
        self.accept()
