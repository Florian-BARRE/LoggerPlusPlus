# ====== Code Summary ======
# This module defines configuration for log levels in different output targets,
# such as console and file logging.

from __future__ import annotations

# ====== Standard Library Imports ======
from dataclasses import dataclass

# ====== Internal Project Imports ======
from ..loglevel import LogLevels


@dataclass(slots=True)
class LevelConfig:
    """
    Configuration for logging levels per output target.

    Attributes:
        console_level (LogLevels): Minimum level of logs to display on the console.
        file_level (LogLevels): Minimum level of logs to write to files.
    """

    console_level: LogLevels = LogLevels.INFO
    file_level: LogLevels = LogLevels.DEBUG
