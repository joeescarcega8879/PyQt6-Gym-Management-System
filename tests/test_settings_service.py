"""
Tests for SettingsService.

All filesystem interactions are isolated by patching:
  - '_SETTINGS_FILE' — the path to user_settings.json
  - 'src.services.settings_service.config.setup_directories' — no-op

Patch targets:
  'src.services.settings_service._SETTINGS_FILE'
  'src.services.settings_service.config'
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.services.settings_service import SettingsService, AVAILABLE_THEMES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_settings_file(exists: bool, content: dict | None = None):
    """Returns a mock Path object simulating the settings file."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = exists
    if content is not None:
        mock_path.read_text.return_value = json.dumps(content)
    return mock_path


# ---------------------------------------------------------------------------
# get_available_themes  (pure static)
# ---------------------------------------------------------------------------

class TestGetAvailableThemes:
    def test_returns_list(self):
        themes = SettingsService.get_available_themes()
        assert isinstance(themes, list)

    def test_list_is_not_empty(self):
        themes = SettingsService.get_available_themes()
        assert len(themes) > 0

    def test_each_entry_is_three_tuple(self):
        for entry in SettingsService.get_available_themes():
            assert len(entry) == 3

    def test_dark_blue_is_included(self):
        keys = [t[0] for t in SettingsService.get_available_themes()]
        assert "dark_blue" in keys

    def test_dark_green_is_included(self):
        keys = [t[0] for t in SettingsService.get_available_themes()]
        assert "dark_green" in keys

    def test_dark_purple_is_included(self):
        keys = [t[0] for t in SettingsService.get_available_themes()]
        assert "dark_purple" in keys

    def test_dark_orange_is_included(self):
        keys = [t[0] for t in SettingsService.get_available_themes()]
        assert "dark_orange" in keys

    def test_dark_cyan_is_included(self):
        keys = [t[0] for t in SettingsService.get_available_themes()]
        assert "dark_cyan" in keys

    def test_accent_colors_are_hex_strings(self):
        for _, _, accent in SettingsService.get_available_themes():
            assert accent.startswith("#"), f"Expected hex color, got: {accent}"
            assert len(accent) == 7


# ---------------------------------------------------------------------------
# load — file does not exist
# ---------------------------------------------------------------------------

class TestLoadNoFile:
    def test_returns_success(self):
        mock_path = _mock_settings_file(exists=False)
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config") as mock_cfg:
            result = SettingsService().load()
        assert result.success

    def test_returns_defaults_when_file_missing(self):
        mock_path = _mock_settings_file(exists=False)
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().load()
        assert result.data["theme"] == "dark_blue"

    def test_calls_setup_directories(self):
        mock_path = _mock_settings_file(exists=False)
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config") as mock_cfg:
            SettingsService().load()
        mock_cfg.setup_directories.assert_called_once()


# ---------------------------------------------------------------------------
# load — file exists
# ---------------------------------------------------------------------------

class TestLoadWithFile:
    def test_reads_saved_theme(self):
        mock_path = _mock_settings_file(exists=True, content={"theme": "dark_green"})
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().load()
        assert result.success
        assert result.data["theme"] == "dark_green"

    def test_merges_with_defaults(self):
        # File has unknown extra key — should still include defaults
        mock_path = _mock_settings_file(exists=True, content={"theme": "dark_purple", "extra": "value"})
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().load()
        assert result.success
        assert result.data["theme"] == "dark_purple"
        assert result.data["extra"] == "value"

    def test_missing_key_in_file_falls_back_to_default(self):
        # File exists but "theme" key is absent — default should be used
        mock_path = _mock_settings_file(exists=True, content={"other": "stuff"})
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().load()
        assert result.data["theme"] == "dark_blue"

    def test_returns_fail_on_invalid_json(self):
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "{ not valid json !!!"
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().load()
        assert not result.success

    def test_returns_fail_on_read_exception(self):
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.side_effect = OSError("permission denied")
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().load()
        assert not result.success


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

