# Audit: loggerplusplus

> Phase 1 of the refactoring campaign (`codebase-refactoring`, `references/audit.md`).
> Read-only snapshot of the code at commit `7420688`, on 2026-11-08.

## Summary

- Applications and entry points: a single published library (a thin, transparent proxy over
  Loguru); no application, no CLI. Public entry is the frozen `__all__` facade of
  `src/loggerplusplus/__init__.py` and the importable submodules `formats`, `transforms`,
  `testing`.
- Size: 3305 lines of Python across 27 `.py` files in `src/loggerplusplus/` (17 root modules +
  the `formats/` sub-package of 9, plus a 0-byte `py.typed`); 32 test modules / 247 test functions
  in `tests/`; 5 files / 200 lines in `test_module/`; 7 runnable examples in `examples/`.
- Main problems: a flat 17-module root hides two obvious sub-architectures (auto-width engine,
  transform layer); `decorators.py` (462 lines) is the only file over the 400-line ceiling;
  `proxy.py` and `transform_proxy.py` duplicate the level-method / `bind`-patch machinery; the
  `Banner` toolkit is defined in a private module and reached only through `transforms`; the
  build/lock surface is still Poetry.
- Clean zones to keep as they are: the `formats/` family (self-contained, 7 concrete formats
  resolved by name) and the test suite's golden + property backbone
  (`tests/test_formats_snapshot.py`, `tests/test_properties.py`).
- Tests today: 32 modules / 247 functions, 95% coverage floor; the only true golden is the inline
  `_GOLDEN` dict in `tests/test_formats_snapshot.py` (it pins the format *template*, not a fully
  rendered record); `test_module/` adds 0% coverage and ~90% duplicates `tests/`.

## Zones

### Package internals (`src/loggerplusplus/`)

- **Role**: the whole library implementation behind the frozen facade.
- **Content**: 17 root modules — `proxy.py`, `transform_proxy.py`, `api.py`, `bootstrap.py`,
  `context.py`, `decorators.py`, `intercept.py`, `logger_class.py`, `parser.py`, `registry.py`,
  `runtime.py`, `structured.py`, `testing.py`, `transforms.py`, `banners.py`, `width.py`,
  `__init__.py` — plus the `formats/` sub-package (9 modules: `base.py`, `theme.py`, `classic.py`,
  `short.py`, `minimal.py`, `ops.py`, `debug.py`, `file.py`, `plain.py`). `decorators.py` (462) is
  the only file over the 400-line ceiling.
- **Layers mixed**: the root is a flat mix of the public proxy (`proxy.py`, `api.py`), the
  auto-width engine (`parser.py` → `runtime.py` → `registry.py` → `width.py`), the transform layer
  (`transforms.py`, `banners.py`, `transform_proxy.py`) and one-call config (`bootstrap.py`); no
  sub-package separates the two obvious sub-architectures.
- **Configuration reads**: `bootstrap.py` (`setup` / `configure_from_env` / `_env_bool`) reads the
  `LOGGING_LPP_*` environment variables; `_resolve_format` (line 42) resolves a format name-string
  to a class via `getattr(formats, name)`.
- **Dependencies**: the graph is acyclic and layered (facade → core → leaves). Leaves: `width`,
  `parser`, `banners`, `transform_proxy`, `context`, `decorators`, `intercept`, `structured`,
  `testing`, `formats/theme`. Two private cross-module edges: `runtime.py` imports `_AutoMap`
  from `parser` and the `_AUTO` singleton from `registry`.
- **Duplications**: `proxy.py` and `transform_proxy.py` carry near-identical
  `__getattr__` / LEVEL_METHODS / `bind`-patch logic (the level-method branch is verbatim).
- **Logs and errors**: no `print()` anywhere (the library never calls `print()`); unknown format
  names raise `ValueError` in `_resolve_format`.
- **Tests**: covered by the tests zone below.
- **Notes**: `Banner` is defined once in `banners.py` and reached only through the chain
  `banners.py` → `transforms.py` → `__init__.py`; `banners` is never in `__all__`, so it is a
  private definition module. `api.py` binds its own global `_loguru_logger`, shadowing the facade
  `logger` alias.

