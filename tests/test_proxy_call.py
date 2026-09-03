# ====== Code Summary ======
# Proxy edge cases not covered elsewhere: the __call__ contract (B4) and attribute
# forwarding for a genuinely missing name.

from __future__ import annotations

import pytest

from loggerplusplus import loggerplusplus
from loggerplusplus.proxy import LoggerPlusPlus


def test_calling_singleton_raises_clear_typeerror() -> None:
    """B4: the default core (loguru logger) is not callable, so calling raises a clear error."""
    with pytest.raises(TypeError, match="not callable"):
        loggerplusplus("nope")


def test_call_forwards_to_a_callable_core() -> None:
    """A custom callable core is forwarded to transparently."""
    proxy = LoggerPlusPlus(core=lambda *a, **k: ("called", a, k))
    assert proxy("x", y=1) == ("called", ("x",), {"y": 1})


def test_missing_attribute_raises_attributeerror() -> None:
    """A name that is neither an override nor a loguru attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = loggerplusplus.definitely_not_a_logger_method
