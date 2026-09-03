# ====== Code Summary ======
# Regression tests for the confirmed bugs found in the deep audit. Each test is named
# after its finding so a re-introduction fails loudly with context.

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, Optional

import pytest

from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.registry import (
    _AUTO,
    _AutoWidthRegistry,
    register_identifier,
)
from loggerplusplus.runtime import compose_filter


def _record(
    name: str = "m",
    level_no: int = 20,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a minimal loguru-like record with a name, a level.no and an extra bag."""
    return {
        "name": name,
        "level": SimpleNamespace(no=level_no, name="INFO"),
        "extra": dict(extra or {}),
    }


# --- B1: dict filter must still apply when an auto-width token is present -------------


def test_b1_dict_filter_is_applied_with_auto_token() -> None:
    """A dict filter gates records even though the format has an auto-width token."""
    _fmt, mappings = prepare_auto_format("{identifier:<auto} {message}")
    flt = compose_filter({"": "INFO"}, mappings)

    # DEBUG (10) < INFO (20) -> rejected; INFO passes. The placeholder is still computed.
    debug_rec = _record(level_no=10, extra={"identifier": "X"})
    info_rec = _record(level_no=20, extra={"identifier": "X"})
    assert flt(debug_rec) is False
    assert flt(info_rec) is True
    assert "__lp_auto_0__" in info_rec["extra"]  # width side effect still ran


def test_b1_dict_filter_most_specific_prefix_wins() -> None:
    """The most specific module prefix decides, matching loguru's own semantics."""
    flt = compose_filter({"a.b": "WARNING", "": "DEBUG"}, [])
    # 'a.b.c' matches 'a.b' -> needs WARNING(30); INFO(20) is rejected.
    assert flt(_record(name="a.b.c", level_no=20)) is False
    # 'other' falls back to '' -> DEBUG(10); INFO(20) passes.
    assert flt(_record(name="other", level_no=20)) is True


def test_b1_dict_filter_false_disables_module() -> None:
    """A False value disables a module subtree entirely."""
    flt = compose_filter({"noisy": False}, [])
    assert flt(_record(name="noisy.worker", level_no=40)) is False
    assert flt(_record(name="quiet", level_no=10)) is True


def test_b1_dict_filter_true_enables_all_levels() -> None:
    """A True value maps to level 0 so every record passes."""
    flt = compose_filter({"mod": True}, [])
    assert flt(_record(name="mod.sub", level_no=5)) is True


# --- B2: an incidental space in the spec must not crash -------------------------------


def test_b2_whitespace_in_spec_is_tolerated() -> None:
    """`{identifier: <auto}` parses instead of leaking to loguru and raising KeyError."""
    new_fmt, mappings = prepare_auto_format("{identifier: <auto} | {message}")
    assert len(mappings) == 1
    assert mappings[0][0] == "identifier"
    assert "{extra[__lp_auto_0__]}" in new_fmt


# --- B3: register_identifier must feed the width used by the shipped (bare) token ------


def test_b3_register_identifier_reaches_bare_token_bucket() -> None:
    """Seeding via `extra[identifier]` widens the bare `identifier` bucket (canonicalized)."""
    register_identifier("A" * 21)
    assert _AUTO.width("identifier") >= 21
    assert _AUTO.width("extra[identifier]") == _AUTO.width("identifier")


def test_b3_first_line_is_aligned_to_registered_width() -> None:
    """A short first identifier is padded to a previously-registered longer identifier."""
    register_identifier("MuchLongerName")  # 14 chars
    _fmt, mappings = prepare_auto_format("{identifier:<auto}")
    flt = compose_filter(None, mappings)
    rec = _record(extra={"identifier": "X"})
    flt(rec)
    padded = rec["extra"]["__lp_auto_0__"]
    assert padded.startswith("X")
    assert len(padded) >= 14


# --- B5: escaped `{{ }}` token look-alikes must be left untouched ---------------------


def test_b5_escaped_braces_are_not_rewritten() -> None:
    """A doubled-brace escape is not matched, so no placeholder leaks into the output."""
    new_fmt, mappings = prepare_auto_format("{{identifier:<auto}} | {message}")
    assert mappings == []
    assert new_fmt == "{{identifier:<auto}} | {message}"


# --- canonicalization unit (supports B3) ----------------------------------------------


@pytest.mark.parametrize(
    "spec_a, spec_b",
    [("identifier", "extra[identifier]"), ("service", "extra[service]")],
)
def test_registry_canonicalizes_wrapped_and_bare(spec_a: str, spec_b: str) -> None:
    """Bare and `extra[...]` spellings of a field share one width bucket."""
    reg = _AutoWidthRegistry()
    reg.observe(spec_b, "abcdef")
    assert reg.width(spec_a) == 6
    assert reg.width(spec_b) == 6