class TestSave:
    def test_save_writes_json(self):
        mock_path = MagicMock(spec=Path)
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().save({"theme": "dark_cyan"})
        assert result.success
        assert result.data is True
        mock_path.write_text.assert_called_once()

    def test_saved_content_is_valid_json(self):
        written_content = []

        def capture_write(text, encoding):
            written_content.append(text)

        mock_path = MagicMock(spec=Path)
        mock_path.write_text.side_effect = capture_write
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            SettingsService().save({"theme": "dark_orange"})

        assert written_content
        parsed = json.loads(written_content[0])
        assert parsed["theme"] == "dark_orange"

    def test_calls_setup_directories(self):
        mock_path = MagicMock(spec=Path)
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config") as mock_cfg:
            SettingsService().save({"theme": "dark_blue"})
        mock_cfg.setup_directories.assert_called_once()

    def test_returns_fail_on_write_exception(self):
        mock_path = MagicMock(spec=Path)
        mock_path.write_text.side_effect = OSError("disk full")
        with patch("src.services.settings_service._SETTINGS_FILE", mock_path), \
             patch("src.services.settings_service.config"):
            result = SettingsService().save({"theme": "dark_blue"})
        assert not result.success


# ---------------------------------------------------------------------------
# get_theme_css_path
# ---------------------------------------------------------------------------

class TestGetThemeCssPath:
    def test_returns_path_for_valid_key(self):
        svc = SettingsService()
        path = svc.get_theme_css_path("dark_blue")
        # The file was generated by generate_themes.py, so it must exist
        assert path is not None
        assert path.exists()

    def test_returns_none_for_invalid_key(self):
        svc = SettingsService()
        path = svc.get_theme_css_path("nonexistent_theme")
        assert path is None

    def test_path_ends_with_css(self):
        svc = SettingsService()
        path = svc.get_theme_css_path("dark_green")
        if path:
            assert str(path).endswith(".css")


# ---------------------------------------------------------------------------
# load_theme_css
# ---------------------------------------------------------------------------

class TestLoadThemeCss:
    def test_returns_css_string_for_valid_theme(self):
        result = SettingsService().load_theme_css("dark_blue")
        assert result.success
        assert isinstance(result.data, str)
        assert len(result.data) > 100  # must be a real CSS file

    def test_css_contains_expected_accent_for_each_theme(self):
        expected = {
            "dark_blue":   "#2196F3",
            "dark_green":  "#4CAF50",
            "dark_purple": "#9C27B0",
            "dark_orange": "#FF9800",
            "dark_cyan":   "#00BCD4",
        }
        for key, accent in expected.items():
            result = SettingsService().load_theme_css(key)
            assert result.success, f"Failed to load theme {key}"
            assert accent in result.data, f"Expected accent {accent} in {key}.css"

    def test_falls_back_to_dark_blue_on_invalid_key(self):
        result = SettingsService().load_theme_css("invalid_theme_xyz")
        assert result.success
        assert "#2196F3" in result.data  # dark_blue accent

    def test_returns_fail_when_no_css_files_exist(self):
        svc = SettingsService()
        with patch.object(svc, "get_theme_css_path", return_value=None):
            result = svc.load_theme_css("dark_blue")
        assert not result.success

    def test_returns_fail_on_read_exception(self):
        svc = SettingsService()
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.side_effect = OSError("disk error")
        with patch.object(svc, "get_theme_css_path", return_value=mock_path):
            result = svc.load_theme_css("dark_blue")
        assert not result.success


# ---------------------------------------------------------------------------
# Round-trip: save then load
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_save_and_load_preserves_theme(self, tmp_path):
        settings_file = tmp_path / "user_settings.json"

        with patch("src.services.settings_service._SETTINGS_FILE", settings_file), \
             patch("src.services.settings_service.config"):
            svc = SettingsService()
            save_result = svc.save({"theme": "dark_purple"})
            assert save_result.success

            load_result = svc.load()
            assert load_result.success
            assert load_result.data["theme"] == "dark_purple"

    def test_overwrite_updates_saved_value(self, tmp_path):
        settings_file = tmp_path / "user_settings.json"

        with patch("src.services.settings_service._SETTINGS_FILE", settings_file), \
             patch("src.services.settings_service.config"):
            svc = SettingsService()
            svc.save({"theme": "dark_orange"})
            svc.save({"theme": "dark_cyan"})
            result = svc.load()
            assert result.data["theme"] == "dark_cyan"
