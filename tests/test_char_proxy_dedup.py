# ====== Code Summary ======
# Characterization test for ticket R-04 (proxy dedup, Wave 3): the single
# source of truth for "logger-returning" method names is now the public
# `transform_proxy.LOGGER_RETURNING` constant, shared by BOTH proxy modules.
#
# Before R-04 the same `frozenset({"bind", "patch"})` was duplicated:
#   * `transform_proxy._LOGGER_RETURNING` (used by `TransformProxy.__getattr__`)
#   * `proxy._WRAP_RETURNING`            (used by `LoggerPlusPlus.__getattr__`)
# R-04 renamed the first to `LOGGER_RETURNING` (public, in `__all__`) and
# deleted the second, which now imports it. These tests pin that the dedup is
# byte-identical in behaviour: the same constant is used by both proxies, its
# value is unchanged, and `bind`/`patch` still re-wrap exactly as before.

from __future__ import annotations

from typing import Any

from loguru import logger

from loggerplusplus import loggerplusplus as singleton
from loggerplusplus.proxy import LOGGER_RETURNING as PROXY_LOGGER_RETURNING
from loggerplusplus.transform_proxy import (
    LEVEL_METHODS,
    LOGGER_RETURNING,
    TransformProxy,
)


def test_logger_returning_is_importable_and_public() -> None:
    """`LOGGER_RETURNING` is importable from `transform_proxy` and in its `__all__`."""
    from loggerplusplus import transform_proxy

    assert "LOGGER_RETURNING" in transform_proxy.__all__
    assert transform_proxy.LOGGER_RETURNING is LOGGER_RETURNING


def test_logger_returning_value_unchanged() -> None:
    """The constant still names exactly the logger-returning methods `bind`/`patch`."""
    assert LOGGER_RETURNING == frozenset({"bind", "patch"})
    # `opt` was deliberately never wrapped; it must remain excluded.
    assert "opt" not in LOGGER_RETURNING


def test_proxy_shares_the_same_constant_object() -> None:
    """`proxy.py` no longer carries its own copy: it uses the very same object."""
    assert PROXY_LOGGER_RETURNING is LOGGER_RETURNING


def test_singleton_bind_returns_a_transform_proxy() -> None:
    """The singleton's `bind` re-wraps: a NEW TransformProxy, not the singleton."""
    bound = singleton.bind(x=1)
    assert isinstance(bound, TransformProxy)
    assert bound is not singleton  # a bound logger is a fresh wrapper


def test_singleton_patch_returns_a_transform_proxy() -> None:
    """`patch` is in the shared set too: it re-wraps just like `bind`."""
    patched = singleton.patch("extra = {'dedup': True}")
    assert isinstance(patched, TransformProxy)
    assert patched is not singleton


def test_bound_level_methods_still_gain_transform_keyword(cap: Any) -> None:
    """Behaviour pin: a bound logger's level methods still gain `transform=`/`raw=`."""
    cap.add(fmt="{message}")
    bound = singleton.bind(identifier="DEDUP_KW")
    assert isinstance(bound, TransformProxy)
    bound.info("hello", transform=str.upper)
    assert cap.text == "HELLO\n"


def test_transform_proxy_forwards_bind_and_rewraps() -> None:
    """`TransformProxy.__getattr__("bind")` returns a TransformProxy, not a raw loguru Logger."""
    bound = TransformProxy(logger).bind(x=1)
    assert isinstance(bound, TransformProxy)
    assert type(bound) is not type(logger)  # not a bare loguru Logger


def test_opt_is_not_rewrapped() -> None:
    """`opt` is NOT in `LOGGER_RETURNING`: it stays loguru's, un-wrapped (non-regression)."""
    opted = TransformProxy(logger).opt(colors=True)
    assert not isinstance(opted, TransformProxy)
    assert type(opted) is type(logger)  # a plain loguru Logger


def test_level_methods_set_untouched() -> None:
    """The dedup only concerns logger-returning names; `LEVEL_METHODS` is unchanged."""
    assert LEVEL_METHODS == frozenset(
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
