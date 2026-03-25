# from src.utils.status_type import StatusType
from .status_type import StatusType

STATUS_BAR_STYLES = {
    StatusType.SUCCESS: """
        .QStatusBar {
            background-color: #e7f6e7;
            color: #1f7a1f;
        }
    """,
    StatusType.ERROR: """
        .QStatusBar {
            background-color: #f8e6e6;
            color: #a12f2f;
        }
    """,

    StatusType.WARNING: """
        .QStatusBar {
            background-color: #fff4e5;
            color: #a15c1f;
        }
    """,
    StatusType.INFO: """
        .QStatusBar {
            background-color: #e5f3ff;
            color: #1f5ca1;
        }
    """
}