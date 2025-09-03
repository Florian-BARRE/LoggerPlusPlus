# ====== Code Summary ======
# This module extends Python's standard logging system by introducing a custom
# `FATAL` log level and installing it into the `logging` module.
# It ensures the level is added only once and provides a `.fatal()` method for loggers.

from __future__ import annotations

# ====== Standard Library Imports ======
import logging

# ====== Internal Project Imports ======
from .log_level import LogLevels

# Tracks whether the fatal log level has already been installed
_installed: bool = False


def install_fatal_level() -> None:
    """
    Install the custom FATAL log level into Python's logging module.

    Behavior:
        - Adds a FATAL level constant and associates it with the name "FATAL".
        - Adds a `Logger.fatal()` method if it does not already exist.
        - Ensures installation is performed only once.

    Returns:
        None
    """
    global _installed

    # 1. Prevent duplicate installation
    if _installed:
        return

    # 2. Register FATAL level name with logging
    logging.addLevelName(LogLevels.FATAL, "FATAL")

    # 3. Define the fatal logging method
    def fatal(self: logging.Logger, msg: str, *args: object, **kwargs: object) -> None:
        """
        Log a message with severity 'FATAL'.

        Args:
            self (logging.Logger): Current logger instance.
            msg (str): The log message.
            *args (object): Positional arguments passed to logger.
            **kwargs (object): Keyword arguments passed to logger.

        Returns:
            None
        """
        if self.isEnabledFor(LogLevels.FATAL):
            self._log(LogLevels.FATAL, msg, args, **kwargs)

    # 4. Attach fatal method to Logger class if not already present
    if not hasattr(logging.Logger, "fatal"):
        setattr(logging.Logger, "fatal", fatal)

    # 5. Mark as installed
    _installed = True
