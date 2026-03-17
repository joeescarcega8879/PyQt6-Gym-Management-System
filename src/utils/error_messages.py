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
    

