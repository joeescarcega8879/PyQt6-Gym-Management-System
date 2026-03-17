from src.domain.permissions import PERMISSIONS

class PermissionService:
    """
    PermissionService class provides methods to check if a user has the required permissions to perform certain actions.
    It uses the PERMISSIONS dictionary to determine which roles have access to specific permissions.
    """

    @staticmethod
    def has_permission(user, permission: str) -> bool:
        roles = PERMISSIONS.get(permission, set())
        return user.role in roles