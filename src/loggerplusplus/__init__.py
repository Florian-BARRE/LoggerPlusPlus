from __future__ import annotations

from loguru import logger as _loguru_logger

# --------------------- Submodules --------------------- #
from . import formats

# --------------------- Enhanced API --------------------- #
from .api import add
from .decorators import catch, log_io, log_timing, opt
from .logger_class import LoggerClass
from .proxy import LoggerPlusPlus, loggerplusplus
from .registry import (
    import_widths,
    observed_widths,
    register_identifier,
    reset_widths,
    set_max_auto_width,
)

# --------------------- Version --------------------- #
# Single source of truth for the runtime version; kept in sync with pyproject.toml
# by release-please (see release-please-config.json `extra-files`).
__version__ = "1.0.5"

# `logger` is the ENHANCED, ready-to-use singleton (drop-in for loguru's `logger`),
# so `from loggerplusplus import logger` gets the overridden add/catch/opt/... .
logger = loggerplusplus
# loguru passthrough, exposed so the documented remove()/add() pair is importable top-level.
remove = _loguru_logger.remove

# ------------------- Public API ------------------- #
__all__ = [
    "__version__",
    # Classes / singleton
    "LoggerClass",
    "LoggerPlusPlus",  # the proxy class
    "loggerplusplus",  # the singleton instance
    "logger",  # alias of the singleton
    "formats",  # formats submodule (resolved by name downstream)
    # Functional API (also available as methods on the singleton)
    "add",
    "remove",
    "catch",
    "opt",
    "log_timing",
    "log_io",
    # Auto-width registry controls
    "register_identifier",
    "reset_widths",
    "observed_widths",
    "set_max_auto_width",
    "import_widths",
]
