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

    # Permissions related to classes
    CLASSES_CREATE = "classes.create"
    CLASSES_READ   = "classes.read"
    CLASSES_UPDATE = "classes.update"

    # Permissions related to class schedules
    SCHEDULES_CREATE = "schedules.create"
    SCHEDULES_READ   = "schedules.read"
    SCHEDULES_UPDATE = "schedules.update"

    # Permissions related to class enrollments
    ENROLLMENTS_CREATE = "enrollments.create"
    ENROLLMENTS_READ   = "enrollments.read"
    ENROLLMENTS_UPDATE = "enrollments.update"

    # Permissions related to the dashboard
    DASHBOARD_READ = "dashboard.read"

    # Permissions related to instructors
    INSTRUCTORS_CREATE = "instructors.create"
    INSTRUCTORS_READ   = "instructors.read"
    INSTRUCTORS_UPDATE = "instructors.update"

    # Permissions related to equipment
    EQUIPMENT_CREATE = "equipment.create"
    EQUIPMENT_READ   = "equipment.read"
    EQUIPMENT_UPDATE = "equipment.update"

    # Permissions related to equipment maintenance
    MAINTENANCE_CREATE = "maintenance.create"
    MAINTENANCE_READ   = "maintenance.read"