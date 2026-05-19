from src.models.enums import UserRole
from src.domain.permissions_definitions import Permissions

PERMISSIONS = {

    # Permissions related to members
    Permissions.MEMBERS_CREATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.MEMBERS_READ: {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.INSTRUCTOR, UserRole.ACCOUNTANT},
    Permissions.MEMBERS_UPDATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.MEMBERS_DELETE: {UserRole.ADMIN},

    # Permissions related to attendance
    Permissions.ATTENDANCE_READ: {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.INSTRUCTOR},
    Permissions.ATTENDANCE_CREATE: {UserRole.RECEPTIONIST, UserRole.ADMIN},

    # Permissions related to membership plans
    Permissions.PLANS_CREATE: {UserRole.ADMIN},
    Permissions.PLANS_UPDATE: {UserRole.ADMIN},

    # Permissions related to member memberships
    Permissions.MEMBERSHIPS_READ: {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.ACCOUNTANT},
    Permissions.MEMBERSHIPS_CREATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.MEMBERSHIPS_UPDATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.MEMBERSHIPS_DELETE: {UserRole.ADMIN},

    # Permissions related to payments
    Permissions.PAYMENTS_READ: {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.ACCOUNTANT},
    Permissions.PAYMENTS_CREATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.PAYMENTS_UPDATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},

    # Permissions related to classes
    Permissions.CLASSES_READ:   {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.INSTRUCTOR},
    Permissions.CLASSES_CREATE: {UserRole.ADMIN},
    Permissions.CLASSES_UPDATE: {UserRole.ADMIN},

    # Permissions related to class schedules
    Permissions.SCHEDULES_READ:   {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.INSTRUCTOR},
    Permissions.SCHEDULES_CREATE: {UserRole.ADMIN},
    Permissions.SCHEDULES_UPDATE: {UserRole.ADMIN},

    # Permissions related to class enrollments
    Permissions.ENROLLMENTS_READ:   {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.INSTRUCTOR},
    Permissions.ENROLLMENTS_CREATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.ENROLLMENTS_UPDATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},

}