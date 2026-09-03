# ====== Code Summary ======
# This module provides a proxy wrapper `LoggerPlusPlus` around `loguru.logger`,
# enhancing it with additional features such as decorated logging utilities
# (`add`, `catch`, `opt`, `log_io`, `log_timing`). It enables seamless forwarding
# of all loguru functionality while selectively overriding specific behaviors.

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger as _core

from .api import add
from .decorators import catch, log_io, log_timing, opt

# Method names intercepted by the proxy, mapped to their project override. Hoisted to a
# module-level constant so `__getattr__` reads it instead of rebuilding the dict on every
# attribute miss (i.e. on every `.info()`/`.debug()` call).
_OVERRIDES: dict[str, Callable[..., Any]] = {
    "add": add,
    "catch": catch,
    "opt": opt,
    "log_io": log_io,
    "log_timing": log_timing,
}


class LoggerPlusPlus:
    """
    A dynamic proxy wrapper around the `loguru.logger` object.

    This class acts as a transparent proxy for the underlying `loguru.logger`:
      - By default, `__getattr__` forwards attributes and methods to the loguru logger.
      - Certain method names (`'add'`, `'catch'`, `'opt'`, `'log_io'`, `'log_timing'`)
        are overridden with custom implementations provided by this project.
      - Overrides maintain simple `*args`/`**kwargs` signatures, avoiding duplication
        of upstream signatures.

    Note:
        The override functions operate on the process-global loguru logger; passing a
        custom `core` only changes forwarded attribute access (`.info`, `.bind`, ...),
        not the overrides (`add`/`catch`/`opt`/`log_io`/`log_timing`).

    Attributes:
        _core (loguru.Logger): The underlying loguru logger instance.
    """

    __slots__ = ("_core",)

    # Annotated as Any: the core may be the loguru logger or any duck-typed logger/callable.
    _core: Any

    def __init__(self, core: Any = None) -> None:
        """
        Initialize the LoggerPlusPlus instance.

        Args:
            core (Any, optional): An optional core logger to proxy.
                Defaults to the global loguru `logger`.
        """
        self._core = core or _core

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
        override = _OVERRIDES.get(name)
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
        Forward a direct call to the core, when the core is itself callable.

        The default core is loguru's `logger`, which is NOT callable, so calling the
        singleton raises a clear `TypeError` (use a logging method like `.info(...)`).
        A custom callable core is forwarded to transparently.

        Args:
            *args (Any): Positional arguments to forward to the core.
            **kwargs (Any): Keyword arguments to forward to the core.

        Returns:
            Any: The result of calling the core.

        Raises:
            TypeError: If the underlying core is not callable.
        """
        core = self._core
        if not callable(core):
            raise TypeError(
                f"{type(self).__name__} object is not callable; "
                f"use a logging method such as .info(...) / .debug(...) instead"
            )
        return core(*args, **kwargs)


# Export a ready-to-use singleton, mirroring loguru usage
loggerplusplus: LoggerPlusPlus = LoggerPlusPlus()
