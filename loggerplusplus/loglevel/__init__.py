# ---------------------- Log Levels ---------------------- #
from .log_level import LogLevels

# ---------------------- Patching ------------------------ #
from .patch import install_fatal_level

# ------------------- Public API ------------------- #
__all__ = [
    "LogLevels",
    "install_fatal_level",
]
