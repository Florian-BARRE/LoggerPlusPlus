# ====== Code Summary ======
# Coverage for the process-global auto-width registry: monotonic max tracking,
# the width floor, and identifier pre-seeding. Also the public registry controls:
# bounded growth (set_max_auto_width), reset (reset_widths), and introspection
# (observed_widths), plus their effect through the rendering pipeline.

from __future__ import annotations

# ====== Standard Library Imports ======
from typing import Any, Dict

# ====== Third-Party Imports ======
import pytest

# ====== Local Project Imports ======
from loggerplusplus import (
    observed_widths,
    reset_widths,
    set_max_auto_width,
)
from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.registry import (
    _AUTO,
    _IDENTIFIER_SPEC,
    _AutoWidthRegistry,
    register_identifier,
)
from loggerplusplus.runtime import compose_filter


def test_observe_tracks_maximum() -> None:
    """`observe` keeps the longest value seen for a spec."""
    reg = _AutoWidthRegistry()
    reg.observe("f", "abc")
    reg.observe("f", "abcdef")
    assert reg.width("f") == 6


def test_width_never_shrinks() -> None:
    """A shorter later value does not reduce the observed maximum."""
    reg = _AutoWidthRegistry()
    reg.observe("f", "abcdef")
    reg.observe("f", "x")
    assert reg.width("f") == 6


def test_unknown_spec_has_floor_of_one() -> None:
    """An unobserved spec reports a minimum width of 1, never 0."""
    reg = _AutoWidthRegistry()
    assert reg.width("never-seen") == 1


def test_none_observation_is_empty_string() -> None:
    """Observing None counts as width 0, so the floor of 1 still applies."""
    reg = _AutoWidthRegistry()
    reg.observe("f", None)
    assert reg.width("f") == 1


def test_register_identifier_seeds_global_registry() -> None:
    """`register_identifier` pre-seeds the shared registry for early alignment."""
    register_identifier("WorkerService")
    assert _AUTO.width(_IDENTIFIER_SPEC) >= len("WorkerService")


def test_register_identifier_handles_empty() -> None:
    """An empty identifier seeds the '-' sentinel without error."""
    register_identifier("")
    assert _AUTO.width(_IDENTIFIER_SPEC) >= 1


@pytest.fixture(autouse=True)
def _clean_registry() -> Any:
    """Reset registry state and remove any global cap around each test."""
    reset_widths()
    set_max_auto_width(None)
    yield
    reset_widths()
    set_max_auto_width(None)


def _render(token: str, value: str) -> str:
    """Render one auto token for `value` and return the placeholder."""
    _fmt, mappings = prepare_auto_format(token)
    rec: Dict[str, Any] = {"extra": {"x": value}}
    compose_filter(None, mappings)(rec)
    return rec["extra"]["__lp_auto_0__"]


def test_observed_widths_reports_and_reset_clears() -> None:
    """observed_widths reflects growth; reset_widths clears it back to empty."""
    _render("{extra[x]:<auto}", "abcdef")
    # snapshot keys are canonical: extra[x] -> x
    assert observed_widths().get("x") == 6
    reset_widths()
    assert observed_widths() == {}


def test_reset_widths_lets_a_column_shrink() -> None:
    """After a one-off huge value, reset lets the column re-grow from scratch."""
    _render("{extra[x]:<auto}", "X" * 40)
    assert observed_widths().get("x") == 40
    reset_widths()
    out = _render("{extra[x]:<auto}", "ab")
    assert out == "ab"  # width re-grown to 2, not padded to 40


def test_set_max_auto_width_caps_growth() -> None:
    """A global cap bounds auto widths even when a longer value is observed."""
    set_max_auto_width(8)
    out = _render("{extra[x]:<auto}", "X" * 40)
    assert out == "X" * 8  # observed 40 but capped and hard-cut to 8


def test_max_auto_width_none_removes_cap() -> None:
    """Clearing the cap restores unbounded growth."""
    set_max_auto_width(5)
    set_max_auto_width(None)
    out = _render("{extra[x]:<auto}", "abcdefgh")
    assert out == "abcdefgh"


def test_set_max_auto_width_rejects_zero() -> None:
    """A cap below 1 is rejected."""
    with pytest.raises(ValueError):
        set_max_auto_width(0)


def test_register_identifier_shows_in_snapshot() -> None:
    """register_identifier seeds the canonical `identifier` bucket."""
    register_identifier("WorkerService")
    assert observed_widths().get("identifier") >= len("WorkerService")


def test_registry_width_query_honors_cap() -> None:
    """The direct width() query applies the global cap to the observed maximum."""
    from loggerplusplus.registry import _AutoWidthRegistry

    reg = _AutoWidthRegistry()
    reg.observe("f", "abcdefghij")  # 10
    assert reg.width("f") == 10
    reg.set_max_width(4)
    assert reg.width("f") == 4
