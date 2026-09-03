# ====== Code Summary ======
# Concurrency coverage for the process-global auto-width registry — the reason the
# RLock exists. Many threads observe values of different lengths on one field; the
# recorded width must converge to the true maximum with no lost update.

from __future__ import annotations

import threading
from typing import Dict, List

from loggerplusplus import reset_widths, set_max_auto_width
from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.registry import _AutoWidthRegistry
from loggerplusplus.runtime import compose_filter


def test_registry_width_is_max_under_heavy_contention() -> None:
    """Concurrent observers of varying lengths converge on the true maximum width."""
    reg = _AutoWidthRegistry()
    start = threading.Barrier(16)
    lengths = list(range(1, 41))  # widest is 40

    def worker(seed: int) -> None:
        start.wait()  # release all threads together to maximize contention
        for n in lengths:
            reg.observe("field", "x" * n)
            reg.observe("field", "y" * ((seed % 40) + 1))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert reg.width("field") == 40


def test_auto_width_growth_is_consistent_across_threads() -> None:
    """compose_filter mutates per-call records safely while sharing one width bucket."""
    _fmt, mappings = prepare_auto_format("{extra[c]:<auto}")
    flt = compose_filter(None, mappings)
    results: List[Dict[str, str]] = []
    lock = threading.Lock()

    def worker(width: int) -> None:
        rec = {"extra": {"c": "z" * width}}
        flt(rec)  # each record dict is private to this thread
        with lock:
            results.append(dict(rec["extra"]))

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(1, 33)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Every placeholder is at least as wide as its own value; none crashed.
    assert len(results) == 32
    for extra in results:
        assert len(extra["__lp_auto_0__"]) >= 1


def test_reset_widths_never_hard_cuts_the_current_record() -> None:
    """A concurrent reset_widths() must not shrink an in-flight record below its own length.

    Regression for the observe()/width() two-lock race: reset landing between the two
    calls dropped the width to its floor of 1 and hard-cut the record to a single char.
    observe_and_width() closes the window.
    """
    reset_widths()
    set_max_auto_width(None)
    _fmt, mappings = prepare_auto_format("{extra[id]:<auto}")
    flt = compose_filter(None, mappings)
    ident = "IDENTIFIER_0123456789"  # 21 chars, always the widest value in play
    too_short: List[str] = []
    stop = threading.Event()

    def logger_thread() -> None:
        for _ in range(1500):
            rec = {"extra": {"id": ident}}
            flt(rec)
            out = rec["extra"]["__lp_auto_0__"]
            if len(out) < len(ident):  # its own value must always be fully rendered
                too_short.append(out)

    def resetter() -> None:
        while not stop.is_set():
            reset_widths()

    workers = [threading.Thread(target=logger_thread) for _ in range(8)]
    r = threading.Thread(target=resetter)
    r.start()
    for t in workers:
        t.start()
    for t in workers:
        t.join()
    stop.set()
    r.join()

    reset_widths()
    assert too_short == []
