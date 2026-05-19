from __future__ import annotations

from typing import Optional

from src.models import User
from src.services.settings_service import settings_service, AVAILABLE_THEMES
from src.utils.error_messages import ErrorMessages
from src.utils.status_type import StatusType


class SettingsPresenter:
    """
    Coordinates SettingsView with SettingsService.

    Responsibilities:
    - Load saved theme preference on open.
    - Apply theme preview live when the user selects a different theme.
    - Save the preference when the user clicks Save.
    - Restore the original theme when the user clicks Discard.
    """

    def __init__(self, view, main_app, status_handler, current_user: Optional[User] = None) -> None:
        self.view           = view
        self.main_app       = main_app
        self.status_handler = status_handler
        self._current_user  = current_user

        # The theme active when the settings panel was opened — used by Discard
        self._original_theme_key: str = "dark_blue"
        # The theme currently previewed (may differ from saved)
        self._previewed_theme_key: str = "dark_blue"

        self._connect_signals()
        self._load_user_information()
        self._initialize()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #

    def _connect_signals(self) -> None:
        self.view.save_settings_requested.connect(self._handle_save)
        self.view.discard_requested.connect(self._handle_discard)
        self.view.theme_selected.connect(self._handle_theme_selected)

    def _initialize(self) -> None:
        """Loads saved settings and populates the view."""
        # Populate theme list
        themes = settings_service.get_available_themes()
        self.view.populate_theme_list(themes)

        # Load saved preferences
        result = settings_service.load()
        saved_theme = result.data.get("theme", "dark_blue") if result.success else "dark_blue"

        self._original_theme_key  = saved_theme
        self._previewed_theme_key = saved_theme

        self.view.set_current_theme(saved_theme)
        self._update_preview_panel(saved_theme)

    # ------------------------------------------------------------------ #
    # Signal handlers
    # ------------------------------------------------------------------ #

    def _handle_theme_selected(self, theme_key: str) -> None:
        """Applies the theme live (preview) without persisting yet."""
        self._previewed_theme_key = theme_key
        self._apply_theme(theme_key)
        self._update_preview_panel(theme_key)

    def _handle_save(self) -> None:
        """Persists the currently previewed theme and updates the original."""
        theme_key = self._previewed_theme_key
        result = settings_service.save({"theme": theme_key})
        if result.success:
            self._original_theme_key = theme_key
            self._emit_success(f"Theme saved: {self._get_display_name(theme_key)}")
        else:
            self._emit_error(result.error or ErrorMessages.GENERIC_ERROR)

    def _handle_discard(self) -> None:
        """Reverts to the theme that was active when the panel was opened."""
        self._previewed_theme_key = self._original_theme_key
        self._apply_theme(self._original_theme_key)
        self.view.set_current_theme(self._original_theme_key)
        self._update_preview_panel(self._original_theme_key)
        self._emit_info("Changes discarded")

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _apply_theme(self, theme_key: str) -> None:
        """Tells main_app to reload the stylesheet for the given theme."""
        self.main_app.load_stylesheet(theme_key)

    def _update_preview_panel(self, theme_key: str) -> None:
        """Updates the right-side preview widgets with the theme's display name and accent."""
        display_name, accent_hex = self._get_theme_meta(theme_key)
        self.view.update_preview(display_name, accent_hex)

    def _load_user_information(self) -> None:
        user_info = {
            "username": self._current_user.username if self._current_user else "Unknown",
            "role":     self._current_user.role.value if self._current_user else "Unknown",
        }
        self.view.set_user_info(user_info)

    @staticmethod
    def _get_theme_meta(theme_key: str) -> tuple[str, str]:
        """Returns (display_name, accent_hex) for a theme key."""
        for key, name, accent in AVAILABLE_THEMES:
            if key == theme_key:
                return name, accent
        return "Dark Blue", "#2196F3"

    @staticmethod
    def _get_display_name(theme_key: str) -> str:
        for key, name, _ in AVAILABLE_THEMES:
            if key == theme_key:
                return name
        return theme_key

    def _emit_success(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.SUCCESS)

    def _emit_error(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.ERROR)

    def _emit_info(self, message: str) -> None:
        self.status_handler(message, 3000, StatusType.INFO)
