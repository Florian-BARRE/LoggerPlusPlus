from __future__ import annotations

from loguru import logger as _loguru_logger

# --------------------- Submodules --------------------- #
from . import formats

# --------------------- Enhanced API --------------------- #
from .api import add
from .bootstrap import configure_from_env, setup
from .context import bind_context, new_id, otel_context
from .decorators import SENSITIVE_KEYS, catch, log_io, log_timing, opt
from .formats import DEFAULT_THEME, Theme
from .intercept import InterceptHandler, intercept_std_logging
from .logger_class import LoggerClass
from .proxy import LoggerPlusPlus, loggerplusplus
from .registry import (
    import_widths,
    observed_widths,
    register_identifier,
    reset_widths,
    set_max_auto_width,
)
from .structured import add_json

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
    "Theme",  # color theme for the formats
    "DEFAULT_THEME",
    # Functional API (also available as methods on the singleton)
    "add",
    "remove",
    "catch",
    "opt",
    "log_timing",
    "log_io",
    "SENSITIVE_KEYS",
    # Correlation context
    "bind_context",
    "new_id",
    "otel_context",
    # Structured (JSON) output
    "add_json",
    # One-call setup
    "setup",
    "configure_from_env",
    # Standard-library logging bridge
    "intercept_std_logging",
    "InterceptHandler",
    # Auto-width registry controls
    "register_identifier",
    "reset_widths",
    "observed_widths",
    "set_max_auto_width",
    "import_widths",
]