### Public surface (`src/loggerplusplus/__init__.py`)

- **Role**: the frozen contract — the frozen `__all__` (30 names) plus the importable submodules.
- **Content**: `__init__.py` (77 lines) is the facade; it re-exports everything and sets
  `__all__` (lines 39-77). The 30 names span constants/metadata (`__version__`, `SENSITIVE_KEYS`,
  `DEFAULT_THEME`), classes (`LoggerClass`, `LoggerPlusPlus`, `Theme`, `Banner`,
  `InterceptHandler`), singletons (`loggerplusplus`, and the `logger` alias), submodules
  (`formats`, `transforms`), and functions (`add`, `remove`, `catch`, `opt`, `log_timing`,
  `log_io`, `bind_context`, `new_id`, `otel_context`, `add_json`, `setup`, `configure_from_env`,
  `intercept_std_logging`, `register_identifier`, `reset_widths`, `observed_widths`,
  `set_max_auto_width`, `import_widths`).
- **Layers mixed**: none — this is the one source of truth for the public surface.
- **Configuration reads**: none.
- **Dependencies**: imports every root module plus `formats` and `transforms`.
- **Duplications**: the two "proxy" modules (`proxy.py` vs `transform_proxy.py`) are both exposed
  at the surface through `LoggerPlusPlus` / `TransformProxy`.
- **Logs and errors**: none.
- **Tests**: `tests/coherence/test_doc_coherence.py` enforces that every `__all__` name and every
  concrete format appears in the docs; the 7 formats (`ClassicFormat`, `DebugFormat`,
  `FileFormat`, `MinimalFormat`, `OpsFormat`, `PlainFormat`, `ShortFormat`) all resolve by name
  via `getattr(formats, name)`.
- **Notes**: the surface is FROZEN — no rename or removal of an `__all__` name or a named format
  without a major version bump. `loggerplusplus.logger == loggerplusplus.loggerplusplus`.
  `BaseFormat` / `Theme` / `DEFAULT_THEME` resolve from `formats` but are deliberately not in
  `formats.__all__`. `testing` (with `capture` / `LogCapture`) is a public submodule, not in the
  top-level `__all__`.

### Tests + test_module (`tests/`, `test_module/`)

- **Role**: the characterization net that must survive the campaign, plus a manual smoke script.
- **Content**: `tests/` = 32 modules (conftest.py + 31 `test_*.py` + the `coherence/` module),
  247 test functions, 17 `@pytest.mark.parametrize` blocks. `test_module/` = 5 files / 200 lines
  (manual smoke, run with `poetry run python -m test_module.main`).
- **Layers mixed**: n/a.
- **Configuration reads**: coverage source is `loggerplusplus` only (`fail_under = 95`), so
  `test_module/` and `examples/` contribute nothing to the measured number.
- **Dependencies**: tests import the public surface and the internal modules directly (e.g.
  `runtime`, `registry`, `width`, `parser`).
- **Duplications**: a local `_render`/`_run` + `compose_filter(None, mappings)` harness is
  re-defined across 7 files; 6 files define their own local `cap`/`messages` capture fixtures
  instead of the conftest `LogCapture`; `test_module/` ~90% overlaps `tests/`.
- **Logs and errors**: `tests/test_examples.py` runs all 7 examples in a subprocess but asserts
  only the exit code, never the output.
- **Tests**: this is the zone. The only true golden is inline — the `_GOLDEN` dict in
  `tests/test_formats_snapshot.py` (byte-exact `colorized`/`plain` rendered strings for all 7
  formats, asserted byte-for-byte, and locked to `set(formats.__all__)`); but it pins the format
  *template* (`str(cls())`), not a fully rendered record. `tests/test_properties.py` is the only
  Hypothesis coverage (auto-width invariants).
- **Notes**: `test_module/` verdict — FOLD the 2 genuinely unique behaviours (a real `sys.stderr`
  sink end-to-end; a spawned child that reconfigures and aligns) into `tests/`, then DELETE the
  folder (0% coverage, ~90% redundant). Splintered files to merge: `test_runtime` +
  `test_runtime_edges`, `test_registry` + `test_registry_controls`, the three
  `test_decorators*` files.

