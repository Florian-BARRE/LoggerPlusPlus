# Performance reference

`examples/benchmark.py` is a manual performance REFERENCE for the per-record
auto-width filter — the library's hot path, which runs once per log record on
every emit. It times one auto-width filter pass over a fixed log record with a
fixed format and prints the result in ns/record. Run it with
`python examples/benchmark.py`; it is NOT run in CI. Absolute numbers are
machine-dependent: the ns/record value is only comparable across runs on the
same machine, so always diff the stable `BENCHMARK:` line rather than absolute
wall-clock times.

## BASELINE

Re-recorded from the current code (commit 118c522 onward) on this machine:
median of 5 consecutive runs (7921 to 8955 ns/record; expect roughly 10% run-to-run
noise). The timed workload INCLUDES the `copy.deepcopy(RECORD)` done on every
iteration by `_make_record()` (the filter may mutate `extra`), so this number is
not comparable with any earlier one recorded from a fresh dict literal.

| Metric | Value | Python | Platform | Date |
|---|---|---|---|---|
| ns/record (auto-width filter) | 8456 | 3.12.15 | Linux-6.12.113+deb13-cloud-amd64-x86_64-with-glibc2.41 | 2026-11-09 |

## How to use it

Run `python examples/benchmark.py` before and after any optimization PR; the
ns/record number should go down. Do not change the frozen constants
(`RECORD`, `FORMAT`, `N`) in `examples/benchmark.py` without updating this
baseline.
