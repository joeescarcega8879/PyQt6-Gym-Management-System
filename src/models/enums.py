"""
Domain enumerations for the gym management system.
All enums use str as a mixin to allow direct comparison with string values from the database.
"""
from enum import Enum


class UserRole(str, Enum):
    """Available roles for system users."""
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"
    INSTRUCTOR = "instructor"
    ACCOUNTANT = "accountant"


class Gender(str, Enum):
    """Gender options for members and instructors."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class MembershipStatus(str, Enum):
    """Possible states of a member's membership."""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Accepted payment methods."""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Possible states of a payment transaction."""
    COMPLETED = "completed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class EquipmentCondition(str, Enum):
    """Physical condition states for gym equipment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    OUT_OF_SERVICE = "out_of_service"


class MaintenanceType(str, Enum):
    """Types of maintenance performed on equipment."""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    INSPECTION = "inspection"


class DifficultyLevel(str, Enum):
    """Difficulty levels for group classes."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL = "all"


class EnrollmentStatus(str, Enum):
    """Possible states of a class enrollment."""
    ENROLLED = "enrolled"
    ATTENDED = "attended"
    ABSENT = "absent"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    """Types of notifications sent to members or system users."""
    MEMBERSHIP_EXPIRING = "membership_expiring"
    MEMBERSHIP_EXPIRED = "membership_expired"
    BIRTHDAY = "birthday"
    PAYMENT_REMINDER = "payment_reminder"
    SYSTEM = "system"
    CUSTOM = "custom"


class NotificationStatus(str, Enum):
    """Delivery status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
