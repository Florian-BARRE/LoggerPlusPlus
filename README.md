<div align="center">

# LoggerPlusPlus

### ALIGNED, READABLE LOGGING

**Enhanced logging for Python, built on [Loguru](https://github.com/Delgan/loguru)** — keep
Loguru's simple, powerful API and add auto-aligned identifier columns, width-aware truncation,
ready-made colorized formats, and convenience decorators. A small, dependency-light library meant
to be shared across every service in a stack.

[![PyPI](https://img.shields.io/pypi/v/loggerplusplus?label=loggerplusplus&color=2f9e44)](https://pypi.org/project/loggerplusplus/)
[![Python](https://img.shields.io/pypi/pyversions/loggerplusplus?color=2f9e44)](https://pypi.org/project/loggerplusplus/)
[![CI](https://github.com/Florian-BARRE/LoggerPlusPlus/actions/workflows/ci.yml/badge.svg)](https://github.com/Florian-BARRE/LoggerPlusPlus/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Florian-BARRE/LoggerPlusPlus/actions/workflows/codeql.yml/badge.svg)](https://github.com/Florian-BARRE/LoggerPlusPlus/actions/workflows/codeql.yml)
[![License](https://img.shields.io/badge/license-GPLv3-2f9e44)](LICENSE)

</div>

> Configure a sink with an auto-width format, bind an `identifier`, and log. Identifier columns
> align themselves to the longest value seen, overflow is truncated where you ask, and the whole
> API stays a transparent, drop-in proxy over Loguru.

---

## Why LoggerPlusPlus

- **Columns that align themselves.** Write `{identifier:<auto}` in a format and every identifier
  is padded to the widest one seen so far — no manual widths, no jitter between lines.
- **Truncation you control.** Cap a field with `[width]` and choose the side: `left`, `right`, or
  `middle`, each with an ellipsis.
- **Ready-made formats, resolved by name.** Five colorized layouts (`Classic`, `Short`, `Ops`,
  `Debug`, `Minimal`) that a service can select from configuration.
- **A transparent Loguru proxy.** Everything Loguru exposes (sinks, levels, filters, backtraces,
  `bind`, `contextualize`, ...) remains available; a few names are enhanced, none are hidden.
- **Convenience decorators.** `catch`, `opt`, `log_timing`, and `log_io`, each accepting an
  `identifier` or a pre-bound logger.
- **Small and safe to depend on.** Runtime deps are just `loguru` and `colorama`; the package
  configures no sinks at import time and never prints.

---

## Installation

```bash
pip install loggerplusplus
# or
poetry add loggerplusplus
```

Requires Python 3.9+.

---

## Quickstart

```python
import sys

from loggerplusplus import add, remove, logger

remove()  # drop Loguru's default handler first
add(
    sink=sys.stderr,
    level="DEBUG",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level.name:<8}</level> | "
        "[<blue>{identifier:<auto[18~middle]}</blue>] | "
        "<level>{message}</level>"
    ),
)

logger.bind(identifier="MAIN").info("Hello from main")
```

```text
2025-09-25 14:03:12.345 | INFO     | [MAIN] | Hello from main
```

`logger` is the enhanced, ready-to-use singleton (a drop-in for Loguru's `logger`). The same API
is also available on the `loggerplusplus` singleton and as the top-level functions
`add` / `remove` / `catch` / `opt` / `log_timing` / `log_io`.

---

## Auto-width alignment

`{identifier:<auto}` is not valid Loguru syntax on its own — LoggerPlusPlus rewrites it. The
`auto` width tracks the longest value observed for that field over the process lifetime and pads
every line to it, so a column never shrinks and never jitters. `LoggerClass` (below) pre-registers
its identifier so alignment is correct from the very first line.

```text
[MAIN]           | starting
[WORKER]         | working
[LONG-SERVICE-A] | columns grew, and stay aligned
```

The token grammar is `{field:<align><width>[cap~trunc]}`:

| Part    | Values                     | Meaning                                        |
|---------|----------------------------|------------------------------------------------|
| `align` | `<` `>` `^`                | left / right / center (default `<`)            |
| `width` | `auto` or an integer       | grow-to-fit, or a fixed width                  |
| `cap`   | integer, in `[...]`        | maximum width                                  |
| `trunc` | `left` `right` `middle`    | which side to cut when overflowing, with `…`   |

`field` may be a record attribute (`level.name`), a dotted path, or `extra[key]`.

---

## Truncation

```python
"{identifier:<auto[18~middle]}"   # grow to fit, but never wider than 18, cut in the middle
"{name:<20~right}"                 # fixed width 20, cut the tail
"{extra[service]:>auto[12~left]}"  # right-aligned, capped at 12, cut the head
```

`VeryLongServiceName` capped at 12 with `~middle` renders as `VeryL…Name`.

---

## Ready-made formats

Each format is a subclass of `str`, so an instance *is* a format string and can be passed straight
to `add(format=...)`. Formats are resolved **by name**, which is convenient for configuration:

```python
import sys

from loggerplusplus import loggerplusplus, formats

loggerplusplus.remove()
loggerplusplus.add(sink=sys.stdout, level="DEBUG", format=formats.ShortFormat())

# Select one by name (e.g. from an env var), with a safe fallback:
chosen = "OpsFormat"
loggerplusplus.add(sink=sys.stdout, format=getattr(formats, chosen, formats.DebugFormat)())
```

| Format          | Contents                                                            |
|-----------------|---------------------------------------------------------------------|
| `ClassicFormat` | time, level, identifier, source `name:line`, message                |
| `ShortFormat`   | time, level, identifier, message                                    |
| `OpsFormat`     | time, level, identifier, process/thread, message                    |
| `DebugFormat`   | time, level, identifier, process/thread, source `name:line`, message|
| `MinimalFormat` | identifier, message                                                 |

Every format accepts overrides such as `colorized=False` (plain output for file sinks) and
per-field widths (`level_width=`, `identifier_width=`, ...). See [`docs/FORMATS.md`](docs/FORMATS.md).

---

## LoggerClass

Any class can get a bound `self.logger` whose identifier defaults to the class name:

```python
from loggerplusplus import LoggerClass

class Service(LoggerClass):
    def run(self):
        self.logger.info("Service is running")

Service().run()
Service(identifier="Custom").run()   # explicit identifier
```

---

## Decorators

```python
from loggerplusplus import catch, log_timing, log_io

@catch(identifier="WORKER", level="ERROR")
def risky():
    raise RuntimeError("Boom!")

@log_timing(identifier="TASK", exit_message="Finished {func} in {duration:.2f}s")
@log_io(identifier="CALC", log_args=True, log_return=True)
def compute(a, b):
    return a + b
```

`catch` also works as a context manager; `opt` accepts either an `identifier` or a pre-bound
`logger`. See [`docs/USAGE.md`](docs/USAGE.md).

---

## Architecture

```text
add(format=str)
   ├─ parser.prepare_auto_format()   rewrite {identifier:<auto} into {extra[__lp_auto_N__]}
   ├─ runtime.compose_filter()       loguru calls this once per record, before formatting —
   │                                 the injection point for the padded/truncated value
   ├─ registry (_AUTO)               thread-safe max-observed width per field (monotonic)
   └─ loguru formatting
```

A fuller explanation is in [`docs/REFERENCE.md`](docs/REFERENCE.md).

---

## Public API

```python
from loggerplusplus import (
    loggerplusplus,   # enhanced singleton (drop-in for loguru's logger)
    logger,           # alias of the singleton
    LoggerPlusPlus,   # the proxy class
    LoggerClass,      # mixin providing self.logger
    formats,          # ClassicFormat, ShortFormat, OpsFormat, DebugFormat, MinimalFormat
    add, remove,      # sink management
    catch, opt,       # loguru helpers with identifier binding
    log_timing, log_io,  # timing / I/O decorators
    __version__,
)
```

The public surface is a stability contract: names are added, never renamed or removed without a
major version bump. Full signatures in [`docs/REFERENCE.md`](docs/REFERENCE.md).

---

## Documentation

| Document                             | Contents                                             |
|--------------------------------------|------------------------------------------------------|
| [docs/INSTALL.md](docs/INSTALL.md)   | Installation, requirements, and version support      |
| [docs/USAGE.md](docs/USAGE.md)       | Task-oriented guide: sinks, formats, decorators      |
| [docs/FORMATS.md](docs/FORMATS.md)   | The five formats and the auto-width token grammar    |
| [docs/REFERENCE.md](docs/REFERENCE.md) | API reference and the auto-width pipeline internals |
| [CHANGELOG.md](CHANGELOG.md)         | Release history (maintained by release-please)       |
| [CONTRIBUTING.md](CONTRIBUTING.md)   | Development workflow, the CI gate, and releasing     |

---

## Project layout

```text
src/loggerplusplus/
├── __init__.py        public API
├── proxy.py           LoggerPlusPlus — transparent proxy over loguru.logger
├── api.py             add() — wires the format parser into loguru.add
├── parser.py          auto-width token grammar
├── runtime.py         per-record width / truncation computation
├── registry.py        thread-safe max-observed width
├── logger_class.py    LoggerClass mixin
├── decorators.py      catch · opt · log_timing · log_io
└── formats/           BaseFormat + Classic · Short · Ops · Debug · Minimal
```

---

## Development

```bash
poetry install
poetry run black src tests test_module
poetry run ruff check src tests test_module
poetry run mypy src
poetry run pytest            # 100% coverage; the CI gate is 95%
```

The CI matrix runs the suite on Python 3.9–3.13 across Linux, macOS, and Windows. See
[CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

LoggerPlusPlus is licensed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE).
It builds on top of Loguru (MIT).

## Author

Created and maintained by **Florian BARRE**.
[Website](https://florianbarre.fr/) · [LinkedIn](https://www.linkedin.com/in/barre-florian) · [GitHub](https://github.com/Florian-BARRE)
