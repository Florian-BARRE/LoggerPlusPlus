# ====== Code Summary ======
# Coverage for the LoggerPlusPlus proxy: override dispatch for the intercepted
# names, transparent __getattr__ forwarding to loguru, __dir__, __repr__, and
# the __call__ passthrough to the core logger.

from __future__ import annotations

from loguru import logger

from loggerplusplus import LoggerPlusPlus, loggerplusplus
from loggerplusplus.api import add as add_override
from loggerplusplus.decorators import catch, log_io, log_timing, opt


def test_overridden_names_return_project_implementations() -> None:
    """The intercepted names resolve to this project's helpers, not loguru's."""
    assert loggerplusplus.add is add_override
    assert loggerplusplus.catch is catch
    assert loggerplusplus.opt is opt
    assert loggerplusplus.log_io is log_io
    assert loggerplusplus.log_timing is log_timing


def test_unknown_attribute_forwards_to_loguru(cap: "object") -> None:
    """A non-overridden attribute is forwarded to the underlying loguru logger."""
    # `.level` is a native loguru method, only reachable through forwarding.
    info_level = loggerplusplus.level("INFO")
    assert info_level.name == "INFO"
    # `.bind` is also forwarded; the bound identifier surfaces in the output.
    cap.add(fmt="{extra[identifier]} {message}")
    loggerplusplus.bind(identifier="XPROXY").info("via proxy")
    assert "XPROXY via proxy" in cap.text


def test_dir_exposes_both_proxy_and_core_names() -> None:
    """__dir__ merges the override names with the core logger's attributes."""
    names = dir(loggerplusplus)
    assert "add" in names
    assert "bind" in names


def test_repr_mentions_the_proxy() -> None:
    """__repr__ identifies the object as a LoggerPlusPlus proxy."""
    assert "LoggerPlusPlus proxy" in repr(loggerplusplus)


def test_call_forwards_to_core() -> None:
    """__call__ forwards to the core object, supporting a callable core."""
    proxy = LoggerPlusPlus(core=lambda *a, **k: ("called", a, k))
    assert proxy(1, x=2) == ("called", (1,), {"x": 2})


def test_default_core_is_the_global_logger() -> None:
    """A proxy built with no core wraps loguru's global logger."""
    assert LoggerPlusPlus()._core is logger
