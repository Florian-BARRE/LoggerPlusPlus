# Architecture: loggerplusplus

> Target architecture following `coding-standards`, to be validated on 2026-11-08 by
> Florian-BARRE (this is the validation-point doc). Written in phase 2 of the refactoring
> campaign; when approved it becomes the project's living architecture document.

## Overview

loggerplusplus is a thin, transparent proxy over Loguru: a single published library with no
application and no CLI. Its public surface is FROZEN — the 30 names in `__all__`, the 7 named
formats (resolved by name), the `formats` / `transforms` / `testing` submodules, and the six
numbered examples (01-06). This campaign is a **behaviour-preserving** restructure: only the
internal layout moves; nothing public changes.

Shape chosen (`coding-standards`, `references/project-shapes.md`): a **src-layout PEP 621
library**. Two obvious sub-architectures are grouped into sub-packages so the tree tells the
architecture (`coding-standards` §2): the **auto-width engine** and the **transform layer**.
Everything else stays as cohesive single modules. Dependency direction stays one-way (acyclic):
facade → (proxy / bootstrap / transforms / auto_width / decorators / context / intercept /
structured / testing) → leaves (width, parser, filter, theme).

## Tree

```
src/loggerplusplus/
├── __init__.py              # facade: FROZEN __all__ (30 names, unchanged); re-exports adjusted to new homes
├── py.typed                 # unchanged
├── proxy.py                 # LoggerPlusPlus class + loggerplusplus singleton (FROZEN public class)
├── transform_proxy.py       # TransformProxy primitive + emit_with_transform + LEVEL_METHODS
├── api.py                   # `add` (enhanced sink add, FROZEN public name) + `logger` alias; imports from auto_width/
├── decorators.py            # catch / opt / log_timing / log_io + _make_decorator (FROZEN public names)
├── redact.py                # NEW brick: redaction/truncation helpers (Redact tool class) + SENSITIVE_KEYS
├── context.py               # new_id / otel_context / bind_context (FROZEN public names)
├── intercept.py             # InterceptHandler / intercept_std_logging
├── structured.py            # add_json (FROZEN public name)
├── testing.py               # LogCapture / capture (FROZEN submodule path loggerplusplus.testing)
├── bootstrap.py             # setup / configure_from_env (one-call config); _resolve_format resolves the 7 formats by name
├── logger_class.py          # LoggerClass mixin (FROZEN public class)
├── formats/                 # UNCHANGED (FROZEN family): base, theme, classic, short, minimal, ops, debug, file, plain, __init__
├── transforms/              # NEW sub-package (was root transforms.py + root banners.py)
│   ├── __init__.py          # FROZEN submodule surface: Transform, Banner, chain, indent, upper, lower
│   ├── banners.py           # Banner toolkit (moved verbatim from root banners.py)
│   └── helpers.py           # Transform type alias + chain/indent/upper/lower (from root transforms.py, minus the Banner re-export)
└── auto_width/              # NEW sub-package (was root width.py + parser.py + runtime.py + registry.py)
    ├── __init__.py          # internal facade: re-export the engine (parser/filter/registry/width) for internal importers
    ├── width.py             # visual-width (terminal-cell) text metrics (from root width.py)
    ├── parser.py            # prepare_auto_format + _AutoMap (from root parser.py)
    ├── filter.py            # compose_filter + _build_dict_filter (from root runtime.py; renamed: "runtime" was vague)
    └── registry.py          # _AutoWidthRegistry + _AUTO + register_identifier/reset_widths/observed_widths/set_max_auto_width/import_widths
```

## Layers and dependencies

- Allowed direction (one-way, acyclic): facade → (proxy / bootstrap / transforms / auto_width /
  decorators / context / intercept / structured / testing) → leaves (width, parser, filter,
  theme).
- Configuration is read only in: `bootstrap.py` (`setup` / `configure_from_env` read the
  `LOGGING_LPP_*` environment variables).
- The auto-width engine is a clean one-way pipeline: parser → filter → registry → width.

## Packages

