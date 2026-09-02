# ====== Code Summary ======
# Behavioural coverage for the decorators: `catch` (decorator + context manager),
# `opt` (identifier and pre-bound logger), `log_timing`, `log_io`, and the
# `_select_logger` resolution helper.

from __future__ import annotations

from loguru import logger

from loggerplusplus.decorators import _select_logger, catch, log_io, log_timing, opt


def test_select_logger_prefers_explicit_logger() -> None:
    """A provided logger is returned unchanged."""
    sentinel = logger.bind(identifier="EXPLICIT")
    assert _select_logger(logger=sentinel, identifier="IGNORED") is sentinel


def test_select_logger_binds_identifier_when_no_logger(cap: "object") -> None:
    """Without a logger, the identifier is bound onto the global logger."""
    cap.add(fmt="{extra[identifier]} {message}")
    _select_logger(identifier="BOUND").info("m")
    assert "BOUND m" in cap.text


def test_select_logger_falls_back_to_global() -> None:
    """With neither argument, the untouched global logger is returned."""
    assert _select_logger() is logger


def test_catch_as_decorator_logs_exception(cap: "object") -> None:
    """`catch` used as a decorator records the raised exception."""
    cap.add()

    @catch(identifier="DEC", reraise=False)
    def boom() -> None:
        raise RuntimeError("kaboom")

    boom()
    assert "RuntimeError" in cap.text
    assert "kaboom" in cap.text


def test_catch_as_context_manager_swallows_and_logs(cap: "object") -> None:
    """`catch` used as a context manager catches and logs the exception."""
    cap.add()
    with catch(identifier="CTX"):
        raise ValueError("in-context")
    assert "ValueError" in cap.text
    assert "in-context" in cap.text


def test_catch_with_prebound_logger(cap: "object") -> None:
    """`catch` accepts a pre-bound logger which takes precedence."""
    cap.add()
    bound = logger.bind(identifier="PREBOUND")

    @catch(logger=bound, reraise=False)
    def boom() -> None:
        raise KeyError("k")

    boom()
    assert "KeyError" in cap.text


def test_opt_with_identifier_binds_extra(cap: "object") -> None:
    """`opt(identifier=...)` binds the identifier visible in extra."""
    cap.add(fmt="{extra[identifier]} {message}")
    log = opt(identifier="OPT_ID")
    log.info("hello")
    assert "OPT_ID hello" in cap.text


def test_opt_with_prebound_logger(cap: "object") -> None:
    """`opt(logger=...)` reuses a pre-bound logger."""
    cap.add(fmt="{extra[identifier]} {message}")
    bound = logger.bind(identifier="OPT_LOG")
    log = opt(logger=bound, colors=False)
    log.warning("heads up")
    assert "OPT_LOG heads up" in cap.text


def test_log_timing_logs_enter_and_exit_with_duration(cap: "object") -> None:
    """`log_timing` logs the enter message and an exit message with a duration."""
    cap.add()

    @log_timing(
        identifier="TIMER",
        enter_message="Entering {func}",
        exit_message="Done {func} in {duration:.3f}s",
    )
    def work() -> int:
        return 42

    assert work() == 42
    assert "Entering work" in cap.text
    assert "Done work in" in cap.text
    assert "s" in cap.text


def test_log_timing_can_skip_enter_message(cap: "object") -> None:
    """With show_enter False (or no enter_message) only the exit line is logged."""
    cap.add()

    @log_timing(identifier="TIMER2", show_enter=False)
    def work() -> str:
        return "ok"

    assert work() == "ok"
    assert "Finished work" in cap.text


def test_log_io_logs_args_and_return(cap: "object") -> None:
    """`log_io` logs both the call arguments and the return value."""
    cap.add()

    @log_io(identifier="IO", log_args=True, log_return=True)
    def add2(a: int, b: int) -> int:
        return a + b

    assert add2(2, 3) == 5
    assert "Calling add2 with args=(2, 3)" in cap.text
    assert "add2 returned 5" in cap.text


def test_log_io_can_disable_both_sides(cap: "object") -> None:
    """With log_args and log_return False the wrapper stays silent but still runs."""
    cap.add()

    @log_io(identifier="IO2", log_args=False, log_return=False)
    def mul(a: int, b: int) -> int:
        return a * b

    assert mul(4, 5) == 20
    assert "mul" not in cap.text


def test_log_io_uses_global_logger_without_identifier(cap: "object") -> None:
    """When no identifier/logger is given the decorator uses the global logger."""
    cap.add()

    @log_io(log_args=True, log_return=False)
    def echo(x: int) -> int:
        return x

    assert echo(7) == 7
    assert "Calling echo" in cap.text
