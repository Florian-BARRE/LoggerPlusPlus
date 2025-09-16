# ====== Code Summary ======
# This module defines `LoggerPlusPlus`, a custom subclass of `logging.Logger`
# that extends the standard logging behavior. It adds support for duplicating
# log messages into specific per-file outputs, and introduces a configurable
# fast/default stacklevel policy.

# ====== Standard Library Imports ======
from __future__ import annotations
import logging

# ====== Internal Project Imports ======
from ..config.file import FileConfig
from .handlers import HandlerFactory


class _LPPLogger(logging.Logger):
    """
    Enhanced logger with support for:
      - Fast/default stacklevel policy.
      - Duplicating log messages into specific per-file outputs.
    """


    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        super().__init__(name, level)
        # Safe defaults; will be overwritten by the manager right after creation.
        self._lpp_default_stacklevel: int = 2
        self._lpp_fast_stacklevel: bool = False
        self._lpp_filecfg = None
        self._lpp_file_formatter = None

    def _duplicate_to_specific(
            self,
            message: str,
            filecfg: FileConfig,
            formatter: logging.Formatter,
            name: str,
    ) -> None:
        """
        Write a message to a specific log file with the given formatter.

        Args:
            message (str): The log message to write.
            filecfg (FileConfig): File configuration including log directory.
            formatter (logging.Formatter): Formatter for the log record.
            name (str): Target file name (without extension).
        """
        path = f"{filecfg.log_dir}/{name}.log"
        h = HandlerFactory.file_for_path(path, filecfg)
        h.setFormatter(formatter)

        try:
            # 1. Create a record and emit it directly
            rec = self.makeRecord(
                self.name,
                self.level,
                fn="",
                lno=0,
                msg=message,
                args=(),
                exc_info=None,
            )
            h.emit(rec)
        finally:
            # 2. Ensure handler is closed after use
            h.close()

    def _log(
            self,
            level,
            msg,
            args,
            exc_info=None,
            extra=None,
            stack_info: bool = False,
            stacklevel: int | None = None,
            **kwargs,
    ) -> None:
        """
        Core logging method override with support for fast/default stacklevel
        policies and per-file duplication.
        """
        # 1) Decide effective stacklevel
        if stacklevel is None:
            # Your existing policy: fast vs default
            if getattr(self, "_lpp_fast_stacklevel", False):
                eff_stacklevel = 1
            else:
                # keep your default (2 is a good default for "logger.X" helpers)
                eff_stacklevel = int(getattr(self, "_lpp_default_stacklevel", 2))
        else:
            try:
                eff_stacklevel = int(stacklevel)
            except Exception:
                eff_stacklevel = 2

        # 2) Optional: read & pop your extra kwargs
        specific = kwargs.pop("specific_file_name", None)

        # 3) Delegate to stdlib with the effective stacklevel
        super()._log(level, msg, args, exc_info, extra, stack_info, eff_stacklevel)

        # 4) Duplicate to specific file if requested (unchanged)
        if specific:
            filecfg = getattr(self, "_lpp_filecfg", None)
            formatter = getattr(self, "_lpp_file_formatter", None)
            if filecfg and formatter:
                payload = str(msg) if not args else str(msg) % args
                self._duplicate_to_specific(payload, filecfg, formatter, specific)