# ====== Code Summary ======
# This module defines an enumeration of log levels, extending Python's standard
# logging levels with a custom `FATAL` level.

from __future__ import annotations

# ====== Standard Library Imports ======
from enum import IntEnum


class LogLevels(IntEnum):
    """
    Enumeration of log levels, compatible with Python's logging module.

    Attributes:
        NOTSET (int): No specific log level.
        DEBUG (int): Detailed diagnostic information for debugging.
        INFO (int): General informational messages.
        WARNING (int): Indications of potential issues.
        ERROR (int): Errors that allow the application to continue.
        CRITICAL (int): Serious errors requiring immediate attention.
        FATAL (int): Custom extension representing the highest-severity level.
    """

    NOTSET: int = 0
    DEBUG: int = 10
    INFO: int = 20
    WARNING: int = 30
    ERROR: int = 40
    CRITICAL: int = 50
    FATAL: int = 60
