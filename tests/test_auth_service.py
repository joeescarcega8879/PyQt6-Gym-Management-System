"""
Tests for AuthService.

All database interactions are isolated by patching the global `db_manager`
singleton imported inside auth_service.

Patch target: 'src.services.auth_service.db_manager'
"""
import pytest
from unittest.mock import patch, MagicMock

from src.services.auth_service import AuthService
from src.models.enums import UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user_row(**kwargs) -> dict:
    defaults = dict(
        id="user-uuid-001",
        username="john_doe",
        email="john@example.com",
        full_name="John Doe",
        role="admin",
        is_active=True,
        password_hash=AuthService.hash_password("correct_password"),
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# hash_password / _verify_password  (pure static — no mocks needed)
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        h = AuthService.hash_password("mypassword")
        assert isinstance(h, str)

    def test_hash_is_not_plaintext(self):
        h = AuthService.hash_password("mypassword")
        assert h != "mypassword"

    def test_verify_correct_password_returns_true(self):
        h = AuthService.hash_password("secret")
        assert AuthService._verify_password("secret", h) is True

    def test_verify_wrong_password_returns_false(self):
        h = AuthService.hash_password("secret")
        assert AuthService._verify_password("wrong", h) is False

    def test_verify_invalid_hash_returns_false(self):
        assert AuthService._verify_password("secret", "not_a_valid_hash") is False

    def test_two_hashes_of_same_password_differ(self):
        h1 = AuthService.hash_password("pw")
        h2 = AuthService.hash_password("pw")
        # bcrypt uses random salt — same password → different hashes
        assert h1 != h2

    def test_both_hashes_verify_correctly(self):
        h1 = AuthService.hash_password("pw")
        h2 = AuthService.hash_password("pw")
        assert AuthService._verify_password("pw", h1) is True
        assert AuthService._verify_password("pw", h2) is True


# ---------------------------------------------------------------------------
# is_authenticated / get_current_user
# ---------------------------------------------------------------------------

class TestAuthState:
    def setup_method(self):
        self.svc = AuthService()

    def test_not_authenticated_by_default(self):
        assert self.svc.is_authenticated() is False

    def test_get_current_user_returns_none_when_not_logged_in(self):
        assert self.svc.get_current_user() is None


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

class TestLogin:
    def setup_method(self):
        self.svc = AuthService()

    @patch("src.services.auth_service.db_manager")
    def test_successful_login_returns_true_and_user(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        success, error, user = self.svc.login("john_doe", "correct_password")
        assert success is True
        assert error is None
        assert user is not None
        assert user.username == "john_doe"

    @patch("src.services.auth_service.db_manager")
    def test_successful_login_sets_current_user(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        self.svc.login("john_doe", "correct_password")
        assert self.svc.is_authenticated() is True

    @patch("src.services.auth_service.db_manager")
    def test_wrong_password_returns_false(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        success, error, user = self.svc.login("john_doe", "wrong_password")
        assert success is False
        assert user is None
        assert error is not None

    @patch("src.services.auth_service.db_manager")
    def test_user_not_found_returns_false(self, mock_db):
        mock_db.select.return_value = []
        success, error, user = self.svc.login("ghost", "any_pass")
        assert success is False
        assert user is None

    @patch("src.services.auth_service.db_manager")
    def test_login_maps_role_to_enum(self, mock_db):
        mock_db.select.return_value = [make_user_row(role="receptionist")]
        _, _, user = self.svc.login("john_doe", "correct_password")
        assert user.role == UserRole.RECEPTIONIST

    @patch("src.services.auth_service.db_manager")
    def test_db_exception_returns_false_with_message(self, mock_db):
        mock_db.select.side_effect = Exception("connection error")
        success, error, user = self.svc.login("john_doe", "pw")
        assert success is False
        assert error is not None
        assert user is None


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:
    def setup_method(self):
        self.svc = AuthService()

    @patch("src.services.auth_service.db_manager")
    def test_logout_clears_current_user(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        self.svc.login("john_doe", "correct_password")
        assert self.svc.is_authenticated() is True
        self.svc.logout()
        assert self.svc.is_authenticated() is False

    def test_logout_when_not_logged_in_is_safe(self):
        self.svc.logout()
        assert self.svc.is_authenticated() is False


# ---------------------------------------------------------------------------
# has_permission
# ---------------------------------------------------------------------------

class TestHasPermission:
    def setup_method(self):
        self.svc = AuthService()

    def test_not_authenticated_returns_false(self):
        assert self.svc.has_permission(UserRole.RECEPTIONIST) is False

    @patch("src.services.auth_service.db_manager")
    def test_admin_has_permission_for_any_role(self, mock_db):
        mock_db.select.return_value = [make_user_row(role="admin")]
        self.svc.login("john_doe", "correct_password")
        for role in UserRole:
            assert self.svc.has_permission(role) is True

    @patch("src.services.auth_service.db_manager")
    def test_receptionist_has_permission_for_own_role(self, mock_db):
        mock_db.select.return_value = [make_user_row(role="receptionist")]
        self.svc.login("john_doe", "correct_password")
        assert self.svc.has_permission(UserRole.RECEPTIONIST) is True

    @patch("src.services.auth_service.db_manager")
    def test_receptionist_lacks_permission_for_other_roles(self, mock_db):
        mock_db.select.return_value = [make_user_row(role="receptionist")]
        self.svc.login("john_doe", "correct_password")
        assert self.svc.has_permission(UserRole.ADMIN) is False
        assert self.svc.has_permission(UserRole.INSTRUCTOR) is False


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    def setup_method(self):
        self.svc = AuthService()

    @patch("src.services.auth_service.db_manager")
    def test_creates_user_successfully(self, mock_db):
        mock_db.select.return_value = []  # no existing username or email
        mock_db.insert.return_value = {}
        success, error = self.svc.create_user(
            username="newuser",
            email="new@example.com",
            password="secure123",
            full_name="New User",
        )
        assert success is True
        assert error is None

    @patch("src.services.auth_service.db_manager")
    def test_duplicate_username_returns_false(self, mock_db):
        mock_db.select.side_effect = [[make_user_row()]]  # username exists
        success, error = self.svc.create_user("john_doe", "x@x.com", "pw", "Name")
        assert success is False
        assert error is not None

    @patch("src.services.auth_service.db_manager")
    def test_duplicate_email_returns_false(self, mock_db):
        mock_db.select.side_effect = [[], [make_user_row()]]  # email exists
        success, error = self.svc.create_user("newuser", "john@example.com", "pw", "Name")
        assert success is False
        assert error is not None

    @patch("src.services.auth_service.db_manager")
    def test_password_is_hashed_before_insert(self, mock_db):
        mock_db.select.return_value = []
        mock_db.insert.return_value = {}
        self.svc.create_user("u", "e@e.com", "plaintext", "Name")
        inserted_data = mock_db.insert.call_args[0][1]
        assert inserted_data["password_hash"] != "plaintext"
        assert AuthService._verify_password("plaintext", inserted_data["password_hash"])

    @patch("src.services.auth_service.db_manager")
    def test_db_exception_returns_false(self, mock_db):
        mock_db.select.return_value = []
        mock_db.insert.side_effect = Exception("db error")
        success, error = self.svc.create_user("u", "e@e.com", "pw", "Name")
        assert success is False
        assert error is not None


# ---------------------------------------------------------------------------
# change_password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def setup_method(self):
        self.svc = AuthService()

    @patch("src.services.auth_service.db_manager")
    def test_changes_password_successfully(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        mock_db.update.return_value = [{}]
        success, error = self.svc.change_password("user-uuid-001", "correct_password", "new_password")
        assert success is True
        assert error is None

    @patch("src.services.auth_service.db_manager")
    def test_wrong_old_password_returns_false(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        success, error = self.svc.change_password("user-uuid-001", "wrong_password", "new_password")
        assert success is False
        assert error is not None

    @patch("src.services.auth_service.db_manager")
    def test_user_not_found_returns_false(self, mock_db):
        mock_db.select.return_value = []
        success, error = self.svc.change_password("nonexistent", "pw", "new_pw")
        assert success is False
        assert error is not None

    @patch("src.services.auth_service.db_manager")
    def test_new_password_is_hashed_in_update(self, mock_db):
        mock_db.select.return_value = [make_user_row()]
        mock_db.update.return_value = [{}]
        self.svc.change_password("user-uuid-001", "correct_password", "new_secret")
        update_data = mock_db.update.call_args.kwargs["data"]
        assert update_data["password_hash"] != "new_secret"
        assert AuthService._verify_password("new_secret", update_data["password_hash"])

    @patch("src.services.auth_service.db_manager")
    def test_db_exception_returns_false(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        success, error = self.svc.change_password("id", "pw", "new_pw")
        assert success is False
        assert error is not None
