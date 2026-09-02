# ====== Code Summary ======
# Coverage for the LoggerClass mixin: it binds `self.logger` with an identifier
# defaulting to the class name, and seeds the auto-width registry for alignment.

from __future__ import annotations

from loggerplusplus import LoggerClass
from loggerplusplus.registry import _AUTO, _IDENTIFIER_SPEC


def test_logger_bound_with_class_name(cap: "object") -> None:
    """A subclass gets a logger bound to its own class name by default."""
    cap.add(fmt="{extra[identifier]} {message}")

    class WorkerService(LoggerClass):
        def __init__(self) -> None:
            LoggerClass.__init__(self)

    WorkerService().logger.info("started")
    assert "WorkerService started" in cap.text


def test_explicit_identifier_overrides_class_name(cap: "object") -> None:
    """An explicit `_log_identifier` overrides the class-name default."""
    cap.add(fmt="{extra[identifier]} {message}")

    class Thing(LoggerClass):
        def __init__(self) -> None:
            LoggerClass.__init__(self, _log_identifier="CUSTOM")

    Thing().logger.warning("hi")
    assert "CUSTOM hi" in cap.text


def test_init_seeds_the_auto_width_registry() -> None:
    """Constructing a LoggerClass pre-registers its identifier width for alignment."""

    class ReallyLongServiceName(LoggerClass):
        def __init__(self) -> None:
            LoggerClass.__init__(self)

    ReallyLongServiceName()
    assert _AUTO.width(_IDENTIFIER_SPEC) >= len("ReallyLongServiceName")
