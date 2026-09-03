# Usage

A task-oriented guide. For the token grammar and formats see [FORMATS.md](FORMATS.md); for
signatures and internals see [REFERENCE.md](REFERENCE.md).

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

Decorators stack; each accepts a pre-bound `logger=` or an `identifier=`.

## Multiprocessing

Use Loguru's `enqueue=True` for process-safe logging:

```python
loggerplusplus.add(sink="app.log", enqueue=True, format=formats.OpsFormat(colorized=False))
```

Note that the auto-width registry is per-process: each worker process aligns columns against the
values *it* has seen, so widths can differ between processes. This is by design — the registry
holds process-local state and never performs inter-process synchronization.
