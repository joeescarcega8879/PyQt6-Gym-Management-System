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
    ATTENDANCE_NO_OPEN_CHECKIN      = "This member has no open check-in to close"
    ATTENDANCE_NO_SELECTION         = "Please select an attendance record"
    ATTENDANCE_CHECKIN_SUCCESS      = "Check-in registered successfully"
    ATTENDANCE_CHECKOUT_SUCCESS     = "Check-out registered successfully"
    ATTENDANCE_CHECKIN_FAILED       = "Failed to register check-in"
    ATTENDANCE_CHECKOUT_FAILED      = "Failed to register check-out"
    ATTENDANCE_SEARCH_EMPTY         = "Please enter a member code or name to search"
    ATTENDANCE_UNEXPECTED_ERROR     = "An unexpected error occurred. Please try again."


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
    

