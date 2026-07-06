import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ErrorMessages:
    """Centralized error messages for the application."""

    # Generic error messages for users
    GENERIC_ERROR = "An error occurred. Please contact your system administrator."
    VALIDATION_ERROR = "The data entered is not valid. Please check your input."
    PERMISSION_DENIED = "You do not have permission to perform this action."
    DATABASE_ERROR = "A database error occurred. Please try again later."
    AUTHENTICATION_ERROR = "Authentication failed. Please check your credentials."
    SESSION_EXPIRED = "Your session has expired. Please log in again."
    NETWORK_ERROR = "A network error occurred. Please check your connection."
    NOT_FOUND = "The requested resource was not found."
    DUPLICATE_ERROR = "This record already exists in the system."

    # Login-specific messages
    LOGIN_FAILED = "Invalid username or password."
    ACCOUNT_LOCKED = "Account temporarily locked due to multiple failed attempts."
    ACCOUNT_DISABLED = "This account has been disabled. Please contact an administrator."
    
    # Password-related messages
    PASSWORD_MISMATCH = "Passwords do not match."
    PASSWORD_WEAK = "Password does not meet security requirements."
    PASSWORD_CHANGE_SUCCESS = "Password changed successfully."
    PASSWORD_CHANGE_FAILED = "Failed to change password. Please try again."
    
    # Operation result messages
    SAVE_SUCCESS = "Record saved successfully."
    SAVE_FAILED = "Failed to save record. Please try again."
    DELETE_SUCCESS = "Record deleted successfully."
    DELETE_FAILED = "Failed to delete record. Please try again."
    UPDATE_SUCCESS = "Record updated successfully."
    UPDATE_FAILED = "Failed to update record. Please try again."

    # Members module
    MEMBERS_NO_PERMISSION_READ = "You do not have permission to view members"
    MEMBERS_NO_PERMISSION_CREATE = "You do not have permission to create members"
    MEMBERS_NO_PERMISSION_UPDATE = "You do not have permission to update members"
    MEMBERS_SELECT_SEARCH_OPTION = "Please select a search option"
    MEMBERS_NOT_FOUND_BY_CODE = "No member found with that code"
    MEMBERS_ID_REQUIRED = "Member ID is required for updates"
    MEMBERS_NO_SELECTION = "Please select a member to update"
    MEMBERS_CREATED = "Member created successfully"
    MEMBERS_CREATION_FAILED = "Creation failed"
    MEMBERS_UPDATED = "Member updated successfully"
    MEMBERS_UPDATE_FAILED = "Update failed"
    MEMBERS_OPERATION_CANCELLED = "Operation cancelled"
    MEMBERS_UNEXPECTED_ERROR = "An unexpected error occurred. Please try again."

    # Attendance module
    ATTENDANCE_NO_PERMISSION_READ   = "You do not have permission to view attendance"
    ATTENDANCE_NO_PERMISSION_CREATE = "You do not have permission to register attendance"
    ATTENDANCE_MEMBER_NOT_FOUND     = "No active member found with that code or name"
    ATTENDANCE_ALREADY_CHECKED_IN   = "This member already has an open check-in today"
    ATTENDANCE_NO_OPEN_CHECKIN              = "This member has no open check-in to close"
    ATTENDANCE_NO_OPEN_CHECKIN_FOR_MEMBER   = "This member has no open check-in today"
    ATTENDANCE_NO_SELECTION                 = "Please select a record or enter a member code/name"
    ATTENDANCE_CHECKIN_SUCCESS      = "Check-in registered successfully"
    ATTENDANCE_CHECKOUT_SUCCESS     = "Check-out registered successfully"
    ATTENDANCE_CHECKIN_FAILED       = "Failed to register check-in"
    ATTENDANCE_CHECKOUT_FAILED      = "Failed to register check-out"
    ATTENDANCE_SEARCH_EMPTY         = "Please enter a member code or name to search"
    ATTENDANCE_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."


    # Memberships module — Plans
    PLANS_NO_PERMISSION_CREATE  = "You do not have permission to create plans"
    PLANS_NO_PERMISSION_UPDATE  = "You do not have permission to update plans"
    PLANS_NO_SELECTION          = "Please select a plan"
    PLANS_NAME_REQUIRED         = "Plan name is required"
    PLANS_INVALID_PRICE         = "Price must be zero or greater"
    PLANS_INVALID_DURATION      = "Duration must be at least 1 day"
    PLANS_CREATED               = "Plan created successfully"
    PLANS_CREATION_FAILED       = "Failed to create plan. Please try again."
    PLANS_UPDATED               = "Plan updated successfully"
    PLANS_UPDATE_FAILED         = "Failed to update plan. Please try again."
    PLANS_STATUS_UPDATED        = "Plan status updated successfully"
    PLANS_STATUS_UPDATE_FAILED  = "Failed to update plan status. Please try again."
    PLANS_UNEXPECTED_ERROR      = "An unexpected error occurred. Please try again."

    # Memberships module — Member Memberships
    MEMBERSHIPS_NO_PERMISSION_READ   = "You do not have permission to view memberships"
    MEMBERSHIPS_NO_PERMISSION_CREATE = "You do not have permission to assign memberships"
    MEMBERSHIPS_NO_PERMISSION_UPDATE = "You do not have permission to update memberships"
    MEMBERSHIPS_NO_PERMISSION_DELETE = "You do not have permission to delete memberships"
    MEMBERSHIPS_MEMBER_NOT_FOUND     = "No active member found with that code or name"
    MEMBERSHIPS_PLAN_NOT_FOUND       = "The selected plan was not found"
    MEMBERSHIPS_ALREADY_ACTIVE       = "This member already has an active membership"
    MEMBERSHIPS_NO_SELECTION         = "Please select a membership from the table"
    MEMBERSHIPS_INVALID_TRANSITION   = "This status change is not allowed"
    MEMBERSHIPS_ASSIGNED             = "Membership assigned successfully"
    MEMBERSHIPS_ASSIGN_FAILED        = "Failed to assign membership. Please try again."
    MEMBERSHIPS_STATUS_UPDATED       = "Membership status updated successfully"
    MEMBERSHIPS_STATUS_UPDATE_FAILED = "Failed to update membership status. Please try again."
    MEMBERSHIPS_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Payments module
    PAYMENTS_NO_PERMISSION_READ   = "You do not have permission to view payments"
    PAYMENTS_NO_PERMISSION_CREATE = "You do not have permission to register payments"
    PAYMENTS_NO_PERMISSION_UPDATE = "You do not have permission to update payments"
    PAYMENTS_MEMBER_NOT_FOUND     = "No active member found with that code or name"
    PAYMENTS_INVALID_AMOUNT       = "Amount must be greater than zero"
    PAYMENTS_NO_SELECTION         = "Please select a payment from the table"
    PAYMENTS_CREATED              = "Payment registered successfully"
    PAYMENTS_CREATION_FAILED      = "Failed to register payment. Please try again."
    PAYMENTS_UPDATED              = "Payment updated successfully"
    PAYMENTS_UPDATE_FAILED        = "Failed to update payment. Please try again."
    PAYMENTS_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Classes module — Class definitions
    CLASSES_NO_PERMISSION_READ   = "You do not have permission to view classes"
    CLASSES_NO_PERMISSION_CREATE = "You do not have permission to create classes"
    CLASSES_NO_PERMISSION_UPDATE = "You do not have permission to update classes"
    CLASSES_NAME_REQUIRED        = "Class name is required"
    CLASSES_INVALID_DURATION     = "Duration must be at least 1 minute"
    CLASSES_INVALID_CAPACITY     = "Capacity must be greater than zero"
    CLASSES_NO_SELECTION         = "Please select a class from the table"
    CLASSES_CREATED              = "Class created successfully"
    CLASSES_CREATION_FAILED      = "Failed to create class. Please try again."
    CLASSES_UPDATED              = "Class updated successfully"
    CLASSES_UPDATE_FAILED        = "Failed to update class. Please try again."
    CLASSES_STATUS_UPDATED       = "Class status updated successfully"
    CLASSES_STATUS_UPDATE_FAILED = "Failed to update class status. Please try again."
    CLASSES_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Classes module — Schedules
    SCHEDULES_NO_PERMISSION_CREATE = "You do not have permission to create schedules"
    SCHEDULES_NO_PERMISSION_UPDATE = "You do not have permission to update schedules"
    SCHEDULES_CLASS_REQUIRED       = "Please select a class for the schedule"
    SCHEDULES_INVALID_TIME         = "End time must be after start time"
    SCHEDULES_NO_SELECTION         = "Please select a schedule from the table"
    SCHEDULES_CREATED              = "Schedule created successfully"
    SCHEDULES_CREATION_FAILED      = "Failed to create schedule. Please try again."
    SCHEDULES_UPDATED              = "Schedule updated successfully"
    SCHEDULES_UPDATE_FAILED        = "Failed to update schedule. Please try again."
    SCHEDULES_STATUS_UPDATED       = "Schedule status updated successfully"
    SCHEDULES_STATUS_UPDATE_FAILED = "Failed to update schedule status. Please try again."
    SCHEDULES_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Classes module — Enrollments
    ENROLLMENTS_NO_PERMISSION_CREATE = "You do not have permission to enroll members"
    ENROLLMENTS_NO_PERMISSION_UPDATE = "You do not have permission to update enrollments"
    ENROLLMENTS_MEMBER_NOT_FOUND     = "No active member found with that code or name"
    ENROLLMENTS_SCHEDULE_REQUIRED    = "Please select a schedule to enroll into"
    ENROLLMENTS_ALREADY_ENROLLED     = "This member is already enrolled in this class"
    ENROLLMENTS_CLASS_FULL           = "This class has reached its maximum capacity"
    ENROLLMENTS_NO_SELECTION         = "Please select an enrollment from the table"
    ENROLLMENTS_ENROLLED             = "Member enrolled successfully"
    ENROLLMENTS_ENROLL_FAILED        = "Failed to enroll member. Please try again."
    ENROLLMENTS_STATUS_UPDATED       = "Enrollment status updated successfully"
    ENROLLMENTS_STATUS_UPDATE_FAILED = "Failed to update enrollment status. Please try again."
    ENROLLMENTS_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Dashboard module
    DASHBOARD_NO_PERMISSION_READ = "You do not have permission to view the dashboard"
    DASHBOARD_LOAD_FAILED        = "Failed to load dashboard data. Please try again."
    DASHBOARD_UNEXPECTED_ERROR   = "An unexpected error occurred. Please try again."

    # Instructors module
    INSTRUCTORS_NO_PERMISSION_READ   = "You do not have permission to view instructors"
    INSTRUCTORS_NO_PERMISSION_CREATE = "You do not have permission to create instructors"
    INSTRUCTORS_NO_PERMISSION_UPDATE = "You do not have permission to update instructors"
    INSTRUCTORS_SELECT_SEARCH_OPTION = "Please select a search option"
    INSTRUCTORS_ID_REQUIRED          = "Instructor ID is required for updates"
    INSTRUCTORS_NO_SELECTION         = "Please select an instructor to update"
    INSTRUCTORS_CREATED              = "Instructor created successfully"
    INSTRUCTORS_CREATION_FAILED      = "Creation failed"
    INSTRUCTORS_UPDATED              = "Instructor updated successfully"
    INSTRUCTORS_UPDATE_FAILED        = "Update failed"
    INSTRUCTORS_OPERATION_CANCELLED  = "Operation cancelled"
    INSTRUCTORS_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Equipment module
    EQUIPMENT_NO_PERMISSION_READ   = "You do not have permission to view equipment"
    EQUIPMENT_NO_PERMISSION_CREATE = "You do not have permission to create equipment"
    EQUIPMENT_NO_PERMISSION_UPDATE = "You do not have permission to update equipment"
    EQUIPMENT_NAME_REQUIRED        = "Equipment name is required"
    EQUIPMENT_INVALID_PRICE        = "Purchase price must be zero or greater"
    EQUIPMENT_NO_SELECTION         = "Please select an equipment item from the table"
    EQUIPMENT_ID_REQUIRED          = "Equipment ID is required for updates"
    EQUIPMENT_CREATED              = "Equipment created successfully"
    EQUIPMENT_CREATION_FAILED      = "Failed to create equipment. Please try again."
    EQUIPMENT_UPDATED              = "Equipment updated successfully"
    EQUIPMENT_UPDATE_FAILED        = "Failed to update equipment. Please try again."
    EQUIPMENT_OPERATION_CANCELLED  = "Operation cancelled"
    EQUIPMENT_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    # Equipment module — Maintenance
    MAINTENANCE_NO_PERMISSION_READ   = "You do not have permission to view maintenance records"
    MAINTENANCE_NO_PERMISSION_CREATE = "You do not have permission to log maintenance"
    MAINTENANCE_EQUIPMENT_REQUIRED   = "Please select the equipment being serviced"
    MAINTENANCE_LOGGED               = "Maintenance record logged successfully"
    MAINTENANCE_LOG_FAILED           = "Failed to log maintenance. Please try again."
    MAINTENANCE_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."

    @staticmethod
    def log_and_mask_error(error: Exception, context: str, user_message: Optional[str] = None) -> str:
        """
        Logs the error with context and returns a user-friendly message.
        The actual error details are masked from the user for security reasons.
        
        Args:
            error: The exception that was raised.
            context: A string describing where in the code the error occurred.
            user_message: An optional custom message to return to the user instead of the generic one.

        Returns:
            A user-friendly error message.
        """

        logger.error(f"Error in {context}: {str(error)}", exc_info=True)
        return user_message or ErrorMessages.GENERIC_ERROR
    

