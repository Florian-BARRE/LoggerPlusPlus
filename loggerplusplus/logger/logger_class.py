# ====== Code Summary ======
# This module defines `LoggerClass`, a mixin that automatically attaches a
# configured logger to classes. It supports class-level and instance-level
# configuration, cooperative `__init__` usage, and integrates with
# `LoggerManager` for flexible logger creation and management.

# ====== Standard Library Imports ======
from __future__ import annotations
from typing import Callable, Any
from copy import deepcopy
import logging

# ====== Local Project Imports ======
from .manager import LoggerManager
from ..config.core import LoggerConfig


class LoggerClass:
    """
    Mixin that auto-attaches a logger with flexible injection options.

    Injection strategies:
        • **Class-level hints**:
            - __logger_identifier__ : str | None
            - __logger_config__     : LoggerConfig | Callable[[], LoggerConfig] | None
            - __logger_instance__   : logging.Logger | None

        • **Instance-level cooperative `__init__` kwargs**:
            - lpp_identifier       : str | None
            - lpp_logger_config    : LoggerConfig | None
            - lpp_logger           : logging.Logger | None

    Precedence (highest → lowest):
        1. lpp_logger (kwarg or set_logger) or __logger_instance__
        2. lpp_logger_config (kwarg or set_logger_config) or __logger_config__
        3. Global default config (via LoggerManager.get_default_config, cloned)
        4. Fallback: logging.getLogger(identifier)

    Identifier resolution:
        - From lpp_identifier kwarg.
        - From __logger_identifier__ (class attr).
        - Defaults to class name.

    Cooperative design:
        - Consumes its lpp_* kwargs.
        - Forwards the rest to super().__init__.
    """
    logger: logging.Logger

    # -------- Class-level knobs -------- #
    __logger_identifier__: str | None = None
    __logger_config__: LoggerConfig | Callable[[], LoggerConfig] | None = None
    __logger_instance__: logging.Logger | None = None

    # -------- Instance-level overrides -------- #
    _lpp_logger_override: logging.Logger | None = None
    _lpp_cfg_override: LoggerConfig | None = None
    _lpp_identifier_override: str | None = None

    # -------- Helpers -------- #
    def _resolved_identifier(self) -> str:
        """
        Resolve the identifier for the logger.

        Returns:
            str: The identifier (instance override, class-level hint, or class name).
        """
        if self._lpp_identifier_override:
            return self._lpp_identifier_override
        if getattr(self.__class__, "__logger_identifier__", None):
            return self.__class__.__logger_identifier__  # type: ignore[attr-defined]
        return self.__class__.__name__

    @classmethod
    def _resolve_class_logger(cls) -> logging.Logger:
        """Resolve logger from class-level definition."""
        return cls.__logger_instance__

    @classmethod
    def _resolve_class_config(cls) -> LoggerConfig | None:
        """Resolve logger config from class-level definition."""
        src = cls.__logger_config__
        if src is None:
            return None
        cfg = src() if callable(src) else src
        if cfg is None:
            return None
        return deepcopy(cfg)

    # -------- Public setters -------- #
    def set_logger(self, logger: logging.Logger) -> None:
        """
        Override the logger instance at runtime.

        Args:
            logger (logging.Logger): The logger to attach.
        """
        self._lpp_logger_override = logger
        self.logger = logger

    def set_logger_config(self, cfg: LoggerConfig) -> None:
        """
        Override the logger configuration at runtime.

        Args:
            cfg (LoggerConfig): The logger configuration to apply.
        """
        self._lpp_cfg_override = deepcopy(cfg)
        self.logger = None  # type: ignore[assignment]
        self._attach_logger()

    # -------- Core attach -------- #
    def _attach_logger(self) -> None:
        """
        Attach a logger to the instance using precedence rules.
        """
        ident = self._resolved_identifier()

        # 1. Explicit logger (instance or class)
        logger = self._lpp_logger_override or self._resolve_class_logger()
        if logger is not None:
            self.logger = logger
            return

        # 2. Explicit config (instance or class)
        cfg = self._lpp_cfg_override or self._resolve_class_config()
        if cfg is not None:
            cfg = deepcopy(cfg)
            cfg.identifier = ident
            self.logger = LoggerManager.get(cfg)
            return

        # 3. Global default config
        base = LoggerManager.get_default_config()
        if base is not None:
            cfg2 = deepcopy(base)
            cfg2.identifier = ident
            self.logger = LoggerManager.get(cfg2)
            return

        # 4. Fallback
        self.logger = logging.getLogger(ident)

    # -------- Cooperative __init__ -------- #
    def __init__(self, *args: Any, **kwargs: Any):
        """
        Initialize the mixin, consuming lpp_* kwargs and attaching a logger.

        Args:
            *args (Any): Positional arguments for cooperative init.
            **kwargs (Any): Keyword arguments including optional lpp_* overrides.
        """
        # 1. Extract cooperative kwargs
        self._lpp_identifier_override = kwargs.pop("lpp_identifier", None)
        logger_kw = kwargs.pop("lpp_logger", None)
        cfg_kw = kwargs.pop("lpp_logger_config", None)

        if logger_kw is not None and isinstance(logger_kw, logging.Logger):
            self._lpp_logger_override = logger_kw
        if cfg_kw is not None and isinstance(cfg_kw, LoggerConfig):
            self._lpp_cfg_override = deepcopy(cfg_kw)

        # 2. Attach resolved logger before parent init
        self._attach_logger()

        # 3. Continue init chain (safe for mixins)
        try:
            super().__init__(*args, **kwargs)  # type: ignore[misc]
        except Exception:
            # Parent may not define __init__ or may have incompatible signature
            pass
