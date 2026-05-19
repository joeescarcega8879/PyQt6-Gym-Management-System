"""
Settings service — manages user preferences persisted in data/user_settings.json.

All filesystem interactions are encapsulated here so the presenter and tests
never touch the filesystem directly.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.config import config
from src.services.result import ServiceResult

logger = logging.getLogger(__name__)

# Path to the preferences file
_SETTINGS_FILE = config.DATA_DIR / "user_settings.json"

# Ordered list of available themes: (key, display_name, accent_hex)
AVAILABLE_THEMES: list[tuple[str, str, str]] = [
    ("dark_blue",   "Dark Blue",   "#2196F3"),
    ("dark_green",  "Dark Green",  "#4CAF50"),
    ("dark_purple", "Dark Purple", "#9C27B0"),
    ("dark_orange", "Dark Orange", "#FF9800"),
    ("dark_cyan",   "Dark Cyan",   "#00BCD4"),
]

# Default preferences applied when no settings file exists
_DEFAULTS: dict = {
    "theme": "dark_blue",
}


class SettingsService:
    """Loads and saves user preferences to/from data/user_settings.json."""

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def load(self) -> ServiceResult[dict]:
        """
        Reads user preferences from disk.

        Returns:
            ServiceResult[dict]: The full preferences dict on success,
            or the defaults if the file does not exist yet.
        """
        try:
            config.setup_directories()          # ensure data/ exists
            if not _SETTINGS_FILE.exists():
                return ServiceResult.ok(dict(_DEFAULTS))

            raw = _SETTINGS_FILE.read_text(encoding="utf-8")
            data = json.loads(raw)

            # Merge with defaults so new keys added in future versions
            # are always present even in old preference files.
            merged = dict(_DEFAULTS)
            merged.update(data)
            return ServiceResult.ok(merged)

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return ServiceResult.fail(f"Could not load settings: {e}")

    def save(self, settings: dict) -> ServiceResult[bool]:
        """
        Persists user preferences to disk.

        Args:
            settings: The full preferences dict to save.

        Returns:
            ServiceResult[bool]: True on success.
        """
        try:
            config.setup_directories()          # ensure data/ exists
            _SETTINGS_FILE.write_text(
                json.dumps(settings, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info(f"Settings saved to {_SETTINGS_FILE}")
            return ServiceResult.ok(True)

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return ServiceResult.fail(f"Could not save settings: {e}")

    def get_theme_css_path(self, theme_key: str) -> Optional[Path]:
        """
        Returns the absolute path to the CSS file for a given theme key,
        or None if the key is invalid or the file does not exist.

        Args:
            theme_key: One of the keys from AVAILABLE_THEMES (e.g. 'dark_blue').
        """
        themes_dir = Path(__file__).parent.parent / "assets" / "themes"
        css_path = themes_dir / f"{theme_key}.css"
        return css_path if css_path.exists() else None

    def load_theme_css(self, theme_key: str) -> ServiceResult[str]:
        """
        Reads and returns the CSS content for the given theme key.

        Args:
            theme_key: One of the keys from AVAILABLE_THEMES.

        Returns:
            ServiceResult[str]: The CSS text on success.
        """
        try:
            path = self.get_theme_css_path(theme_key)
            if path is None:
                # Fall back to dark_blue if the requested theme file is missing
                logger.warning(f"Theme '{theme_key}' not found — falling back to dark_blue")
                path = self.get_theme_css_path("dark_blue")

            if path is None or not path.exists():
                return ServiceResult.fail("No theme CSS file found")

            return ServiceResult.ok(path.read_text(encoding="utf-8"))

        except Exception as e:
            logger.error(f"Failed to load theme CSS for '{theme_key}': {e}")
            return ServiceResult.fail(f"Could not load theme: {e}")

    @staticmethod
    def get_available_themes() -> list[tuple[str, str, str]]:
        """
        Returns the list of available themes as (key, display_name, accent_hex) tuples.
        """
        return list(AVAILABLE_THEMES)


# Global instance
settings_service = SettingsService()
