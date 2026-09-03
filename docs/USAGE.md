# Usage

A task-oriented guide. For the token grammar and formats see [FORMATS.md](FORMATS.md); for
signatures and internals see [REFERENCE.md](REFERENCE.md).

## One-call setup

For the common case, `setup()` configures a console sink (with a format chosen by name), an
optional plain file sink, and optional stdlib interception in a single opt-in call — replacing the
bootstrap every service would otherwise re-implement:

```python
from loggerplusplus import setup

setup(level="INFO", format="OpsFormat", file="app.log", intercept=True)
```

`configure_from_env()` does the same from environment variables, so a service reads its logging
config the same way everywhere:

```python
from loggerplusplus import configure_from_env

# LOGGING_LPP_LEVEL, LOGGING_LPP_FORMAT, LOGGING_LPP_FILE, LOGGING_LPP_COLORIZE,
# LOGGING_LPP_ENQUEUE, LOGGING_LPP_INTERCEPT, LOGGING_LPP_ROTATION, LOGGING_LPP_RETENTION
configure_from_env()
```

Both return the created sink ids (`{"console": ..., "file": ...}`) and never run at import time.
For finer control, use the building blocks below directly.

## Configuring a sink

LoggerPlusPlus does not configure any sink for you. As with Loguru, remove the default handler
first, then add your own:

```python
import sys

from loggerplusplus import add, remove, logger

remove()
add(sink=sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<8} | {message}")

logger.info("ready")
```

`add()` accepts the usual Loguru keyword arguments (`level`, `format`, `filter`, `colorize`,
`serialize`, `backtrace`, `diagnose`, `enqueue`, `catch`, ...) and returns the sink id, which you
can pass to `remove(sink_id)`.

## Binding an identifier

The `identifier` is a value in the record's `extra` bag. Bind it once and every subsequent record
carries it:

```python
log = logger.bind(identifier="INGEST")
log.info("started")     # -> [INGEST] started
```

Used with an auto-width token (`{identifier:<auto}`), the identifier column aligns itself across
all identifiers seen in the process. See [FORMATS.md](FORMATS.md).

## Class-scoped loggers

`LoggerClass` gives a class a bound `self.logger` whose identifier defaults to the class name and
pre-registers that identifier so alignment is correct from the first line:

```python
from loggerplusplus import LoggerClass

class Worker(LoggerClass):
    def __init__(self):
        LoggerClass.__init__(self)          # required: creates self.logger
        self.logger.info("constructed")

    def run(self):
        self.logger.info("working")

Worker().run()
```

Override the identifier explicitly with `identifier=`:

```python
class Worker(LoggerClass):
    def __init__(self):
        LoggerClass.__init__(self, identifier="WORKER-1")
```

A static-only helper class can bind directly:

```python
class Helpers:
    logger = logger.bind(identifier="Helpers")
```

## Ready-made formats

```python
import sys

from loggerplusplus import loggerplusplus, formats

loggerplusplus.remove()
loggerplusplus.add(sink=sys.stdout, level="DEBUG", format=formats.ShortFormat())
```

Select by name from configuration, with a safe fallback:

```python
name = os.environ.get("LOGGING_LPP_FORMAT", "DebugFormat")
loggerplusplus.add(sink=sys.stdout, format=getattr(formats, name, formats.DebugFormat)())
```

For a file sink, disable color:

```python
loggerplusplus.add(sink="app.log", format=formats.ClassicFormat(colorized=False))
```

## Structured (JSON) logging

For log pipelines (ELK, Loki, Datadog, ...), `add_json()` installs a sink that emits one compact
JSON object per record — with the identifier promoted, the user `extra` preserved, and a structured
`exception` — using loguru's own destination handling (stream, callable, or file path, with
rotation/retention/enqueue):

```python
import sys
from loggerplusplus import add_json

add_json(sink=sys.stdout, level="INFO")
add_json(sink="app.jsonl", rotation="50 MB")            # newline-delimited JSON file
add_json(sink=sys.stdout, fields=("time", "level", "identifier", "message"))  # trim the schema
```

```json
{"time": "2025-09-25T14:03:12.345000+00:00", "level": "INFO", "identifier": "MAIN", "message": "started", "name": "app", "function": "run", "line": 12, "module": "app", "process": 4321, "thread": 140000, "extra": {"user": "bob"}, "exception": null}
```

## Correlation / request context

Bind a correlation or request id (and any fields) onto every record emitted within a block, so a
request can be traced across a service. It is built on loguru's contextvars-based context, so it is
correct under threads and asyncio tasks, and the bound fields appear in `extra` (and thus in JSON
output or any format that references them):

```python
from loggerplusplus import bind_context, new_id

with bind_context(request_id=new_id(prefix="req-"), user="bob"):
    logger.info("handling request")   # extra carries request_id + user

# Inject OpenTelemetry trace/span ids when opentelemetry is installed (never a hard dependency):
with bind_context(otel=True):
    logger.info("traced")             # extra carries trace_id/span_id if a span is active
```

