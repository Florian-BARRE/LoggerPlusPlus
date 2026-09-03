# Installation

## Requirements

- **Python 3.9 or newer** (`requires-python = ">=3.9,<4.0"`). Tested in CI on Python 3.9, 3.10,
  3.11, 3.12, and 3.13, across Linux, macOS, and Windows.
- Runtime dependencies (installed automatically):
  - [`loguru`](https://github.com/Delgan/loguru) `>= 0.7.3` — the logging backend.
  - [`colorama`](https://pypi.org/project/colorama/) `>= 0.4.6` — cross-platform ANSI colors.
  - `win32-setctime` `>= 1.2.0` — installed **only on Windows** (Loguru's file-time helper).

LoggerPlusPlus sits at the bottom of the dependency graph: it never depends on another in-house
package, configures no sinks at import time, and never calls `print()`.

## Install

With pip:

```bash
pip install loggerplusplus
```

With Poetry:

```bash
poetry add loggerplusplus
```

With uv:

```bash
uv add loggerplusplus
```

## Verify

```python
import loggerplusplus

print(loggerplusplus.__version__)
```

## Versioning and stability

The project follows semantic versioning, with a specific reading for a shared library:

| Bump  | When                                                                              |
|-------|-----------------------------------------------------------------------------------|
| patch | bug fix, Python-compatibility fix, documentation fix                               |
| minor | a new exported name, a new format, a new decorator option                         |
| major | anything a consumer must adapt to (a rename, a removal, an alignment change)       |

The public surface is a stability contract: names are **added**, never renamed or removed without
a major bump. Formats are resolved by name, so a rename would silently degrade every consumer to
the fallback format — hence it is treated as a breaking change.

Releases are automated with [release-please](https://github.com/googleapis/release-please) and
published to PyPI via Trusted Publishing (OIDC). See [CONTRIBUTING.md](../CONTRIBUTING.md).
