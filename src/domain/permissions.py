from src.models.enums import UserRole
from src.domain.permissions_definitions import Permissions

PERMISSIONS = {

    # Permissions related to members
    Permissions.MEMBERS_CREATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.MEMBERS_READ: {UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.INSTRUCTOR, UserRole.ACCOUNTANT},
    Permissions.MEMBERS_UPDATE: {UserRole.ADMIN, UserRole.RECEPTIONIST},
    Permissions.MEMBERS_DELETE: {UserRole.ADMIN},

}