## Filters

Callable and dict filters both work, including alongside an auto-width format:

```python
# Callable filter
loggerplusplus.add(sink=sys.stderr, format=formats.ShortFormat(),
                   filter=lambda r: "secret" not in r["message"])

# Per-module dict filter (Loguru semantics: most specific prefix wins)
loggerplusplus.add(sink=sys.stderr, format=formats.ShortFormat(),
                   filter={"": "INFO", "noisy.module": "WARNING"})
```

## Decorators

### catch

Drop-in for `logger.catch`, as a decorator or a context manager:

```python
from loggerplusplus import catch

@catch(identifier="JOB", level="ERROR", reraise=False)
def risky():
    raise RuntimeError("boom")

with catch(identifier="BATCH", level="ERROR"):
    do_work()
```

### opt

`logger.opt` with optional identifier or pre-bound logger:

```python
from loggerplusplus import opt

opt(depth=1, identifier="TRACE").info("one frame up")
```

### log_timing

```python
from loggerplusplus import log_timing

@log_timing(identifier="TASK",
            enter_message="Starting {func}...",
            exit_message="Finished {func} in {duration:.2f}s")
def slow():
    ...
```

### log_io

```python
from loggerplusplus import log_io

@log_io(identifier="CALC", log_args=True, log_return=True)
def add(a, b):
    return a + b
```

Decorators stack; each accepts a pre-bound `logger=` or an `identifier=`. `log_timing` and `log_io`
work on both sync and `async def` functions — on a coroutine they time and log the actual awaited
execution and its return value (not the coroutine object). `log_io(redact=SENSITIVE_KEYS)` masks
sensitive argument values; `log_io(max_value_length=n)` shortens huge args/returns; and
`log_timing(min_duration=s)` logs only calls at least that slow (failures are always timed).

## Capturing standard-library logging

Third-party libraries (uvicorn, SQLAlchemy, requests, ...) usually log through the standard
library `logging`. Route them through LoggerPlusPlus so they share your sinks and format:

```python
import logging
from loggerplusplus import intercept_std_logging

# Take over the root logger — everything flows through loguru:
intercept_std_logging()

# Or intercept only specific trees, tagged and at a chosen level:
intercept_std_logging(modules=["uvicorn", "sqlalchemy.engine"], level=logging.INFO)
```

Each intercepted record is re-emitted at the matching level, from the original call site, and
bound with an `identifier` (the source logger's name by default, or a fixed `identifier=`). Call
it once at start-up; it is opt-in and never runs at import time. For a specific module, `NOTSET`
inherits the parent level (typically WARNING) — pass an explicit `level` to capture below that.

## Controlling the auto-width registry

The `auto` width tracks the widest value seen per field over the process lifetime. A few public
helpers let you bound and manage that state:

```python
from loggerplusplus import set_max_auto_width, reset_widths, observed_widths, register_identifier

set_max_auto_width(24)     # no auto column ever grows past 24 cells (None removes the cap)
register_identifier("IngestWorker")  # pre-seed a width so the first line is already aligned
observed_widths()          # -> {"identifier": 12, ...} snapshot (canonical keys), a copy
reset_widths()             # forget observed widths (they re-grow from the next record)
```

`reset_widths()` is useful in long-running processes to release a column that a one-off huge value
widened. Note that `set_max_auto_width` bounds only `auto` columns, not fixed-width tokens like
`{name:<20}` — a fixed width is taken at face value.

## Multiprocessing

Use Loguru's `enqueue=True` for process-safe logging:

```python
loggerplusplus.add(sink="app.log", enqueue=True, format=formats.OpsFormat(colorized=False))
```

The auto-width registry is **per-process**: each worker aligns columns against the values *it* has
seen, so widths can differ between processes. This is by design — the registry holds process-local
state and never synchronizes across processes (a shared registry would add per-record IPC on the
logging hot path).

To align columns **across processes** without that cost, export the widths in the parent and import
them in each worker's start-up — this works for both `fork` and `spawn`:

```python
from loggerplusplus import observed_widths, import_widths

snapshot = observed_widths()          # in the parent, once widths are known

def _init(widths):                    # Process initializer, runs in each child
    import_widths(widths)
    loggerplusplus.add(sink="app.log", enqueue=True, format=formats.OpsFormat(colorized=False))

# multiprocessing.Pool(initializer=_init, initargs=(snapshot,))  # or a Process target
```

Two further notes on the start method:

- **`fork` start method:** pre-register the known identifiers in the parent *before* starting
  workers. Children inherit the seeded widths (copy-on-write), so their columns line up:

  ```python
  for name in ("Ingest", "Transform", "Load"):
      register_identifier(name)
  # ... then start the worker processes
  ```

- **`spawn` start method** (default on Windows/macOS): children re-import fresh and do **not**
  inherit the parent's sinks or registry. Configure the sink inside each child (e.g. a `Process`
  initializer that calls `loggerplusplus.add(...)` and re-registers identifiers), otherwise child
  logs fall back to Loguru's default handler.
