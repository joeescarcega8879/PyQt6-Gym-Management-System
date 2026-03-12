"""
Models package.
Re-exports all enums and dataclass models for backward compatibility.
"""
from src.models.enums import (
    UserRole,
    Gender,
    MembershipStatus,
    PaymentMethod,
    PaymentStatus,
    EquipmentCondition,
    MaintenanceType,
    DifficultyLevel,
    EnrollmentStatus,
    NotificationType,
    NotificationStatus,
)
from src.models.models import (
    User,
    Member,
    MembershipPlan,
    MemberMembership,
    Payment,
    Attendance,
    Instructor,
    Class,
    ClassSchedule,
    ClassEnrollment,
    Equipment,
    EquipmentMaintenance,
    CashRegister,
    Notification,
)

__all__ = [
    # Enums
    'UserRole',
    'Gender',
    'MembershipStatus',
    'PaymentMethod',
    'PaymentStatus',
    'EquipmentCondition',
    'MaintenanceType',
    'DifficultyLevel',
    'EnrollmentStatus',
    'NotificationType',
    'NotificationStatus',
    # Models
    'User',
    'Member',
    'MembershipPlan',
    'MemberMembership',
    'Payment',
    'Attendance',
    'Instructor',
    'Class',
    'ClassSchedule',
    'ClassEnrollment',
    'Equipment',
    'EquipmentMaintenance',
    'CashRegister',
    'Notification',
]
