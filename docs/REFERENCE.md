# API reference and internals

## Public API

Importable from the top-level package:

```python
from loggerplusplus import (
    loggerplusplus, logger, LoggerPlusPlus, LoggerClass, formats,
    add, remove, catch, opt, log_timing, log_io, __version__,
)
```

### Singletons and classes

| Name             | Kind      | Description                                                          |
|------------------|-----------|----------------------------------------------------------------------|
| `loggerplusplus` | instance  | The enhanced proxy singleton over `loguru.logger`.                   |
| `logger`         | instance  | Alias of `loggerplusplus` (drop-in for `from loguru import logger`). |
| `LoggerPlusPlus` | class     | The proxy class; construct with `LoggerPlusPlus(core=...)`.          |
| `LoggerClass`    | class     | Mixin that provides a bound `self.logger`.                           |
| `formats`        | module    | `ClassicFormat`, `ShortFormat`, `OpsFormat`, `DebugFormat`, `MinimalFormat`. |
| `__version__`    | str       | Installed version.                                                   |

`LoggerPlusPlus` forwards every attribute to its core logger via `__getattr__` (so `.info`,
`.bind`, `.contextualize`, `.level`, ... all work) and intercepts a small override set. The
override functions operate on the process-global Loguru logger; a custom `core=` only affects
forwarded attribute access, not the overrides. Calling the singleton directly raises `TypeError`
unless its core is itself callable.

### Functions

```python
add(sink, *, level="DEBUG",
    format="{time} {level} {message}",
    filter=None, colorize=None, serialize=False,
    backtrace=False, diagnose=False, enqueue=False, catch=False,
    **kwargs) -> int
```
Adds a sink. When `format` is a string, auto-width tokens are rewritten and, if any are present,
the filter is wrapped so widths are computed per record. All other keywords are forwarded to
`loguru.logger.add`. Returns the sink id.

```python
remove(sink_id=None)
```
Loguru's `remove` (removes one sink, or all when called with no id).

```python
catch(*args, identifier=None, logger=None, **kwargs)
```
`logger.catch` with optional identifier binding or a pre-bound `logger`. Works as a decorator or a
context manager.

```python
opt(*args, identifier=None, logger=None, **kwargs)
```
`logger.opt` with the same identifier / logger convenience.

```python
log_timing(*, logger=None, identifier=None, level="DEBUG",
           enter_message=None,
           exit_message="Finished {func} in {duration:.3f}s",
           show_enter=True)
```
Decorator that logs execution time. Message templates support `{func}` and `{duration}`.

```python
log_io(*, logger=None, identifier=None, level="DEBUG",
       log_args=True, log_return=True,
       message_args="Calling {func} with args={args}, kwargs={kwargs}",
       message_return="{func} returned {result!r}")
```
Decorator that logs arguments and/or the return value.

### LoggerClass

```python
class LoggerClass:
    def __init__(self, *, identifier=None, _log_identifier=None) -> None: ...
```
Sets `self.logger = logger.bind(identifier=...)`, defaulting the identifier to the class name and
pre-registering it for early alignment. `_log_identifier` is a deprecated alias of `identifier`
(the latter takes precedence).

### formats

Each format is a `BaseFormat` subclass. Instantiating it runs `format(**overrides)` and returns a
`str`. See [FORMATS.md](FORMATS.md) for fields and overrides.

## The auto-width pipeline

`{identifier:<auto}` is not valid Loguru syntax; LoggerPlusPlus rewrites it before Loguru sees it.

1. **`parser.prepare_auto_format(fmt)`** scans the format for auto-width tokens, replaces each with
   a plain `{extra[__lp_auto_N__]}` placeholder, and returns the rewritten string plus a list of
   mappings `(field, placeholder_key, align, width_spec, cap, trunc)`. The token regex ignores
   escaped braces (`{{...}}`) and tolerates incidental whitespace in the spec.

2. **`runtime.compose_filter(user_filter, mappings)`** returns a callable that Loguru invokes once
   per record, **before formatting**. This is the only place the padded/truncated value can be
   computed and written into `record["extra"]`. It then applies the user's filter: a callable is
   delegated to, a dict is evaluated with Loguru's own per-module semantics, and `None` passes.

3. **`registry._AutoWidthRegistry` (`_AUTO`)** stores the maximum observed width per canonicalized
   field, guarded by an `RLock`. Widths grow over the process lifetime and never shrink, so columns
   stay aligned. `register_identifier()` (called by `LoggerClass`) seeds the identifier width so the
   first line is aligned.

4. **Loguru** formats the record with the rewritten string and the injected `extra` placeholders.

### Design notes

- The width computation lives in a **filter**, not a formatter function, because the filter is the
  single per-record hook Loguru runs before formatting.
- The registry is **process-global and monotonic**: Loguru formats each record with no cross-record
  memory, so alignment requires remembering the widest value for the whole process. Under
  `enqueue=True`/multiprocessing each process keeps its own registry.
- `BaseFormat` inherits `str` so an instance can be passed directly as `format=`; concrete formats
  share segment builders on the base class to avoid duplicating the layout across the five formats.

## Module map

| Module            | Responsibility                                              |
|-------------------|-------------------------------------------------------------|
| `proxy.py`        | `LoggerPlusPlus` proxy and the `loggerplusplus` singleton   |
| `api.py`          | `add()` and the raw `logger` re-export                      |
| `parser.py`       | auto-width token grammar and rewriting                      |
| `runtime.py`      | per-record width/truncation and filter composition          |
| `registry.py`     | thread-safe max-observed width registry                     |
| `logger_class.py` | `LoggerClass` mixin                                         |
| `decorators.py`   | `catch`, `opt`, `log_timing`, `log_io`                      |
| `formats/`        | `BaseFormat` and the five concrete formats                  |
