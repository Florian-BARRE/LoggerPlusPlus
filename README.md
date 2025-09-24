# LoggerPlusPlus

**LoggerPlusPlus** is an enhanced Python logging module built on top of [Loguru](https://github.com/Delgan/loguru).  
It provides the same simple and powerful API, while adding extra features for better readability, productivity, and multi-logger management.

---

## ✨ Features

- **Dynamic identifier alignment**:  
  Use `{identifier:<auto}` in your log format and all identifiers will be aligned automatically, with width adapting to the longest seen identifier.

- **Truncation support**:  
  Define a maximum width with `[...]` and choose how truncation should occur: 

`{identifier:<auto[18~middle]}`
→ if the identifier is longer than 18 chars, it will be truncated with `…` in the middle.

* **LoggerClass**:
  Any class can easily get a bound logger with its class name as identifier:

  ```python
  from loggerPlusPlus import LoggerClass

  class Worker(LoggerClass):
      def run(self):
          self.logger.info("Working...")
  ```

* **Extra decorators**:

  * `@catch` → same as `loguru.logger.catch`, with optional `identifier` or a pre-bound logger.
  * `opt()` → same as `loguru.logger.opt`, extended with `identifier` or logger binding.
  * `@log_timing` → log execution time of functions (enter/exit messages configurable).
  * `@log_io` → log function parameters and/or return values.

* **Compatible with Loguru**:
  All of Loguru’s core features (sinks, levels, filters, backtraces, etc.) remain available.

---

## 🚀 Installation

```bash
pip install loggerplusplus
```

---

## 🛠 Usage

### Basic configuration

```python
from loggerplusplus import add, remove, logger

remove()
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

Output:

```
2025-09-25 14:03:12.345 | INFO     | [MAIN] | Hello from main
```

---

### LoggerClass

```python
from loggerplusplus import LoggerClass

class Service(LoggerClass):
    def run(self):
        self.logger.info("Service is running")

svc = Service()
svc.run()
```

---

### Decorators

#### Catch exceptions

```python
from loggerplusplus import catch

@catch(identifier="WORKER", level="ERROR")
def risky():
    raise RuntimeError("Boom!")

risky()
```

#### Measure execution time

```python
from loggerplusplus import log_timing
import time

@log_timing(identifier="TASK", enter_message="Starting {func}...", exit_message="Finished {func} in {duration:.2f}s")
def slow():
    time.sleep(0.5)

slow()
```

#### Log function arguments / return values

```python
from loggerplusplus import log_io

@log_io(identifier="CALC", log_args=True, log_return=True)
def add(a, b):
    return a + b

add(3, 4)
```

---

## 📜 License

loggerplusplus is licensed under the **GPLv3**.
It builds on top of Loguru (MIT license).

## Author

Project created and maintained by **Florian BARRE**.  
For any questions or contributions, feel free to contact me.  
[My Website](https://florianbarre.fr/) | [My LinkedIn](www.linkedin.com/in/barre-florian) | [My GitHub](https://github.com/Florian-BARRE)