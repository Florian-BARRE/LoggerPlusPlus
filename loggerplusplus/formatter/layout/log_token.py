# ====== Code Summary ======
# This module defines the `LogToken` enumeration, which represents the set of
# supported tokens for log message templates (e.g., date, level, message).
# Each token can be rendered as a string in curly-brace format (e.g., "{level}")
# and is used by log formatting utilities.

# ====== Standard Library Imports ======
from __future__ import annotations
from enum import StrEnum


class LogToken(StrEnum):
    """
    Enumeration of log tokens used in template-based log formatting.

    Members:
        DATE (str): Timestamp token ("date").
        LEVEL (str): Log level token ("level").
        IDENT (str): Identifier token ("id").
        FILENAME (str): Filename token ("file").
        LINENO (str): Line number token ("line").
        FUNCNAME (str): Function name token ("func").
        MODULE (str): Module name token ("module").
        THREAD (str): Thread ID token ("thread").
        PROCESS (str): Process ID token ("process").
        MSG (str): Log message token ("msg").
    """

    DATE = "date"
    LEVEL = "level"
    IDENT = "id"
    FILENAME = "file"
    LINENO = "line"
    FUNCNAME = "func"
    MODULE = "module"
    THREAD = "thread"
    PROCESS = "process"
    MSG = "msg"

    def __str__(self) -> str:
        """
        Return the token as a template placeholder in curly braces.

        Returns:
            str: The token formatted as "{token}".
        """
        return "{" + str(self.value) + "}"

    def __format__(self, spec: str) -> str:
        """
        Format the token as a string with optional format specification.

        Args:
            spec (str): Optional format specification.

        Returns:
            str: Formatted token string.
        """
        return format(str(self), spec)
