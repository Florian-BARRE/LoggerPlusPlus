# ====== Code Summary ======
# This module defines configuration for enabling or disabling different log output targets.

from __future__ import annotations

# ====== Standard Library Imports ======
from dataclasses import dataclass


@dataclass(slots=True)
class OutputConfig:
    """
    Configuration for controlling which logging outputs are enabled.

    Attributes:
        enable_console (bool): Whether console logging is enabled.
        enable_file (bool): Whether file logging is enabled.
    """

    enable_console: bool = True
    enable_file: bool = True
