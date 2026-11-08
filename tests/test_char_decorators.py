# ====== Code Summary ======
# Phase-3 characterization safety net for the four public decorators
# (catch / opt / log_timing / log_io) and the SENSITIVE_KEYS redaction of
# loggerplusplus. It pins the CURRENT behaviour at the public boundary by
# capturing what is actually logged through the shared `cap` fixture and
# asserting byte-stable golden values. Time is frozen wherever a duration
# appears so the goldens are deterministic across runs and machines.

from __future__ import annotations

import time
from typing import List

import pytest
from loguru import logger

from loggerplusplus import SENSITIVE_KEYS, catch, log_io, log_timing, opt


def _frozen_clock(monkeypatch: "pytest.MonkeyPatch", values: List[float]) -> None:
    """Patch time.perf_counter to yield fixed values so a measured duration is
    byte-stable (monkeypatch restores the real clock on teardown)."""
    it = iter(values)
    monkeypatch.setattr(time, "perf_counter", lambda: next(it))


# =======================
#   catch
# =======================


def test_catch_default_message_and_level(cap) -> None:
    """Default catch logs the error at ERROR level with loguru's stock message."""
    cap.add(fmt="{level} | {message}")

    @catch()
    def boom() -> None:
        raise RuntimeError("kaboom")

    boom()
    assert "ERROR | " in cap.text
    assert "An error has been caught" in cap.text  # loguru's default message
    assert "RuntimeError: kaboom" in cap.text  # the exception repr is in the record


def test_catch_custom_message_deterministic(cap) -> None:
    """A custom message renders the record's exception value at ERROR level."""
    cap.add(fmt="{level} | {message}")

    @catch(message="caught: {record[exception].value}")
    def boom() -> None:
        raise ValueError("in-func")

    boom()
    assert "ERROR | caught: in-func" in cap.text
    assert "ValueError: in-func" in cap.text  # the raised exception (traceback)


def test_catch_reraise_propagates(cap) -> None:
    """With reraise=True the exception is still logged, then re-raised."""
    cap.add(fmt="{level} | {message}")

    @catch(reraise=True, message="saw {record[exception].value}")
    def boom() -> None:
        raise KeyError("k!")

    with pytest.raises(KeyError):
        boom()
    assert "ERROR | " in cap.text
    assert "saw 'k!'" in cap.text
    assert "KeyError: 'k!'" in cap.text


def test_catch_swallowed_returns_none(cap) -> None:
    """Default reraise=False swallows the error; the wrapped call returns None."""
    cap.add(fmt="{level} | {message}")

    @catch(message="swallowed {record[exception].value}")
    def boom() -> int:
        raise RuntimeError("x")
        return 99  # pragma: no cover - unreachable on the error path

    assert boom() is None  # error swallowed -> the wrapper's default (None)
    assert "swallowed x" in cap.text


# =======================
#   opt
# =======================


def test_opt_binds_identifier(cap) -> None:
    """opt(identifier=...) makes that identifier visible in the rendered record."""
    cap.add(fmt="{extra[identifier]} {message}")

    log = opt(identifier="JOB42")
    log.info("hello")

    assert "JOB42 hello" in cap.text


def test_opt_single_call(cap) -> None:
    """opt() with no arguments returns a working logger for that one call."""
    cap.add(fmt="{level} | {message}")

    opt().warning("heads up")

    assert "WARNING | heads up" in cap.text


def test_opt_depth_shifts_function(cap) -> None:
    """opt(depth=1) records the caller's function instead of the local one."""
    cap.add(fmt="fn={function} | {message}")

    def outer() -> None:
        logger.info("plain")  # depth 0 -> fn = outer
        opt(depth=1).info("deep")  # depth 1 -> fn = outer's caller (not pinned)

    outer()

    assert "fn=outer | plain" in cap.text  # the depth-0 record: fn is `outer`
    assert "deep" in cap.text  # the depth-1 record was logged too


# =======================
#   log_timing
# =======================


def test_log_timing_enter_and_exit_frozen(
    monkeypatch: "pytest.MonkeyPatch", cap
) -> None:
    """With time frozen, the enter and exit lines and the duration are exact."""
    cap.add(fmt="{level} | {message}")
    _frozen_clock(monkeypatch, [1000.0, 1000.25])  # enter, exit -> 0.250s

    @log_timing(identifier="TIMER", enter_message="Entering {func}")
    def work() -> int:
        return 42

    assert work() == 42
    assert cap.text == ("DEBUG | Entering work\n" "DEBUG | Finished work in 0.250s\n")


def test_log_timing_exit_error_frozen(monkeypatch: "pytest.MonkeyPatch", cap) -> None:
    """On failure a timed error line is logged and the exception re-raised."""
    cap.add(fmt="{level} | {message}")
    _frozen_clock(monkeypatch, [500.0, 500.1])  # enter, on_error -> 0.100s

    @log_timing(show_enter=False)
    def fail() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        fail()
    assert cap.text == "DEBUG | Failed fail after 0.100s: ValueError('nope')\n"


def test_log_timing_min_duration_suppresses_exit(
    monkeypatch: "pytest.MonkeyPatch", cap
) -> None:
    """A duration below min_duration suppresses the exit line (frozen 0.250 < 10)."""
    cap.add(fmt="{level} | {message}")
    _frozen_clock(monkeypatch, [0.0, 0.25])

    @log_timing(min_duration=10.0, show_enter=False)
    def fast() -> int:
        return 1

    assert fast() == 1
    assert cap.text == ""  # 0.250s < 10.0s -> no exit line


# =======================
#   log_io
# =======================


def test_log_io_args_and_return(cap) -> None:
    """log_io logs the call arguments and the return value for a fixed call."""
    cap.add(fmt="{level} | {message}")

    @log_io(identifier="IO")
    def add2(a: int, b: int) -> int:
        return a + b

    assert add2(2, 3) == 5
    assert cap.text == (
        "DEBUG | Calling add2 with args=(2, 3), kwargs={}\n" "DEBUG | add2 returned 5\n"
    )


def test_log_io_redact_masks_kwargs_and_positional(cap) -> None:
    """With SENSITIVE_KEYS, matching kwargs and positional args are masked as ***."""
    cap.add(fmt="{level} | {message}")

    @log_io(log_return=False, redact=SENSITIVE_KEYS)
    def login(user: str, password: str) -> bool:
        return True

    login("bob", password="hunter2")
    assert cap.text == (
        "DEBUG | Calling login with args=('bob',), kwargs={'password': '***'}\n"
    )

    cap.buf.clear()
    login2 = login  # call the same function positionally
    login2("bob", "hunter2")
    assert cap.text == "DEBUG | Calling login with args=('bob', '***'), kwargs={}\n"


def test_log_io_redact_masks_nested_dict(cap) -> None:
    """A secret nested inside a dict argument is masked; non-sensitive keys are kept."""
    cap.add(fmt="{level} | {message}")

    @log_io(log_return=False, redact=SENSITIVE_KEYS)
    def configure(cfg: dict) -> None:
        return None

    configure({"password": "hunter2", "host": "db"})
    assert (
        cap.text
        == "DEBUG | Calling configure with args=({'password': '***', 'host': 'db'},), kwargs={}\n"
    )


# =======================
#   SENSITIVE_KEYS
# =======================


def test_sensitive_keys_values() -> None:
    """The exported SENSITIVE_KEYS tuple is exactly these substrings, in order."""
    assert SENSITIVE_KEYS == (
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "credential",
        "private_key",
    )
