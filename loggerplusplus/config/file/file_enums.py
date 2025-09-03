from __future__ import annotations
from enum import Enum, auto


# ---------------------- File Routing ---------------------- #
class FileRouting(Enum):
    """
    Enumeration of routing strategies for files.

    Options:
        SHARED_ONLY: Files are routed exclusively to shared storage.
        DEDICATED_ONLY: Files are routed exclusively to dedicated storage.
        BOTH: Files are routed to both shared and dedicated storage.
    """

    SHARED_ONLY = auto()
    DEDICATED_ONLY = auto()
    BOTH = auto()


# ---------------------- File Naming ----------------------- #
class FileNaming(Enum):
    """
    Enumeration of file naming strategies.

    Options:
        NONE: No specific naming convention.
        TIMESTAMP: Files are named using precise timestamps.
        DAILY: Files are named based on daily intervals.
        CUSTOM: Files follow a user-defined custom naming scheme.
    """

    NONE = auto()
    TIMESTAMP = auto()
    DAILY = auto()
    CUSTOM = auto()
