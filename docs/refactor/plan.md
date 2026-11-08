# Refactoring plan: loggerplusplus

> Phase 4 of the refactoring campaign (`codebase-refactoring`). Turns the VP1-approved target
> (`docs/architecture.md`) into an ordered, behaviour-preserving ticket plan. Source of truth for
> what moves where: `docs/architecture.md`. Context snapshot (current sizes/lines):
> `docs/refactor/audit.md`. Target validated (VP1) on 2026-11-08 by Florian-BARRE; this plan is the
> deliverable for validation point 2 (VP2).

## Scope and constraints

- **Scope**: the whole library — the internal layout of `src/loggerplusplus/`, the test zone
  (`tests/` and `test_module/`), the non-frozen 7th example (`examples/benchmark.py`), and the
  build/lock/CI tooling surface. Only the internal layout moves; behaviour is preserved.
- **Approach**: incremental (default). Nine behaviour-preserving tickets (R-00..R-08) across five
  waves. No rewrite; no ticket mixes refactoring with a feature or a bug fix.
- **Frozen during migration** (the public surface is a contract — no rename or removal without a
  major bump, which this campaign must not do): the 30 names in `__all__`, the 7 named formats
  (resolved by name), the `formats` / `transforms` / `testing` submodules, and the six numbered
  examples (01-06).
