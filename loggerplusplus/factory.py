"""
Public Logger Factory
=====================

User-facing, dead simple API:

    from loggerplusplus import LoggerPlusPlus, LoggerConfig
    log = LoggerPlusPlus(cfg)
    log.info("ready")
"""

from __future__ import annotations

import logging

from .logger.manager import LoggerManager
from .config.core import LoggerConfig


class LoggerPlusPlus:
    """
    Friendly factory so you can write: LoggerPlusPlus(config) -> logging.Logger

    Returns the cached logger built by LoggerManager for the given config,
    so repeated calls with the same identifier will not duplicate handlers.
    """

    def __new__(
            cls,
            identifier: str = "",
            config: LoggerConfig | None = None,
            global_config: bool = False
    ) -> logging.Logger:
        if config is None and global_config is False:
            config = LoggerConfig(identifier=identifier)
        elif config and global_config is False:
            config.identifier = identifier
        else:
            config = LoggerManager.get_default_config()
            config.identifier = identifier

        return LoggerManager.get(config)

    @classmethod
    def reconfigure(cls, new_config: LoggerConfig) -> logging.Logger:
        """Optional helper to bubble up manager's hot-reconfigure."""
        return LoggerManager.reconfigure(new_config)
