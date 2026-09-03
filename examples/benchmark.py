"""Micro-benchmark of the per-record auto-width filter (the hot path).

Run: python examples/benchmark.py
"""

from __future__ import annotations

import timeit
from typing import Any, Dict

from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.runtime import compose_filter


def _make_record() -> Dict[str, Any]:
    return {
        "extra": {"identifier": "Service"},
        "name": "app.module.submodule",
        "message": "a representative log message",
    }


def main() -> None:
    _fmt, mappings = prepare_auto_format(
        "{identifier:<auto} {name:<auto[24~middle]} {message}"
    )
    flt = compose_filter(None, mappings)
    n = 200_000

    def run() -> None:
        flt(_make_record())

    seconds = timeit.timeit(run, number=n)
    per_record_us = seconds / n * 1e6
    print(
        f"auto-width filter: {per_record_us:.3f} us/record "
        f"({n:,} records in {seconds:.3f}s)"
    )


if __name__ == "__main__":
    main()
