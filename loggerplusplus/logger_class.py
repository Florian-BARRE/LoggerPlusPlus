# ====== Code Summary ======
# Defines `LoggerClass`, a mixin providing a `self.logger` attribute.
# The logger is bound with an identifier (defaulting to the class name),
# enabling consistent identification of log records within the system.

from __future__ import annotations

# ====== Third-Party Library Imports ======
from loguru import logger as _loguru_logger

# ====== Local Project Imports ======
from .registry import register_identifier

# ------------------- Public API ------------------- #
__all__ = ["LoggerClass"]


class LoggerClass:
    """
    Base class/mixin that provides `self.logger` bound with an identifier.
    By default, the identifier is the class name, but it can be overridden.

    Example:
        class MyService(LoggerClass):
            def __init__(self):
                super().__init__()
                self.logger.info("Service started")

    Attributes:
        logger: A loguru logger instance bound with an `identifier`.
    """

    def __init__(self, *, _log_identifier: str | None = None) -> None:
        """
        Initialize the logger with an identifier and register it.

        Args:
            _log_identifier (str | None): Optional explicit identifier for the logger.
                Defaults to the class name when not provided.
        """
        # 1. Resolve identifier: provided argument or fallback to class name
        ident = _log_identifier or self.__class__.__name__

        # 2. Register identifier in global registry
        register_identifier(ident)

        # 3. Bind logger with identifier and attach to instance
        self.logger = _loguru_logger.bind(identifier=ident)
