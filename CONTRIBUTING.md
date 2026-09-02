# Contributing to LoggerPlusPlus

A thin, transparent proxy over [Loguru](https://github.com/Delgan/loguru), published on PyPI as
`loggerplusplus` (GPLv3). The **public surface is a contract** — add names freely, but never rename
or remove an exported name (formats are resolved by name) without a major version bump.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — manages the venv, the lockfile,
  and every Python version used by the gate.

## Working locally

```bash
uv sync --frozen             # install locked deps (incl. the dev group: ruff, pytest)
uv run ruff format .         # auto-format
uv run ruff check .          # lint
uv run pytest                # unit suite (parser / runtime / registry)
uv run python -m test_module.main   # manual smoke test — read the output by eye
```

## The Python 3.9 floor (non-negotiable)

`requires-python = ">=3.9"`. Since development usually happens on newer interpreters, a 3.10+
construct will not fail locally — so the **CI matrix is the real guard**: the suite and the smoke
module run on Python 3.9 → 3.13, catching a 3.9 break before it merges.

Forbidden in `loggerplusplus/`: `X | Y` unions (use `Optional` / `Union`), `match`, `StrEnum`,
`slots=True`. Every module starts with `from __future__ import annotations`.

## The CI gate

Every push and PR runs the reusable gate in
[`.github/workflows/gate.yml`](.github/workflows/gate.yml):

| Job | What |
|---|---|
| `quality` | `ruff format --check` + `ruff check` (ruff is the enforced linter) |
| `test` | Python **3.9 → 3.13** matrix: `pytest` + the smoke module (must exit 0) |
| `build` | `uv build` + `twine check` (valid wheel/sdist, README renders on PyPI) |

A change cannot merge unless the whole gate is green — and the **same gate must pass before a
release publishes** ([`release.yml`](.github/workflows/release.yml)).

Run the essentials before opening a PR:

```bash
uv run ruff format --check . && uv run ruff check . && uv run pytest
```

## Releasing (maintainer)

Publishing goes to PyPI via **Trusted Publishing (OIDC)** — no API token is stored in the repo.
The one-time PyPI / GitHub environment setup is documented at the top of
[`release.yml`](.github/workflows/release.yml).

1. Bump `version` in `pyproject.toml` **in the same commit** as the change.
2. Tag and push — the tag must match the version, or the release guard fails:

   ```bash
   git tag v1.0.7 && git push origin v1.0.7
   ```

The tag triggers the full gate, then the OIDC publish.

## Notes

- Never configure sinks at import time and never `print()` inside the library — that is the
  consuming application's job.
- Runtime dependencies stay minimal (`loguru`, `colorama`); keep `pyproject.toml` and
  `requirements.txt` in sync.
