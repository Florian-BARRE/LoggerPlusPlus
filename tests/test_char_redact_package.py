# ====== Code Summary ======
# Structure-resolves check for the R-03 carve-out: the redaction/truncation helpers and
# SENSITIVE_KEYS moved from decorators.py into the new brick src/loggerplusplus/redact.py.
# This test is behaviour-preserving; it only documents that the moved units resolve from their
# new home and that the `Redact` tool class's staticmethods ARE the same objects as the
# module-level helpers (no duplicated logic), plus one end-to-end redaction to pin the shape.

from __future__ import annotations

from loggerplusplus import SENSITIVE_KEYS as TOP_LEVEL_SENSITIVE_KEYS
from loggerplusplus.redact import (
    SENSITIVE_KEYS,
    Redact,
    _deep_redact,
    _is_sensitive,
    _redact_call,
    _shorten,
    _shorten_args,
    _shorten_kwargs,
)


def test_redact_exposes_six_staticmethods() -> None:
    """Redact exposes the six expected staticmethod names, all callable."""
    for name in (
        "is_sensitive",
        "deep_redact",
        "redact_call",
        "shorten",
        "shorten_args",
        "shorten_kwargs",
    ):
        assert callable(getattr(Redact, name))


def test_redact_methods_are_the_module_helpers() -> None:
    """Each Redact staticmethod is the same object as the module-level helper (no dup logic)."""
    assert Redact.is_sensitive is _is_sensitive
    assert Redact.deep_redact is _deep_redact
    assert Redact.redact_call is _redact_call
    assert Redact.shorten is _shorten
    assert Redact.shorten_args is _shorten_args
    assert Redact.shorten_kwargs is _shorten_kwargs


def test_sensitive_keys_single_source_of_truth() -> None:
    """The redact SENSITIVE_KEYS is the SAME object as the frozen top-level one, with the keys."""
    assert SENSITIVE_KEYS is TOP_LEVEL_SENSITIVE_KEYS
    for key in ("password", "token", "secret"):
        assert key in SENSITIVE_KEYS


def test_redact_call_masks_sensitive_kwargs() -> None:
    """End-to-end: a kwarg named `password` is masked to '***'; a plain arg is kept."""

    def login(user: str, password: str) -> bool:
        return True

    shown_args, shown_kwargs = Redact.redact_call(
        login, ("bob",), {"password": "x"}, SENSITIVE_KEYS
    )
    assert shown_kwargs == {"password": "***"}
    assert shown_args == ("bob",)
