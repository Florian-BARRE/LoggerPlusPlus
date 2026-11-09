"""Performance reference for the per-record auto-width filter (the hot path).

What is measured
----------------
The per-record time spent in the callable returned by
``loggerplusplus.auto_width.filter.compose_filter``: one auto-width filter
pass over one fixed log record (width computation, truncation, column
alignment). That filter runs once per log record, on every emit, which
makes it the hot path of the library.

Machine dependence
------------------
Absolute timing is machine-dependent. The ns/record number is only
comparable across runs on the SAME machine. The stable ``BENCHMARK:``
summary line (same format every run) is what to diff before/after.

Not run in CI
-------------
This benchmark is a manual tool, not part of the test suite or of any CI
workflow: ``python examples/benchmark.py``.

How to use it
-------------
Run it before an optimization PR, run it again after the change, and
compare the ``BENCHMARK:`` line. The ns/record number should go down.
The frozen constants below define what is measured: do not change them
without updating the baseline in ``docs/PERFORMANCE.md``.
"""

from __future__ import annotations

import copy
import platform
import timeit
from typing import Any, Dict

from loggerplusplus.auto_width.filter import compose_filter
from loggerplusplus.auto_width.parser import prepare_auto_format

# ---- Frozen benchmark constants (do NOT change without updating the baseline) ----
RECORD: Dict[str, Any] = {
    "extra": {"identifier": "Service"},
    "name": "app.module.submodule",
    "message": "a representative log message",
}
FORMAT = "{identifier:<auto} {name:<auto[24~middle]} {message}"
N = 200_000


def _make_record() -> Dict[str, Any]:
    """A fresh deep copy of the frozen record (the filter may mutate ``extra``)."""
    return copy.deepcopy(RECORD)


def main() -> None:
    """Measure the per-record auto-width filter and print the BENCHMARK line."""
    _fmt, mappings = prepare_auto_format(FORMAT)
    flt = compose_filter(None, mappings)

    def run() -> None:
        flt(_make_record())

    seconds = timeit.timeit(run, number=N)
    per_record_ns = seconds / N * 1e9
    print(
        f"auto-width filter: {per_record_ns:.0f} ns/record ({N:,} records, {seconds:.3f}s)"
    )
    print(
        "BENCHMARK: "
        f'ns/record={per_record_ns:.0f} records={N:,} format="{FORMAT}" '
        f"platform={platform.platform()}"
    )


if __name__ == "__main__":
    main()
