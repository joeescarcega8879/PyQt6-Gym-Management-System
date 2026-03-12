"""
Domain dataclass models for the gym management system.
Uses dataclasses to simplify data handling and facilitate future migration to Django Models.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date

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


@dataclass
class User:
    """Represents a system user with an assigned role."""
    id: Optional[str] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: UserRole = UserRole.RECEPTIONIST
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Member:
    """Represents a gym member."""
    id: Optional[str] = None
    member_code: str = ""
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Returns the member's full name."""
        return f"{self.first_name} {self.last_name}"


@dataclass
class MembershipPlan:
    """Represents a membership plan available for purchase."""
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    duration_days: int = 30
    price: float = 0.0
    has_class_access: bool = True
    max_classes_per_week: Optional[int] = None
    features: Optional[dict] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MemberMembership:
    """Represents the membership assigned to a specific member."""
    id: Optional[str] = None
    member_id: str = ""
    membership_plan_id: str = ""
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    status: MembershipStatus = MembershipStatus.ACTIVE
    auto_renew: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Relationships — populated when loaded from the database
    member: Optional[Member] = None
    plan: Optional[MembershipPlan] = None

    @property
    def is_expired(self) -> bool:
        """Returns True if the membership end date has passed."""
        if self.end_date:
            return date.today() > self.end_date
        return False


@dataclass
class Payment:
    """Represents a payment transaction made by a member."""
    id: Optional[str] = None
    member_id: str = ""
    membership_id: Optional[str] = None
    amount: float = 0.0
    payment_method: PaymentMethod = PaymentMethod.CASH
    payment_date: datetime = field(default_factory=datetime.now)
    status: PaymentStatus = PaymentStatus.COMPLETED
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Relationships — populated when loaded from the database
    member: Optional[Member] = None


@dataclass
class Attendance:
    """Records a member's gym visit (check-in / check-out)."""
    id: Optional[str] = None
    member_id: str = ""
    check_in_time: datetime = field(default_factory=datetime.now)
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None

    # Relationships — populated when loaded from the database
    member: Optional[Member] = None


@dataclass
class Instructor:
    """Represents a gym instructor."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    specialties: List[str] = field(default_factory=list)
    certifications: Optional[str] = None
    hire_date: Optional[date] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Returns the instructor's full name."""
        return f"{self.first_name} {self.last_name}"


@dataclass
class Class:
    """Represents a group fitness class offered by the gym."""
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    duration_minutes: int = 60
    max_capacity: Optional[int] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.ALL
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ClassSchedule:
    """Represents a recurring schedule slot for a class."""
    id: Optional[str] = None
    class_id: str = ""
    instructor_id: Optional[str] = None
    day_of_week: int = 0  # 0 = Sunday, 6 = Saturday
    start_time: str = "00:00"  # Format: HH:MM
    end_time: str = "00:00"   # Format: HH:MM
    room: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships — populated when loaded from the database
    class_info: Optional[Class] = None
    instructor: Optional[Instructor] = None


@dataclass
class ClassEnrollment:
    """Represents a member's enrollment in a scheduled class."""
    id: Optional[str] = None
    schedule_id: str = ""
    member_id: str = ""
    enrollment_date: datetime = field(default_factory=datetime.now)
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    class_date: date = field(default_factory=date.today)
    notes: Optional[str] = None

    # Relationships — populated when loaded from the database
    schedule: Optional[ClassSchedule] = None
    member: Optional[Member] = None


@dataclass
class Equipment:
    """Represents a piece of gym equipment."""
    id: Optional[str] = None
    name: str = ""
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    condition: EquipmentCondition = EquipmentCondition.GOOD
    location: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class EquipmentMaintenance:
    """Records a maintenance event performed on a piece of equipment."""
    id: Optional[str] = None
    equipment_id: str = ""
    maintenance_date: date = field(default_factory=date.today)
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    description: Optional[str] = None
    cost: Optional[float] = None
    performed_by: Optional[str] = None
    next_maintenance_date: Optional[date] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Relationships — populated when loaded from the database
    equipment: Optional[Equipment] = None


@dataclass
class CashRegister:
    """Represents a cash register session (open/close cycle)."""
    id: Optional[str] = None
    opening_date: datetime = field(default_factory=datetime.now)
    closing_date: Optional[datetime] = None
    opening_amount: float = 0.0
    closing_amount: Optional[float] = None
    expected_amount: Optional[float] = None
    difference: Optional[float] = None
    status: str = "open"  # Allowed values: "open", "closed"
    notes: Optional[str] = None
    opened_by: Optional[str] = None
    closed_by: Optional[str] = None


@dataclass
class Notification:
    """Represents a notification sent to a member or generated by the system."""
    id: Optional[str] = None
    notification_type: NotificationType = NotificationType.SYSTEM
    member_id: Optional[str] = None
    title: str = ""
    message: str = ""
    scheduled_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: Optional[datetime] = None

    # Relationships — populated when loaded from the database
    member: Optional[Member] = None
