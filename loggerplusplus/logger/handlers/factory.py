# ====== Code Summary ======
# This module defines `HandlerFactory`, which provides a factory method for
# creating safe rotating file handlers with directory creation, UTF-8 encoding,
# and managed rollover settings.

# ====== Standard Library Imports ======
import os
import logging

# ====== Local Project Imports ======
from .safe_rotating import SafeRotatingFileHandler


class HandlerFactory:
    """
    Factory class for creating pre-configured logging handlers.
    """

    @staticmethod
    def file_for_path(path: str, cfg: object) -> logging.Handler:
        """
        Create a rotating file handler with safe rollover, UTF-8 encoding,
        and automatic parent directory creation.

        Args:
            path (str): Path to the log file.
            cfg (object): Configuration object with optional attributes:
                - max_bytes (int): Maximum file size before rollover.
                - backup_count (int): Number of backup files to keep.
                - encoding (str): File encoding (default: "utf-8").
                - errors (str): Error handling strategy (default: "replace").

        Returns:
            logging.Handler: Configured file handler.
        """
        # 1. Ensure parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 2. Extract configuration with fallbacks
        max_bytes = getattr(cfg, "max_bytes", 0) or 0
        backup_count = getattr(cfg, "backup_count", 0) or 0
        enc = getattr(cfg, "encoding", "utf-8") or "utf-8"
        errs = getattr(cfg, "errors", "replace") or "replace"

        # 3. Create safe rotating file handler
        h = SafeRotatingFileHandler(
            path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=enc,
            errors=errs,
            delay=True,
        )

        # 4. Mark handler as managed by logging-plus-plus
        setattr(h, "_lpp_managed", True)
        return h