| Package | Responsibility | Main units | Form |
|---|---|---|---|
| `__init__.py` | public facade; the FROZEN `__all__` (30 names) | `logger`, `__all__` | single facade |
| `proxy.py` | transparent proxy class + `loggerplusplus` singleton | `LoggerPlusPlus`, `loggerplusplus` | single class |
| `transform_proxy.py` | `transform=` / `raw=` primitive on a loguru logger | `TransformProxy`, `emit_with_transform` | single class + free fn |
| `api.py` | enhanced `add` sink + `logger` alias; imports from `auto_width/` | `add`, `logger` | single module |
| `decorators.py` | the 4 public logging decorators + core | `catch`, `opt`, `log_timing`, `log_io`, `_make_decorator` | single module |
| `redact.py` | redaction / truncation brick | `Redact`, `SENSITIVE_KEYS` | single tool class |
| `context.py` | correlation-context binding on loguru `contextualize` | `new_id`, `otel_context`, `bind_context` | single module |
| `intercept.py` | route stdlib `logging` into loguru | `InterceptHandler`, `intercept_std_logging` | class + free fn |
| `structured.py` | JSON (NDJSON) sink | `add_json` | single module |
| `testing.py` | downstream capture helper (FROZEN submodule) | `LogCapture`, `capture` | class + free fn |
| `bootstrap.py` | one-call config; resolves the 7 formats by name | `setup`, `configure_from_env`, `_resolve_format` | single module |
| `logger_class.py` | mixin giving `self.logger` (FROZEN public class) | `LoggerClass` | single mixin class |
| `formats/` | FROZEN named-format family (resolved by name) | `BaseFormat`, `Theme`, 7 concrete `*Format` | family |
| `transforms/` | FROZEN transform submodule surface | `Transform`, `Banner`, `chain`, `indent`, `upper`, `lower` | family (sub-package) |
| `auto_width/` | auto-width engine (visual-width pipeline) | `prepare_auto_format`, `compose_filter`, `_AutoWidthRegistry`, width metrics | sub-package (internal facade) |

## Families

| Family | Contract | Params | Implementations |
|---|---|---|---|
| `formats` (FROZEN) | `BaseFormat(str, ABC)` | via `format(**overrides)` | `ClassicFormat`, `ShortFormat`, `OpsFormat`, `DebugFormat`, `MinimalFormat`, `FileFormat` (← Classic), `PlainFormat` (← Short) |
| `transforms` (FROZEN submodule surface) | `Transform = Callable[[str], str]` | `Banner` tool class (figlet / box / rule / preset) | composable helpers `chain`, `indent`, `upper`, `lower` (free functions — a justified exception: the frozen public API of the submodule) |

`formats` is resolved by name via `getattr(formats, name)` at `bootstrap.py:42`.

## Cross-cutting choices

- **Tooling — FULL UV, NO POETRY** (florian's decision). Build backend → **hatchling** (PEP 621,
  auto src-layout); `uv build` replaces `poetry build`; `poetry check` has no uv equivalent (drop).
  PEP 735 `[dependency-groups]` for the dev matrix. `uv.lock` committed (un-ignore it in
  `.gitignore`). The 3.9-3.13 × 3-OS test matrix + the `ubuntu-24.04` pin for the 3.9 leg STAY.
  black/mypy keep their `python = ">=3.10"` markers (newest majors dropped 3.9; the same matrix
  runs 3.9).
- **Invariants (unchanged, from the charter)**: the library configures NO sink at import and never
  calls `print()`; Python 3.9 floor; minimal runtime deps (loguru, colorama, win32-setctime[win]);
  the public surface is a contract (no rename/removal of an `__all__` name or a named format
  without a major bump).

## Mapping table

