"""
Logger Manager
==============

Single responsibility:
- Build and (re)configure LPP-backed loggers from a LoggerConfig.
- Guarantee that created loggers are instances of `_LPPLogger`.
- Keep a small in-process registry to avoid re-wiring handlers repeatedly.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from ..config.core import LoggerConfig
from ..formatter.factory import build_formatter
from .handlers import SafeStreamHandler, HandlerFactory
from .lpp_intern_logger import _LPPLogger


class LoggerManager:
    """
    Manager for `_LPPLogger` instances.

    Public API:
        - set_default_config(cfg)
        - get_default_config()
        - get(cfg)         -> logging.Logger (instance of _LPPLogger)
        - reconfigure(cfg) -> logging.Logger

    Implementation notes:
    - We *never* leave `logging.setLoggerClass(...)` globally overridden.
    - We cache loggers by identifier to avoid duplicate handler wiring.
    """

    _registry: dict[str, logging.Logger] = {}
    _default_cfg: LoggerConfig | None = None

    # ----------------------------- Defaults ------------------------------ #

    @classmethod
    def set_default_config(cls, cfg: LoggerConfig) -> None:
        """Store a default configuration (optional convenience)."""
        cls._default_cfg = cfg

    @classmethod
    def get_default_config(cls) -> LoggerConfig | None:
        """Return the stored default configuration, if any."""
        return cls._default_cfg

    # --------------------------- Public Methods -------------------------- #

    @classmethod
    def get(cls, cfg: LoggerConfig) -> logging.Logger:
        """
        Get or create a logger configured according to the given `LoggerConfig`.
        Ensures the concrete type is `_LPPLogger` and wires handlers exactly
        as specified by the configuration.
        """
        name = cfg.identifier

        # Fast path: already built and cached by this manager.
        if name in cls._registry:
            return cls._registry[name]

        # Create a fresh `_LPPLogger` safely (no global side effects).
        logger = cls._new_lpp_logger(name)
        logger.setLevel(min(cfg.levels.console_level, cfg.levels.file_level))

        # Wire handlers/formatters and runtime options.
        cls._apply_handlers(logger, cfg)
        logger.propagate = cfg.propagate

        # Cache for subsequent calls.
        cls._registry[name] = logger
        return logger

    @classmethod
    def reconfigure(cls, cfg: LoggerConfig) -> logging.Logger:
        """
        Reconfigure an existing logger with a new configuration. If not present,
        behaves like `get(cfg)`.
        """
        logger = cls.get(cfg)
        logger.setLevel(min(cfg.levels.console_level, cfg.levels.file_level))
        cls._apply_handlers(logger, cfg)
        logger.propagate = cfg.propagate
        return logger

    # -------------------------- Internal Helpers ------------------------- #

    @staticmethod
    def _apply_handlers(logger: logging.Logger, cfg: LoggerConfig) -> None:
        """
        Apply handlers to a logger based on the provided configuration.

        Steps:
          1) Remove previously managed handlers.
          2) Build console/file formatters (file formatter without colors).
          3) Add console handler if enabled.
          4) Add file handlers (routing & naming) if enabled.
          5) Persist references required for on-demand duplication.
          6) Configure stacklevel strategy.
        """
        # 1) Remove previously managed handlers
        for h in list(logger.handlers):
            if getattr(h, "_lpp_managed", False):
                logger.removeHandler(h)

        # 2) Prepare formatters
        console_formatter = build_formatter(cfg.fmt) if cfg.fmt else None
        file_formatter = None
        if cfg.fmt:
            fmt = cfg.fmt
            fmt_no_color = replace(
                fmt,
                layout_model=fmt.layout_model,
                color_scheme=fmt.color_scheme,
                time_format=fmt.time_format,
                template=fmt.template,
                extra_placeholders=fmt.extra_placeholders,
                rules=fmt.rules,
                enable_level_color=False,
                enable_token_color=False,
                separators=fmt.separators,
            )
            file_formatter = build_formatter(fmt_no_color)

        # 3) Console handler
        if cfg.outputs.enable_console:
            sh = SafeStreamHandler()
            if console_formatter:
                sh.setFormatter(console_formatter)
            sh._lpp_managed = True  # mark so we can cleanly remove later
            logger.addHandler(sh)

        # 4) File handlers
        if cfg.outputs.enable_file and cfg.files:
            targets = cfg.files.get_file_targets(cfg.identifier, logger_name=logger.name)
            for t in targets:
                fh = HandlerFactory.file_for_path(str(t), cfg.files)
                if file_formatter:
                    fh.setFormatter(file_formatter)
                fh._lpp_managed = True
                logger.addHandler(fh)

        # 5) Save references used by `_LPPLogger` for specific-file duplication
        setattr(logger, "_lpp_filecfg", cfg.files)
        if file_formatter:
            setattr(logger, "_lpp_file_formatter", file_formatter)

        # 6) Stacklevel tuning
        try:
            setattr(logger, "_lpp_default_stacklevel", int(getattr(cfg, "default_stacklevel", 2)))
            setattr(logger, "_lpp_fast_stacklevel", bool(getattr(cfg, "fast_stacklevel", False)))
        except Exception:
            # Stay resilient; tuning is optional.
            pass

    @staticmethod
    def _new_lpp_logger(name: str) -> logging.Logger:
        """
        Create (or recreate) a logger named `name` as an instance of `_LPPLogger`,
        without leaving the global logger class overridden.

        If the stdlib logging registry already contains a logger with that name but
        of the wrong class, it is removed so a fresh `_LPPLogger` can be created.
        """
        prev_cls = logging.getLoggerClass()
        try:
            # If a logger with this name exists but isn't our subclass, drop it.
            existing = logging.root.manager.loggerDict.get(name)
            if isinstance(existing, logging.Logger) and not isinstance(existing, _LPPLogger):
                for h in list(existing.handlers):
                    existing.removeHandler(h)
                try:
                    del logging.root.manager.loggerDict[name]
                except KeyError:
                    pass

            # Temporarily set our class for the next creation
            logging.setLoggerClass(_LPPLogger)
            logger = logging.getLogger(name)  # will be an _LPPLogger
        finally:
            # Always restore the previous logger class to avoid global side-effects
            logging.setLoggerClass(prev_cls)

        return logger
