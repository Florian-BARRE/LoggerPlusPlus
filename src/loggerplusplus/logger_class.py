# ====== Code Summary ======
# Defines `LoggerClass`, a mixin providing a `self.logger` attribute.
# The logger is bound with an identifier (defaulting to the class name),
# enabling consistent identification of log records within the system.

from __future__ import annotations

from typing import Optional

from loguru import logger as _loguru_logger

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

    def __init__(
        self,
        *,
        identifier: Optional[str] = None,
        _log_identifier: Optional[str] = None,
    ) -> None:
        """
        Initialize the logger with an identifier and register it.

        Args:
            identifier (str | None): Public, explicit identifier for the logger.
                Defaults to the class name when not provided.
            _log_identifier (str | None): Deprecated alias of `identifier`, kept for
                backward compatibility; `identifier` takes precedence when both are given.
        """
        # 1. Resolve identifier: public arg, then legacy alias, then class name
        ident = identifier or _log_identifier or self.__class__.__name__

        # 2. Register identifier in global registry
        register_identifier(ident)

        # 3. Bind logger with identifier and attach to instance
        self.logger = _loguru_logger.bind(identifier=ident)