| Current location | Content | Target location | Ticket | Status |
|---|---|---|---|---|
| `src/loggerplusplus/__init__.py` | facade + FROZEN `__all__` (30 names) | `__init__.py` (re-exports updated to new homes; `__all__` unchanged) | R-00 (layout) | todo |
| `src/loggerplusplus/banners.py` | `Banner` toolkit | `transforms/banners.py` | R-01 | todo |
| `src/loggerplusplus/transforms.py` | `Transform`, chain/indent/upper/lower, Banner re-export | `transforms/__init__.py` (FROZEN surface) + `transforms/helpers.py` | R-01 | todo |
| `src/loggerplusplus/width.py` | visual-width engine | `auto_width/width.py` | R-02 | todo |
| `src/loggerplusplus/parser.py` | `prepare_auto_format`, `_AutoMap` | `auto_width/parser.py` | R-02 | todo |
| `src/loggerplusplus/runtime.py` | `compose_filter`, `_build_dict_filter` | `auto_width/filter.py` | R-02 | todo |
| `src/loggerplusplus/registry.py` | `_AutoWidthRegistry`, `_AUTO`, width controls | `auto_width/registry.py` | R-02 | todo |
| `src/loggerplusplus/decorators.py` | 4 decorators + `_make_decorator` + redaction/trunc helpers + SENSITIVE_KEYS | `decorators.py` (4 decorators + core) + `redact.py` (`Redact` tool class + SENSITIVE_KEYS) | R-03 | todo |
| `examples/benchmark.py` (7th, NOT in frozen six) | imports internals `loggerplusplus.parser.prepare_auto_format` + `loggerplusplus.runtime.compose_filter` | same file, 2 import lines updated to `loggerplusplus.auto_width.parser` / `loggerplusplus.auto_width.filter` | R-02 | todo |
| `src/loggerplusplus/proxy.py` + `transform_proxy.py` | duplicated `__getattr__`/LEVEL_METHODS/bind-patch logic | keep locations; the dedup is its OWN ticket | R-04 | todo |
| `test_module/` (5 files / 200 lines, manual smoke, 0% coverage) | fold 2 unique behaviours (real stderr sink e2e; spawned child reconfigures+aligns) into `tests/`, then DELETE the folder | deleted | R-05 | todo |
| `tests/` (32 modules / 247 fns) | (a) extend format golden to pin RENDERED output, not just templates; (b) consolidate splintered files + dedup the `_render`/`_run` harness & capture fixtures into conftest; (c) add hypothesis for the transforms | `tests/` reworked over the characterization net | R-06 | todo |
| `poetry.lock`, `requirements.txt`, `[tool.poetry]` (pyproject), poetry in CI/checks/docs | the POETRY install surface | DELETED / uv: hatchling backend, committed `uv.lock`, PEP 735 `[dependency-groups]` (pytest/pytest-cov/hypothesis/ruff + black/mypy gated `python=">=3.10"`), `.gitignore` un-ignores `uv.lock` | R-07 | todo |
| `examples/benchmark.py` (7th, NOT in frozen six) | a stable performance REFERENCE for the next campaign's optimization objective: ns/record for the per-record auto-width filter on a fixed record + format; a BASELINE recorded in a PERFORMANCE.md section or in architecture.md | same file restructured + documented; a manual reference (`python examples/benchmark.py`), kept OUT of CI | R-08 | todo |

Status values: `todo`, `in progress`, `done`, `deleted` (with the reason in Decisions).

## Decisions

- 2026-11-08 — Build backend = hatchling (PEP 621 native, src-layout friendly, `uv build`
  drop-in). — the one real fork in the road; hatchling is the low-friction default for
  src-layout + PEP 621.
- 2026-11-08 — Two sub-packages: `transforms/` (the transform layer) and `auto_width/` (the
  auto-width engine). — the two obvious sub-architectures the flat 17-module root was hiding
  (`coding-standards` §2).
- 2026-11-08 — `runtime.py` renamed `filter.py` (its role: the per-record auto-width filter
  composer); `api`, `bootstrap` keep their names (acceptable). — the name said the role.
- 2026-11-08 — `banner` home: `Banner` moves into `transforms/banners.py`; root `banners.py`
  deleted. `loggerplusplus.banners` no longer resolves (it was never in `__all__` and never a
  documented import path — not part of the frozen surface). `loggerplusplus.Banner` and
  `loggerplusplus.transforms.Banner` keep resolving (FROZEN). — one source of truth; the frozen
  import paths stay.
- 2026-11-08 — `decorators.py` redaction/truncation helpers move to a `redact.py` brick (`Redact`
  tool class, staticmethods) + `SENSITIVE_KEYS`; the 4 public decorators + `_make_decorator` stay
  in `decorators.py`. — drops it from 462 lines to under the 400-line ceiling.
- 2026-11-08 — `benchmark.py` (the 7th example, NOT in the frozen six) reaches into internals, so
  its 2 internal imports follow the `auto_width/` move. (No permanent re-export shim for
  `loggerplusplus.parser` / `loggerplusplus.runtime` — internal paths are free to move; if an
  unknown downstream consumer breaks, that is a discovered issue, not a seam.)
- 2026-11-08 — `test_module/` is folded (2 behaviours) then deleted. — it adds 0% coverage and
  ~90% duplicates `tests/`.
- 2026-11-08 — `proxy.py` / `transform_proxy.py` duplication is a SEPARATE ticket (R-04), not
  bundled with the layout move. — the proxy is the library's core; keep the layout move low-risk.

## Open questions

- This doc is a VALIDATION POINT — to be approved on 2026-11-08 by Florian-BARRE before any code
  moves.
- Out of scope for the campaign (report only, do not fix): `REFERENCE.md:96` documents the wrong
  `set_max_auto_width` signature; README / `FORMATS.md` say "five formats" while seven ship; the
  `_UNDOCUMENTED_NAMES` exemptions in the coherence test are vestigial.
- No version bump / release / touching `release-please.yml` or `publish.yml` (florian's).
