# ====== Code Summary ======
# Cross-process auto-width alignment via export/import (audit item B10). The registry
# is process-local, so a child aligns to a parent's columns by importing the parent's
# width snapshot — proven here end-to-end with a real `spawn` child (the hard case:
# a spawned child starts with an empty registry, so import_widths is the only source).

from __future__ import annotations

import multiprocessing as mp
from typing import Any

from loggerplusplus import (
    import_widths,
    observed_widths,
    reset_widths,
    set_max_auto_width,
)
from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.registry import _AutoWidthRegistry
from loggerplusplus.runtime import compose_filter


def _render_id(value: str) -> str:
    """Render one auto identifier token for `value` in the current process."""
    _fmt, mappings = prepare_auto_format("{extra[id]:<auto}")
    rec = {"extra": {"id": value}}
    compose_filter(None, mappings)(rec)
    return rec["extra"]["__lp_auto_0__"]


def _child(snapshot: dict, queue: Any) -> None:
    """Child entrypoint: import the parent's widths, then render a short value."""
    import_widths(snapshot)
    queue.put(_render_id("X"))


def test_import_widths_merges_taking_max() -> None:
    """import via merge keeps the larger width and honors canonical keys."""
    reg = _AutoWidthRegistry()
    reg.observe("f", "abc")  # 3
    reg.merge({"f": 10, "extra[g]": 7})
    assert reg.width("f") == 10  # 10 > 3
    reg.merge({"f": 2})  # smaller ignored
    assert reg.width("f") == 10
    assert reg.width("g") == 7  # extra[g] canonicalized to g


def test_import_widths_aligns_a_spawned_child() -> None:
    """A spawned child (empty registry) aligns to the parent's column via import_widths."""
    reset_widths()
    set_max_auto_width(None)
    try:
        _render_id("LongIdentifier")  # parent observes width 14
        snapshot = observed_widths()
        assert snapshot.get("id") == 14

        ctx = mp.get_context("spawn")
        queue = ctx.Queue()
        proc = ctx.Process(target=_child, args=(snapshot, queue))
        proc.start()
        try:
            out = queue.get(timeout=30)
        finally:
            proc.join(30)
            if proc.is_alive():  # pragma: no cover - safety net for a hung child
                proc.terminate()
                proc.join(5)
        # The child padded its short "X" to the imported width of 14.
        assert out == "X" + " " * 13
    finally:
        reset_widths()
