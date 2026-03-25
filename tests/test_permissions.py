"""
Tests for PermissionService and Permissions.

These classes are pure Python — no database, no Qt, no mocks required.
We just need User objects with the appropriate role.
"""
import pytest

from src.domain.permissions_definitions import Permissions
from src.domain.permissions_service import PermissionService
from src.models.models import User
from src.models.enums import UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def user_with_role(role: UserRole) -> User:
    return User(username="test", role=role)


# ---------------------------------------------------------------------------
# Permissions constants — sanity check the string values
# ---------------------------------------------------------------------------

class TestPermissionsDefinitions:
    def test_members_create_value(self):
        assert Permissions.MEMBERS_CREATE == "members.create"

    def test_members_read_value(self):
        assert Permissions.MEMBERS_READ == "members.read"

    def test_members_update_value(self):
        assert Permissions.MEMBERS_UPDATE == "members.update"

    def test_members_delete_value(self):
        assert Permissions.MEMBERS_DELETE == "members.delete"

    def test_all_four_permissions_are_distinct(self):
        perms = [
            Permissions.MEMBERS_CREATE,
            Permissions.MEMBERS_READ,
            Permissions.MEMBERS_UPDATE,
            Permissions.MEMBERS_DELETE,
        ]
        assert len(set(perms)) == 4


# ---------------------------------------------------------------------------
# MEMBERS_CREATE
# ---------------------------------------------------------------------------

class TestMembersCreatePermission:
    PERM = Permissions.MEMBERS_CREATE

    def test_admin_can_create(self):
        assert PermissionService.has_permission(user_with_role(UserRole.ADMIN), self.PERM)

    def test_receptionist_can_create(self):
        assert PermissionService.has_permission(user_with_role(UserRole.RECEPTIONIST), self.PERM)

    def test_instructor_cannot_create(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.INSTRUCTOR), self.PERM)

    def test_accountant_cannot_create(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.ACCOUNTANT), self.PERM)


# ---------------------------------------------------------------------------
# MEMBERS_READ
# ---------------------------------------------------------------------------

class TestMembersReadPermission:
    PERM = Permissions.MEMBERS_READ

    def test_admin_can_read(self):
        assert PermissionService.has_permission(user_with_role(UserRole.ADMIN), self.PERM)

    def test_receptionist_can_read(self):
        assert PermissionService.has_permission(user_with_role(UserRole.RECEPTIONIST), self.PERM)

    def test_instructor_can_read(self):
        assert PermissionService.has_permission(user_with_role(UserRole.INSTRUCTOR), self.PERM)

    def test_accountant_can_read(self):
        assert PermissionService.has_permission(user_with_role(UserRole.ACCOUNTANT), self.PERM)


# ---------------------------------------------------------------------------
# MEMBERS_UPDATE
# ---------------------------------------------------------------------------

class TestMembersUpdatePermission:
    PERM = Permissions.MEMBERS_UPDATE

    def test_admin_can_update(self):
        assert PermissionService.has_permission(user_with_role(UserRole.ADMIN), self.PERM)

    def test_receptionist_can_update(self):
        assert PermissionService.has_permission(user_with_role(UserRole.RECEPTIONIST), self.PERM)

    def test_instructor_cannot_update(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.INSTRUCTOR), self.PERM)

    def test_accountant_cannot_update(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.ACCOUNTANT), self.PERM)


# ---------------------------------------------------------------------------
# MEMBERS_DELETE
# ---------------------------------------------------------------------------

class TestMembersDeletePermission:
    PERM = Permissions.MEMBERS_DELETE

    def test_admin_can_delete(self):
        assert PermissionService.has_permission(user_with_role(UserRole.ADMIN), self.PERM)

    def test_receptionist_cannot_delete(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.RECEPTIONIST), self.PERM)

    def test_instructor_cannot_delete(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.INSTRUCTOR), self.PERM)

    def test_accountant_cannot_delete(self):
        assert not PermissionService.has_permission(user_with_role(UserRole.ACCOUNTANT), self.PERM)


# ---------------------------------------------------------------------------
# Unknown permission
# ---------------------------------------------------------------------------

class TestUnknownPermission:
    def test_unknown_permission_always_returns_false(self):
        for role in UserRole:
            assert not PermissionService.has_permission(user_with_role(role), "unknown.permission")
