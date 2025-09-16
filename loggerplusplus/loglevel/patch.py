import logging
from .log_level import LogLevels


def _bump(sl, add, default):
    if sl is None:
        return default
    try:
        return int(sl) + add
    except Exception:
        return default


def _logger_fatal(self: logging.Logger, msg, *args, **kwargs):
    """
    Instance method: logger.fatal(...)
    Call chain: user -> Logger.fatal(wrapper) -> _LPPLogger._log -> logging
    We must skip both our wrapper and _LPPLogger._log.
    """
    sl = kwargs.pop("stacklevel", None)
    eff = _bump(sl, add=2, default=3)  # default 3, or +2 if user gave one
    # Use self._log to keep your LPP features (duplication, etc.)
    self._log(LogLevels.FATAL, msg, args, stacklevel=eff, **kwargs)


def _root_fatal(msg, *args, **kwargs):
    """
    Module-level: logging.fatal(...)
    Call chain: user -> _root_fatal(wrapper) -> logging.root.log -> logging
    We must skip our wrapper only (logging.* is auto-skipped).
    """
    if len(logging.root.handlers) == 0:
        logging.basicConfig()
    sl = kwargs.pop("stacklevel", None)
    eff = _bump(sl, add=1, default=2)  # default 2, or +1 if user gave one
    logging.root.log(LogLevels.FATAL, msg, *args, stacklevel=eff, **kwargs)


def install_fatal_level() -> None:
    # register level name/number
    if logging.getLevelName(int(LogLevels.FATAL)) != "FATAL":
        logging.addLevelName(int(LogLevels.FATAL), "FATAL")
    if not hasattr(logging, "FATAL"):
        logging.FATAL = int(LogLevels.FATAL)

    # override both entry points
    logging.Logger.fatal = _logger_fatal  # type: ignore[attr-defined]
    logging.fatal = _root_fatal  # type: ignore[attr-defined]
