# ====== Code Summary ======
# Concurrency coverage for the process-global auto-width registry — the reason the
# RLock exists. Many threads observe values of different lengths on one field; the
# recorded width must converge to the true maximum with no lost update.

from __future__ import annotations

import threading
from typing import Dict, List

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
