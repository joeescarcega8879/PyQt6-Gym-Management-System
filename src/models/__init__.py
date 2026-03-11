"""
Modelos de datos del sistema.
Usa dataclasses para facilitar la migración futura a Django Models.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ============================================
# ENUMS
# ============================================

class UserRole(str, Enum):
    """Roles de usuario del sistema"""
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"
    INSTRUCTOR = "instructor"
    ACCOUNTANT = "accountant"


class Gender(str, Enum):
    """Género"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class MembershipStatus(str, Enum):
    """Estados de membresía"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Métodos de pago"""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Estados de pago"""
    COMPLETED = "completed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class EquipmentCondition(str, Enum):
    """Condiciones del equipamiento"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    OUT_OF_SERVICE = "out_of_service"


class MaintenanceType(str, Enum):
    """Tipos de mantenimiento"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    INSPECTION = "inspection"


class DifficultyLevel(str, Enum):
    """Niveles de dificultad de clases"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL = "all"


class EnrollmentStatus(str, Enum):
    """Estados de inscripción a clases"""
    ENROLLED = "enrolled"
    ATTENDED = "attended"
    ABSENT = "absent"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    """Tipos de notificación"""
    MEMBERSHIP_EXPIRING = "membership_expiring"
    MEMBERSHIP_EXPIRED = "membership_expired"
    BIRTHDAY = "birthday"
    PAYMENT_REMINDER = "payment_reminder"
    SYSTEM = "system"
    CUSTOM = "custom"


class NotificationStatus(str, Enum):
    """Estados de notificación"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================
# MODELOS DE DATOS
# ============================================

@dataclass
class User:
    """Usuario del sistema"""
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
    """Miembro del gimnasio"""
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
        """Retorna el nombre completo"""
        return f"{self.first_name} {self.last_name}"


@dataclass
class MembershipPlan:
    """Plan de membresía"""
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
    """Membresía de un miembro"""
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
    
    # Relaciones (se llenarán al cargar desde BD)
    member: Optional[Member] = None
    plan: Optional[MembershipPlan] = None
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la membresía está vencida"""
        if self.end_date:
            return date.today() > self.end_date
        return False


@dataclass
class Payment:
    """Pago"""
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
    
    # Relaciones
    member: Optional[Member] = None


@dataclass
class Attendance:
    """Registro de asistencia"""
    id: Optional[str] = None
    member_id: str = ""
    check_in_time: datetime = field(default_factory=datetime.now)
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    
    # Relaciones
    member: Optional[Member] = None


@dataclass
class Instructor:
    """Instructor"""
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
        """Retorna el nombre completo"""
        return f"{self.first_name} {self.last_name}"


@dataclass
class Class:
    """Clase grupal"""
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
    """Horario de clase"""
    id: Optional[str] = None
    class_id: str = ""
    instructor_id: Optional[str] = None
    day_of_week: int = 0  # 0=Domingo, 6=Sábado
    start_time: str = "00:00"  # Formato HH:MM
    end_time: str = "00:00"
    room: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relaciones
    class_info: Optional[Class] = None
    instructor: Optional[Instructor] = None


@dataclass
class ClassEnrollment:
    """Inscripción a clase"""
    id: Optional[str] = None
    schedule_id: str = ""
    member_id: str = ""
    enrollment_date: datetime = field(default_factory=datetime.now)
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    class_date: date = field(default_factory=date.today)
    notes: Optional[str] = None
    
    # Relaciones
    schedule: Optional[ClassSchedule] = None
    member: Optional[Member] = None


@dataclass
class Equipment:
    """Equipamiento"""
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
    """Mantenimiento de equipamiento"""
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
    
    # Relaciones
    equipment: Optional[Equipment] = None


@dataclass
class CashRegister:
    """Caja registradora"""
    id: Optional[str] = None
    opening_date: datetime = field(default_factory=datetime.now)
    closing_date: Optional[datetime] = None
    opening_amount: float = 0.0
    closing_amount: Optional[float] = None
    expected_amount: Optional[float] = None
    difference: Optional[float] = None
    status: str = "open"  # open, closed
    notes: Optional[str] = None
    opened_by: Optional[str] = None
    closed_by: Optional[str] = None


@dataclass
class Notification:
    """Notificación"""
    id: Optional[str] = None
    notification_type: NotificationType = NotificationType.SYSTEM
    member_id: Optional[str] = None
    title: str = ""
    message: str = ""
    scheduled_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: Optional[datetime] = None
    
    # Relaciones
    member: Optional[Member] = None
