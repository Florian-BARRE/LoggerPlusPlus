# ====== Code Summary ======
# Internal, transparent wrapper that adds a `transform=` (and `raw=`) keyword to loguru's
# level methods (`.info`, `.debug`, ...) WITHOUT altering any other behaviour. It exists so a
# *bound* logger (`logger.bind(...)`, `LoggerClass.logger`) gains the transform keyword while
# `.catch`, `.opt`, `.bind`, ... keep their exact loguru semantics — the reason we do NOT reuse
# the project `LoggerPlusPlus` proxy here (that one overrides catch/opt/... against the GLOBAL
# logger, which would silently break a bound logger).

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

__all__: list[str] = ["emit_with_transform", "TransformProxy", "LEVEL_METHODS"]

# The loguru logging methods that accept a leading `message` and gain the `transform`/`raw` keyword.
LEVEL_METHODS: frozenset[str] = frozenset(
    {
        "trace",
        "debug",
        "info",
        "success",
        "warning",
        "error",
        "critical",
        "exception",
        "log",
    }
)

# Logger-returning methods whose result is re-wrapped so the transform keyword survives chaining.
# `opt` is deliberately NOT here: it stays loguru's own `opt`, so `logger.opt(...).info(...)`
# keeps exact loguru semantics (loguru's `opt` resets options, so wrapping it would be a trap).
_LOGGER_RETURNING: frozenset[str] = frozenset({"bind", "patch"})

# Number of Python frames between the user's call site and the loguru level method we invoke:
# the `__getattr__` lambda, then `emit_with_transform` itself. We pass this to loguru's
# `opt(depth=...)` so the record is attributed to the caller, not to this module — otherwise the
# shipped formats' `{name}`/`{line}` would point here. Because we never wrap loguru's `opt`, the
# `core` we opt on carries no user-set options, so this fresh `opt(...)` only sets the depth.
_CALLER_DEPTH: int = 2


def emit_with_transform(
    core: Any, name: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]
) -> Any:
    """
    Apply an optional `transform` to a level method's message, then emit via loguru.

    The `transform` and `raw` keywords are consumed here and never forwarded to loguru. The
    transform runs AFTER loguru-style argument substitution, so `info("{u}", u=x,
    transform=str.upper)` behaves as a caller intuitively expects. When `raw=True`, emission
    goes through loguru's `opt(raw=True)` so no timestamp/level prefix is prepended — the clean
    path for multi-line ASCII-art banners — and a trailing newline is ensured.

    Args:
        core (Any): The underlying loguru logger (bound or global).
        name (str): The level method name (one of `LEVEL_METHODS`).
        args (tuple): Positional args as passed by the caller (message first, or level+message
            for `log`).
        kwargs (dict): Keyword args as passed by the caller; `transform`/`raw` are popped out.

    Returns:
        Any: Whatever the underlying loguru method returns (normally None).
    """
    # 1. Consume our two reserved keywords; everything else stays loguru's.
    transform: Optional[Callable[[str], str]] = kwargs.pop("transform", None)
    raw: bool = bool(kwargs.pop("raw", False))

    # 2. Always emit through `opt(depth=...)` so the record is attributed to the caller, not to
    #    this wrapper (see `_CALLER_DEPTH`).
    emitter: Any = core.opt(depth=_CALLER_DEPTH, raw=raw)

    # 3. Fast path: no message rewriting, forward verbatim (loguru still does its own formatting).
    if transform is None and not raw:
        return getattr(emitter, name)(*args, **kwargs)

    # 4. Locate the message (the `log` method carries the level in front of it).
    if name == "log":
        level: Any = args[0]
        message: Any = args[1] if len(args) > 1 else ""
        rest: Tuple[Any, ...] = args[2:]
    else:
        level = None
        message = args[0] if args else ""
        rest = args[1:]

    # 5. Substitute loguru-style placeholders ourselves, then transform the final string. We
    #    substitute here (not via loguru) because the transformed string is emitted with no args.
    text: str = str(message)
    if rest or kwargs:
        text = text.format(*rest, **kwargs)
    if transform is not None:
        text = transform(text)

    # 6. In raw mode loguru prints the message verbatim, so guarantee a trailing newline.
    if raw and not text.endswith("\n"):
        text = text + "\n"
    if name == "log":
        return emitter.log(level, text)
    return getattr(emitter, name)(text)


class TransformProxy:
    """
    Transparent wrapper adding the `transform`/`raw` keyword to a loguru logger's level methods.

    Every attribute except the level methods is forwarded unchanged to the wrapped logger, so
    `.catch`, `.opt`, `.bind`, `.patch`, `.contextualize`, `.level`, ... keep their exact loguru
    behaviour. `bind` and `patch` are re-wrapped so the keyword remains available further down a
    call chain; `opt` is intentionally NOT re-wrapped (see the module header).

    Attributes:
        _core (Any): The wrapped loguru logger (bound or global).
    """

    __slots__ = ("_core",)

    _core: Any

    def __init__(self, core: Any) -> None:
        """
        Wrap a loguru logger.

        Args:
            core (Any): The loguru logger to proxy.
        """
        self._core = core

    def __getattr__(self, name: str) -> Any:
        """
        Forward attribute access to the wrapped logger, adding the transform keyword.

        Args:
            name (str): The attribute name being accessed.

        Returns:
            Any: A transform-aware callable for level methods, a re-wrapping callable for
                logger-returning methods, or the raw forwarded attribute otherwise.
        """
        # 1. Level methods gain the transform/raw keyword.
        if name in LEVEL_METHODS:
            core = self._core
            return lambda *a, **k: emit_with_transform(core, name, a, k)

        # 2. Everything else is forwarded verbatim (loguru semantics preserved).
        attr = getattr(self._core, name)

        # 3. Re-wrap logger-returning methods so the keyword survives chaining.
        if name in _LOGGER_RETURNING and callable(attr):
            return lambda *a, **k: TransformProxy(attr(*a, **k))
        return attr

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.

        Returns:
            str: The representation string.
        """
        return f"<TransformProxy of {self._core!r}>"
