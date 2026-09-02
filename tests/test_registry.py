# ====== Code Summary ======
# Coverage for the process-global auto-width registry: monotonic max tracking,
# the width floor, and identifier pre-seeding.

from __future__ import annotations

# ====== Local Project Imports ======
from loggerplusplus.registry import (
    _AUTO,
    _IDENTIFIER_SPEC,
    _AutoWidthRegistry,
    register_identifier,
)


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
