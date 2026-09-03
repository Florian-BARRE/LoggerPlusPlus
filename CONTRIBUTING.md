# Contributing to LoggerPlusPlus

A thin, transparent proxy over [Loguru](https://github.com/Delgan/loguru), published on PyPI as
`loggerplusplus` (GPLv3). The **public surface is a contract** — add names freely, but never rename
or remove an exported name (formats are resolved by name) without a major version bump.

## Prerequisites

- [Poetry](https://python-poetry.org/docs/#installation) — manages the venv, the lockfile, and the
  build backend (`poetry-core`, `src/` layout).

## Working locally

```bash
poetry install                 # install deps + the dev group (black, ruff, mypy, pytest, hypothesis)
poetry run black src tests test_module   # auto-format
poetry run ruff check src tests test_module   # lint
poetry run mypy src            # type-check
poetry run pytest              # unit suite (100% coverage, gate is 95%)
poetry run python -m test_module.main    # manual smoke test — read the output by eye
```

## The Python 3.9 floor (non-negotiable)

`requires-python = ">=3.9,<4.0"`. Since development usually happens on newer interpreters, a 3.10+
construct will not fail locally — so the **CI matrix is the real guard**: the suite runs on Python
3.9 → 3.13 across Linux/macOS/Windows. Forbidden in `src/loggerplusplus/`: `X | Y` unions (use
`Optional` / `Union`), `match`, `StrEnum`, `slots=True`. Every module starts with
`from __future__ import annotations`.

## The CI gate

Every push and PR runs the reusable gate in
[`.github/workflows/quality.yml`](.github/workflows/quality.yml):

| Job | What |
|---|---|
| `lint` | `black --check` + `ruff check` + `mypy src` |
| `test` | **Linux/macOS/Windows × Python 3.9 → 3.13** matrix: `pytest` with a 95% coverage gate |
| `build` | `poetry build` + `twine check` + a clean-venv smoke install |

A change cannot merge unless the whole gate is green — and the **same gate must pass before a
release publishes** ([`publish.yml`](.github/workflows/publish.yml)).

## Releasing (automated)

Releases are driven by [release-please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/):

1. Merge conventional commits to `main` (`fix:` → patch, `feat:` → minor, `feat!:`/`BREAKING CHANGE`
   → major). [`release-please.yml`](.github/workflows/release-please.yml) opens/updates a release PR
   that bumps the version (in `pyproject.toml` and `src/loggerplusplus/__init__.py`) and the
   `CHANGELOG.md`.
2. Merge the release PR. release-please tags the release and dispatches
   [`publish.yml`](.github/workflows/publish.yml), which re-runs the full gate and publishes to PyPI
   via **Trusted Publishing (OIDC)** — no API token is stored in the repo.

## Notes

- Never configure sinks at import time and never `print()` inside the library — that is the
  consuming application's job.
- Runtime dependencies stay minimal (`loguru`, `colorama`); keep `pyproject.toml` and
  `requirements.txt` in sync.