### Tooling/config — the Poetry → uv surface (`pyproject.toml`, lock, CI, docs)

- **Role**: build backend, lockfile, dev-deps and the CI/docs that all still speak Poetry.
- **Content**: `pyproject.toml` (build-system = `poetry-core`, a `[tool.poetry]` section),
  `poetry.lock` (1194 lines / 126,926 bytes), `requirements.txt` (6-line pip mirror), and Poetry
  references in `.aidk/project.toml`, `.github/workflows/quality.yml`, `publish.yml`, `orca.yaml`,
  `CONTRIBUTING.md`, `AGENTS.md`, and `.gitignore` (where `uv.lock` is currently ignored).
- **Layers mixed**: n/a.
- **Configuration reads**: the dev matrix lives in `[tool.poetry.group.dev.dependencies]`:
  pytest, pytest-cov, hypothesis, ruff, plus black and mypy each gated `python = ">=3.10"`.
- **Dependencies**: `uv` / `uvx` (0.13.4) are already the launch vehicle — every check runs
  `uvx --from 'poetry>=2,<3' poetry …`, so the machine already assumes uv.
- **Duplications**: `requirements.txt` duplicates the runtime deps already in
  `pyproject.toml` / the lockfile.
- **Logs and errors**: none.
- **Tests**: none.
- **Notes**: the black/mypy `>=3.10` markers exist because their newest majors dropped Python
  3.9 while the same test matrix also runs 3.9 — the gating must be preserved. The 3.9-3.13 ×
  3-OS matrix and the `ubuntu-24.04` pin for the 3.9 leg stay. `README.md` and `docs/INSTALL.md`
  still carry `poetry add` / `poetry run` instructions and must join the migration wave.

## Cross-cutting problems

| Problem | Where (files) | Count |
|---|---|---|
| Configuration read outside an entry point | `src/loggerplusplus/bootstrap.py` (env vars) | 1 |
| Free functions holding business logic | `transforms.py`, `width.py`, `runtime.py`, `parser.py`, `structured.py`, `api.py`, `context.py`, `bootstrap.py`, `decorators.py` | 9 |
| Duplicated logic | `proxy.py` + `transform_proxy.py` (level-method/`bind`-patch); `_render`/`_run` harness in 7 test files | 2 (code) + 1 (tests) |
| `print` / no logger | none (the library never calls `print()`) | 0 |
| Swallowed errors | none found (unknown format name raises `ValueError`) | 0 |
| Tooling different from the default tooling | Poetry across `pyproject.toml`, `poetry.lock`, `requirements.txt`, CI, docs | 1 surface |

## Risks

- The public surface is FROZEN (30 `__all__` names, 7 named formats, the `formats`/`transforms`/
  `testing` submodules, the 6 numbered examples) — a rename or removal is a breaking change
  requiring a major version bump, which the campaign must not do.
- The only true golden pins the format *template*, not a rendered record; reworking the formats
  without first pinning rendered output risks silent output drift.
- `examples/benchmark.py` (the 7th, non-frozen example) imports the internal modules
  `loggerplusplus.parser.prepare_auto_format` and `loggerplusplus.runtime.compose_filter`; moving
  or renaming `parser.py`/`runtime.py` breaks it.
- The `black`/`mypy` `>=3.10` markers must be preserved when the dev matrix moves to uv, or the
  Python 3.9 test job's resolution breaks.
- `uv.lock` is currently git-ignored; it is not committable until `.gitignore` un-ignores it.

## Open questions

- `REFERENCE.md:96` documents `set_max_auto_width(field, width)` but the real signature is
  `set_max_auto_width(max_width)` — a latent doc bug (out of scope; report only).
- README/`FORMATS.md` say "five formats" while the tables list seven — cosmetic wording (out of
  scope; report only).
- The `_UNDOCUMENTED_NAMES` exemptions in `tests/coherence/test_doc_coherence.py` are now all
  redundant (every exempted name is documented) — vestigial (out of scope; report only).
- Where `Banner`'s definition should live (its home vs its `transforms`-via re-export) — the
  target resolves this in `docs/architecture.md`.
