# --------------------- Version --------------------- #
# Single source of truth for the runtime version; kept in sync with pyproject.toml
# by release-please (see release-please-config.json `extra-files`).
__version__ = "1.0.5"

# --------------------- Logger --------------------- #
from .logger_class import LoggerClass

# --------------------- Logger Proxy --------------------- #
from .proxy import LoggerPlusPlus, loggerplusplus

# `LoggerPlusPlus` : The proxy *class* that wraps around `loguru.logger`.
# `loggerplusplus` : A ready-to-use *singleton instance* of `LoggerPlusPlus`,
#                    provided for convenience (mirroring loguru's usage style).

# ------------------- Public API ------------------- #
__all__ = [
    "__version__",
    "LoggerClass",
    "LoggerPlusPlus",  # The class definition
    "loggerplusplus",  # The singleton instance
]
