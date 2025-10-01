# ====== Code Summary ======
# This module provides a proxy wrapper `LoggerPlusPlus` around `loguru.logger`,
# enhancing it with additional features such as decorated logging utilities
# (`add`, `catch`, `opt`, `log_io`, `log_timing`). It enables seamless forwarding
# of all loguru functionality while selectively overriding specific behaviors.

from __future__ import annotations

# ====== Standard Library Imports ======
from typing import Any, Callable

# ====== Third-Party Library Imports ======
from loguru import logger as _core

# ====== Local Project Imports ======
from .decorators import catch, opt, log_io, log_timing
from .api import add


class LoggerPlusPlus:
    """
    A dynamic proxy wrapper around the `loguru.logger` object.

    This class acts as a transparent proxy for the underlying `loguru.logger`:
      - By default, `__getattr__` forwards attributes and methods to the loguru logger.
      - Certain method names (`'add'`, `'catch'`, `'opt'`, `'log_io'`, `'log_timing'`)
        are overridden with custom implementations provided by this project.
      - Overrides maintain simple `*args`/`**kwargs` signatures, avoiding duplication
        of upstream signatures.

    Attributes:
        _core (loguru.Logger): The underlying loguru logger instance.
    """

    __slots__ = ("_core",)

    def __init__(self, core: Any = None) -> None:
        """
        Initialize the LoggerPlusPlus instance.

        Args:
            core (Any, optional): An optional core logger to proxy.
                Defaults to the global loguru `logger`.
        """
        self._core = core or _core

    # ---- Dynamic routing table (no signature duplication) ---- #

    def _get_override(self, name: str) -> Callable | None:
        """
        Return an override function for selected method names.

        Args:
            name (str): The name of the method being requested.

        Returns:
            Callable | None: The override function if available; otherwise, None.
        """
        # Map of method names you want to intercept -> bound override
        return {
            "add": add,
            "catch": catch,
            "opt": opt,
            "log_io": log_io,
            "log_timing": log_timing,
        }.get(name)

    # ---- Core proxying ---- #

    def __getattr__(self, name: str) -> Any:
        """
        Forward attribute access to loguru, except for overridden names.

        This automatically covers logger methods such as `.debug`, `.info`,
        `.bind`, `.contextualize`, `.configure`, etc.

        Args:
            name (str): The attribute name being accessed.

        Returns:
            Any: The resolved attribute, either an override or from the core logger.
        """
        override = self._get_override(name)
        if override is not None:
            return override
        return getattr(self._core, name)

    def __dir__(self) -> list[str]:
        """
        Extend `dir()` to expose attributes from both the proxy and the core logger.

        Returns:
            list[str]: A sorted list of available attributes.
        """
        # Nice developer experience: expose both sets of attributes
        return sorted(set(dir(self._core)) | set(self.__class__.__dict__.keys()))

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation of the proxy.

        Returns:
            str: The representation string.
        """
        return f"<LoggerPlusPlus proxy of {self._core!r}>"

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Preserve callable behavior if someone calls the logger directly.

        This ensures fluent behavior is maintained, though it is rarely used.

        Args:
            *args (Any): Positional arguments to forward to the core logger.
            **kwargs (Any): Keyword arguments to forward to the core logger.

        Returns:
            Any: The result of calling the core logger.
        """
        return self._core(*args, **kwargs)


# Export a ready-to-use singleton, mirroring loguru usage
loggerplusplus: LoggerPlusPlus = LoggerPlusPlus()
