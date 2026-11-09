# ====== Code Summary ======
# Behavioural coverage for the decorators: `catch` (decorator + context manager),
# `opt` (identifier and pre-bound logger), `log_timing`, `log_io`, and the
# `_select_logger` resolution helper. Also the enriched decorators (audit item B11):
# log_io argument redaction and value truncation, and log_timing's slow-call
# threshold; and the Phase-3 characterization safety net for the four public
# decorators and the SENSITIVE_KEYS redaction (byte-stable goldens, time frozen
# wherever a duration appears).
#
# Characterization goldens moved to ``tests/test_decorators_char.py``.

from __future__ import annotations

from typing import List

import pytest
from loguru import logger

from loggerplusplus import SENSITIVE_KEYS
from loggerplusplus.decorators import (
    _redact_call,
    _select_logger,
    _shorten,
    catch,
    log_io,
    log_timing,
    opt,
)

# Shared harness helpers (fixtures auto-imported by pytest):
from tests.conftest import _frozen_clock  # noqa: F401


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


def test_log_io_redacts_sensitive_kwargs(custom_cap: List[str]) -> None:
    """A kwarg whose name matches SENSITIVE_KEYS has its value masked."""

    @log_io(redact=SENSITIVE_KEYS, log_return=False)
    def login(user: str, password: str) -> bool:
        return True

    login("bob", password="hunter2")
    text = "".join(custom_cap)
    assert "hunter2" not in text
    assert "***" in text
    assert "bob" in text  # non-sensitive args are untouched


def test_log_io_custom_redact_patterns(custom_cap: List[str]) -> None:
    """A custom redact pattern masks a matching kwarg by name substring."""

    @log_io(redact=["pin"], log_return=False)
    def pay(amount: int, card_pin: str) -> None:
        return None

    pay(10, card_pin="4321")
    text = "".join(custom_cap)
    assert "4321" not in text
    assert "***" in text


def test_log_io_truncates_long_values(custom_cap: List[str]) -> None:
    """A value whose repr exceeds max_value_length is shortened with an ellipsis."""

    @log_io(max_value_length=8, log_args=True, log_return=True)
    def echo(blob: str) -> str:
        return blob

    echo("A" * 50)
    text = "".join(custom_cap)
    assert "…" in text
    assert "A" * 50 not in text  # the full value never appears


def test_log_io_defaults_are_unchanged(custom_cap: List[str]) -> None:
    """With no redact/truncation, values are logged verbatim."""

    @log_io()
    def add(a: int, b: int) -> int:
        return a + b

    add(3, 5)
    text = "".join(custom_cap)
    assert "args=(3, 5)" in text
    assert "returned 8" in text


def test_log_timing_min_duration_suppresses_fast_calls(custom_cap: List[str]) -> None:
    """With a high threshold, a fast call logs no exit message."""

    @log_timing(min_duration=10.0, show_enter=False)
    def fast() -> int:
        return 1

    fast()
    assert not any("Finished" in m for m in custom_cap)


def test_log_timing_min_duration_zero_still_logs(custom_cap: List[str]) -> None:
    """A threshold of 0 logs every call."""

    @log_timing(min_duration=0.0, show_enter=False)
    def fast() -> int:
        return 1

    fast()
    assert any("Finished" in m for m in custom_cap)


def test_log_io_redacts_positional_secret(custom_cap: List[str]) -> None:
    """A secret passed positionally is masked via the function signature (B1)."""

    @log_io(redact=SENSITIVE_KEYS, log_return=False)
    def login(user: str, password: str) -> bool:
        return True

    login("bob", "hunter2")  # password is POSITIONAL here
    text = "".join(custom_cap)
    assert "hunter2" not in text
    assert "***" in text
    assert "bob" in text


def test_log_io_redacts_nested_dict_secret(custom_cap: List[str]) -> None:
    """A secret nested in a dict argument is masked recursively (B1)."""

    @log_io(redact=SENSITIVE_KEYS, log_return=False)
    def configure(config: dict) -> None:
        return None

    configure(config={"password": "hunter2", "host": "db"})
    text = "".join(custom_cap)
    assert "hunter2" not in text
    assert "host" in text  # non-sensitive nested keys are kept


def test_log_timing_times_and_reraises_on_failure(custom_cap: List[str]) -> None:
    """A failing call still logs a timed failure message and re-raises (B2)."""

    @log_timing(show_enter=False)
    def boom() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        boom()
    text = "".join(custom_cap)
    assert "Failed boom" in text
    assert "nope" in text  # {error!r}


def test_logging_never_aborts_the_decorated_function(custom_cap: List[str]) -> None:
    """An argument whose repr raises must not abort the call or propagate (B4)."""

    class Bad:
        def __repr__(self) -> str:
            raise RuntimeError("repr boom")

    ran: List[bool] = []

    @log_io()
    def use(x: object) -> str:
        ran.append(True)
        return "ok"

    result = use(
        Bad()
    )  # custom_cap has a DEBUG sink -> build() runs -> repr raises -> swallowed
    assert result == "ok"
    assert ran == [True]


def test_redact_call_handles_signatureless_callable() -> None:
    """A signature-less callable does not crash redaction; kwargs still mask by name."""
    args, kwargs = _redact_call(object(), ("secret",), {"password": "x"}, ("password",))
    assert kwargs == {"password": "***"}
    assert args == ("secret",)  # positional not name-redacted without a signature


def test_shorten_edge_cases() -> None:
    """_shorten returns short values unchanged and degrades gracefully at tiny limits."""
    assert _shorten("ab", 10) == "ab"  # repr fits under the limit -> unchanged
    assert _shorten("abcdef", 1) == "…"  # no room for any content
    assert _shorten(12345, None) == 12345  # None -> no-op
