class Permissions:
    """
    Permissions class defines the various permissions that can be assigned to users or roles in the system.
    Each permission is represented as a string constant.
    """

    # Permissions related to members
    MEMBERS_CREATE = "members.create"
    MEMBERS_READ = "members.read"
    MEMBERS_UPDATE = "members.update"
    MEMBERS_DELETE = "members.delete"

    # Permissions related to attendance
    ATTENDANCE_CREATE = "attendance.create"
    ATTENDANCE_READ = "attendance.read" 

    # Permissions related to membership plans
    PLANS_CREATE = "plans.create"
    PLANS_UPDATE = "plans.update"

    # Permissions related to member memberships
    MEMBERSHIPS_READ   = "memberships.read"
    MEMBERSHIPS_CREATE = "memberships.create"
    MEMBERSHIPS_UPDATE = "memberships.update"
    MEMBERSHIPS_DELETE = "memberships.delete"

    # Permissions related to payments
    PAYMENTS_CREATE = "payments.create"
    PAYMENTS_READ   = "payments.read"
    PAYMENTS_UPDATE = "payments.update"