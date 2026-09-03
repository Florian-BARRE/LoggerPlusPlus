# Examples

Runnable examples for LoggerPlusPlus. Each is self-contained — run with `python examples/<file>`.

| File | Shows |
|---|---|
| [`01_quickstart.py`](01_quickstart.py) | Configure a sink; the identifier column self-aligns |
| [`02_formats.py`](02_formats.py) | The ready-made formats, selected by name |
| [`03_decorators.py`](03_decorators.py) | `catch` · `log_timing` · `log_io` (with secret redaction, sync + async) |
| [`04_structured_json.py`](04_structured_json.py) | `add_json()` — one JSON object per record |
| [`05_setup_and_intercept.py`](05_setup_and_intercept.py) | `setup()` + routing stdlib `logging` through loguru |
| [`06_context.py`](06_context.py) | `bind_context()` — a shared request id across a request |
| [`benchmark.py`](benchmark.py) | Micro-benchmark of the per-record auto-width filter |

```bash
python examples/01_quickstart.py
python examples/benchmark.py
```
