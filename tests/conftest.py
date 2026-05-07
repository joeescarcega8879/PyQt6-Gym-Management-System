"""
Shared pytest fixtures available to all test modules.
"""
import pytest
from unittest.mock import MagicMock

from src.models.models import Member, User
from src.models.enums import Gender, UserRole


# ---------------------------------------------------------------------------
# Member fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_member() -> Member:
    """A valid Member instance with sensible defaults."""
    return Member(
        id="uuid-001",
        member_code="MEM-AABBCCDD",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="555-1234",
        gender=Gender.MALE,
        is_active=True,
    )


@pytest.fixture
def sample_member_row() -> dict:
    """A raw database row dict matching the members table schema."""
    return dict(
        id="uuid-001",
        member_code="MEM-AABBCCDD",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="555-1234",
        gender="male",
        address=None,
        emergency_contact_name=None,
        emergency_contact_phone=None,
        photo_url=None,
        notes=None,
        is_active=True,
        created_at=None,
        updated_at=None,
        created_by=None,
    )


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user() -> User:
    return User(id="admin-001", username="admin", role=UserRole.ADMIN)


@pytest.fixture
def receptionist_user() -> User:
    return User(id="recep-001", username="receptionist", role=UserRole.RECEPTIONIST)


@pytest.fixture
def instructor_user() -> User:
    return User(id="inst-001", username="instructor", role=UserRole.INSTRUCTOR)


@pytest.fixture
def accountant_user() -> User:
    return User(id="acct-001", username="accountant", role=UserRole.ACCOUNTANT)