- **Constraints**:
  - Python 3.9 floor; the 3.9-3.13 × 3-OS CI matrix and the `ubuntu-24.04` pin for the 3.9 leg
    stay.
  - The library configures NO sink at import and never calls `print()`.
  - Minimal runtime deps (loguru, colorama, win32-setctime on Windows).
  - The 95% coverage gate (`--cov-fail-under=95`) stays green throughout.
  - R-07 (uv) touches never_alone files → its own dedicated wave, CI green before merge, routed to
    florian's merge even in autonomous mode.
  - No version bump / release; never touch `release-please.yml` or `publish.yml` (florian's).
- **How each ticket proves no-change**: it keeps the Phase-3 characterization net (below) green.
  Phase 3 is done (five boundary test files merged, green); a layout ticket that keeps it green is
  behaviour-preserving by construction.

## Safety net

Phase 3 (the characterization safety net) is DONE and merged. Every layout ticket below keeps
these green; that is its proof of no behavioural change.

| Zone | Characterization tests | Status |
|---|---|---|
| formats + themes | `tests/test_char_formats.py` (PR #35) | green |
| banners | `tests/test_char_banners.py` (PR #32) | green |
| decorators + redaction | `tests/test_char_decorators.py` (PR #33) | green |
| auto-width + setup | `tests/test_char_config.py` (PR #34) | green |
| structured JSON | `tests/test_char_structured.py` (PR #36) | green |

Whole suite on merged main: **416 passed / 2 skipped**, coverage **99.66%** (≥ the 95 floor).

## Waves and tickets

Each ticket owns its files (may change); two tickets open at the same time never own the same
file. Within a wave, tickets on disjoint zones may run in parallel; across waves, a ticket starts
only when the tickets it depends on are merged. Review capacity (not agent capacity) sets the pace
— keep the number of parallel tickets small enough for a human to review.

### Wave 1: sub-package moves (run in PARALLEL — disjoint zones)

Turn the two sub-architectures the flat root was hiding (the transform layer, the auto-width
engine) into sub-packages, and carve the redaction brick out of `decorators.py`. R-01, R-02 and
R-03 own disjoint files → they may run at once.

| Ticket | Goal | Owns | Depends on | Status |
|---|---|---|---|---|
| R-01 | transforms/ sub-package: root `transforms.py` + root `banners.py` → `transforms/` (`__init__.py` = FROZEN surface `Transform`, `Banner`, `chain`, `indent`, `upper`, `lower`; `banners.py` moved verbatim; `helpers.py` = the `Transform` alias + `chain`/`indent`/`upper`/`lower`). Root `banners.py` deleted. `Banner` keeps resolving at `loggerplusplus.Banner` AND `loggerplusplus.transforms.Banner`. | `src/loggerplusplus/transforms.py`, `src/loggerplusplus/banners.py`, `src/loggerplusplus/transforms/` (new) | — | todo |
| R-02 | auto_width/ sub-package: root `width.py` + `parser.py` + `runtime.py` + `registry.py` → `auto_width/` (`width.py`, `parser.py`, `filter.py` [renamed from `runtime.py`], `registry.py`, internal-facade `__init__.py`). ALSO update the 2 internal import lines in `examples/benchmark.py` to `loggerplusplus.auto_width.parser` / `loggerplusplus.auto_width.filter`. | `src/loggerplusplus/width.py`, `src/loggerplusplus/parser.py`, `src/loggerplusplus/runtime.py`, `src/loggerplusplus/registry.py`, `src/loggerplusplus/auto_width/` (new), `examples/benchmark.py` (2 import lines) | — | todo |
| R-03 | redact.py brick: carve the redaction/truncation helpers + `SENSITIVE_KEYS` out of `decorators.py` into a new `redact.py` (`Redact` tool class, staticmethods). The 4 public decorators + `_make_decorator` stay in `decorators.py`. Drops `decorators.py` from 462 lines to under the 400-line ceiling. | `src/loggerplusplus/decorators.py`, `src/loggerplusplus/redact.py` (new) | — | todo |

Parallelism: R-01, R-02, R-03 own disjoint files → run in parallel.

### Wave 2: facade re-wiring (depends on Wave 1 merged)

| Ticket | Goal | Owns | Depends on | Status |
|---|---|---|---|---|
| R-00 | `__init__.py` facade: update the root `__init__.py` re-exports to the new homes (`transforms/`, `auto_width/`, `redact.py`) and remove any temporary shims the Wave-1 moves left. The FROZEN `__all__` (30 names) is unchanged. **Numbered R-00 but runs AFTER R-01+R-02+R-03** — it wires the facade to wherever the modules ended up; do NOT run R-00 first. | `src/loggerplusplus/__init__.py` | R-01, R-02, R-03 (merged) | todo |

### Wave 3: core dedup + benchmark reference (disjoint; run in PARALLEL; after Wave 2)

Runs on the settled layout (facade wired in Wave 2). R-04 and R-08 own disjoint files → they may
run at once.

| Ticket | Goal | Owns | Depends on | Status |
|---|---|---|---|---|
| R-04 | proxy dedup: de-duplicate the `__getattr__` / LEVEL_METHODS / `bind`-patch logic between `proxy.py` and `transform_proxy.py` (keep both files at their locations). This is the deliberate SEPARATE ticket so the layout move stays low-risk — the proxy is the library's core. | `src/loggerplusplus/proxy.py`, `src/loggerplusplus/transform_proxy.py` | R-00 (facade settled) | todo |
| R-08 | benchmark reference (NEW, from florian's scope addition): make `examples/benchmark.py` (the 7th example, NOT in the frozen six) a proper performance REFERENCE for the next campaign's optimization objective. Clean structure + documented methodology + stable output format; print a STABLE comparable number for the hot path (the per-record auto-width filter), e.g. ns/record, on a FIXED representative record + format with the record/format constants FROZEN in the file; record a BASELINE (measured once from current code, Python version + platform noted) in a durable location (a `docs/PERFORMANCE.md` section or an addition to `docs/architecture.md`); keep it OUT of CI (absolute timing is machine-dependent) — a manual reference: `python examples/benchmark.py` before/after an optimization PR. **R-08 is the cleanup + baseline, NOT the move** (the 2 import lines are already moved in R-02). | `examples/benchmark.py`, the durable baseline location (`docs/PERFORMANCE.md` or `docs/architecture.md`) | R-02 (Wave 1 merged — its 2 imports follow the `auto_width/` move) | todo |

### Wave 4: tests rework (sequenced — both own `tests/`)

Both R-05 and R-06 own `tests/`, so they run in sequence (R-05 first, then R-06); do not run them
at once. Keep the 95% coverage gate green throughout.

| Ticket | Goal | Owns | Depends on | Status |
|---|---|---|---|---|
| R-05 | test_module fold: fold the 2 unique behaviours from `test_module/` (a real `sys.stderr` sink end-to-end; a spawned child that reconfigures and aligns) into `tests/`, then DELETE the `test_module/` folder (0% coverage, ~90% duplicates `tests/`). The mapping-table row for `test_module/` goes to `deleted` when this merges. | `test_module/` (delete), `tests/` (the 2 folded behaviours) | — | todo |
| R-06 | tests/ rework, over the Phase-3 safety net: (a) the rendered-output goldens are already in place (Phase 3) — build on them; (b) consolidate the splintered test files and de-dup the `_render`/`_run` harness + capture fixtures into `conftest`; (c) add hypothesis for the transforms. **LARGEST ticket**: it MAY be split into sub-tickets at execution time (harness consolidation / hypothesis / per-module trim) if it is too big for one review — noted here, not pre-split. | `tests/`, `tests/conftest.py` | R-05 (merged) | todo |

Sequencing: R-05 then R-06 (R-06 depends on R-05 merged).

### Wave 5: tooling — FULL UV, NO POETRY (SENSITIVE, dedicated, florian's merge)

| Ticket | Goal | Owns | Depends on | Status |
|---|---|---|---|---|
| R-07 | FULL UV, NO POETRY, in this ONE wave: PEP 621 `pyproject.toml` + committed `uv.lock` only; delete `poetry.lock`, the `[tool.poetry]` section, and `requirements.txt`. Build backend → hatchling (`uv build` replaces `poetry build`; drop `poetry check`). PEP 735 `[dependency-groups]` for the dev matrix (pytest, pytest-cov, hypothesis, ruff + black/mypy gated `python=">=3.10"`). `.gitignore` un-ignores `uv.lock`. The 3.9-3.13 × 3-OS matrix + the `ubuntu-24.04` pin for the 3.9 leg STAY. CI green before merge. | `pyproject.toml`, `uv.lock` (new, committed), `poetry.lock` (delete), `requirements.txt` (delete), `.github/workflows/quality.yml`, `publish.yml`, `.aidk/project.toml`, `orca.yaml`, `CONTRIBUTING.md`, `AGENTS.md`, `.gitignore` | R-06 (i.e. all of Waves 1-4 merged; the layout is settled) | todo |

Sensitivity: R-07 touches never_alone files (`pyproject.toml`, `uv.lock`, CI workflows,
`.gitignore`) → it is its OWN dedicated wave, needs CI green before merge, and is routed to
florian's merge even in autonomous mode.

Status values: `todo`, `in progress`, `in review`, `done` (and `deleted` for the `test_module/`
mapping row when R-05 merges).

## Discovered issues

All are OUT OF SCOPE for this behaviour-preserving campaign — report only, do not fix.

| Found in | Issue | Where | Handling |
|---|---|---|---|
| Phase 3 (structured net) | `add_json` file sink is documented as "newline-delimited" but writes records back-to-back with NO newline terminator (a callable format → loguru does not append `\n`). Characterized (pinned) by test #12 in `tests/test_char_structured.py`. | `src/loggerplusplus/structured.py`, `docs/REFERENCE.md` | open question / candidate forge issue for florian — behaviour pinned, not changed |
| Phase 1 (audit) | `docs/REFERENCE.md:96` documents the wrong `set_max_auto_width` signature (`set_max_auto_width(field, width)`; the real one is `set_max_auto_width(max_width)`). | `docs/REFERENCE.md` | out of scope (report only) |
| Phase 1 (audit) | README / `FORMATS.md` say "five formats" while seven ship. | `README.md`, `docs/FORMATS.md` | out of scope (report only) |
| Phase 1 (audit) | The `_UNDOCUMENTED_NAMES` exemptions in the coherence test are vestigial (every exempted name is documented). | `tests/coherence/test_doc_coherence.py` | out of scope (report only) |
| charter | No version bump / release / touching `release-please.yml` or `publish.yml`. | — | out of scope (florian's) |

## Decisions

- 2026-11-08 — Wave order: code layout (Waves 1-4) FIRST, tooling (R-07) LAST — a deliberate
  deviation from the generic "tooling first" wave. — for THIS campaign the code layout runs under
  the existing Poetry-based checks and does NOT depend on the tooling switch; R-07 is the
  sensitive, florian-merged unit, so it is isolated as the final dedicated wave with CI green.
- 2026-11-08 — R-00 is numbered first but runs AFTER R-01+R-02+R-03 (Wave 2). — the facade
  re-exports the new homes; running it first would point at not-yet-moved modules.
- 2026-11-08 — Wave 1 (R-01/R-02/R-03) and Wave 3 (R-04/R-08) run their tickets in parallel
  (disjoint owned files); Wave 4 (R-05→R-06) is sequenced (both own `tests/`). — review capacity
  sets the pace; two tickets open at once never own the same file.
- 2026-11-08 — R-07 (uv) is a dedicated, florian-merged wave (never_alone files; CI green before
  merge). — `pyproject.toml` / `uv.lock` / CI workflows / `.gitignore` are the sensitive shared
  surface; isolating it keeps the layout moves low-risk.
- 2026-11-08 — R-08 (benchmark) is the cleanup + baseline, not the import move (that move is
  already in R-02). — the benchmark is a durable performance reference for the next campaign's
  optimization objective, kept out of CI.
- 2026-11-08 — Every layout ticket proves no-change by keeping the Phase-3 characterization net
  green. — Phase 3 is the safety net; a ticket that keeps it green is behaviour-preserving by
  construction.
- (Inherited from the target, `docs/architecture.md`): build backend = hatchling; two
  sub-packages `transforms/` + `auto_width/`; `runtime.py` renamed `filter.py`; `Banner` home =
  `transforms/banners.py` (root `banners.py` deleted); `decorators.py` redaction carved to
  `redact.py`; `test_module/` folded then deleted; `proxy.py`/`transform_proxy.py` dedup is a
  separate ticket (R-04).

## Open questions

- The `add_json` newline behaviour — pin or fix? — florian decides (candidate forge issue). We
  pinned the current behaviour; this campaign does not change it.
- Baseline durable location for R-08: a new `docs/PERFORMANCE.md` section OR an addition to
  `docs/architecture.md`. — the R-08 executor picks (both are durable); recommend the one that
  keeps the campaign docs tidy.
- R-06 split: if R-06 is too big for one review, it is split into sub-tickets (harness
  consolidation / hypothesis / per-module trim) at execution time. — the queue lead decides; do
  not pre-split.
- The out-of-scope doc bugs (`docs/REFERENCE.md:96` `set_max_auto_width` signature; README /
  `FORMATS.md` "five formats"; vestigial `_UNDOCUMENTED_NAMES`). — florian decides whether to open
  forge issues; not fixed this campaign.
