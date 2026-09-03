# ====== Code Summary ======
# Tests for the enriched decorators (audit item B11): log_io argument redaction and
# value truncation, and log_timing's slow-call threshold. Defaults must preserve the
# original behavior (covered by test_decorators.py).

from __future__ import annotations

from typing import Any, List

import pytest
from loguru import logger

from loggerplusplus import SENSITIVE_KEYS, log_io, log_timing
from loggerplusplus.decorators import _redact_call, _shorten


@pytest.fixture
def cap() -> Any:
    """Capture emitted log messages to a list, then remove the sink."""
    messages: List[str] = []
    sink_id = logger.add(messages.append, level="DEBUG", format="{message}")
    try:
        yield messages
    finally:
        logger.remove(sink_id)


def test_log_io_redacts_sensitive_kwargs(cap: List[str]) -> None:
    """A kwarg whose name matches SENSITIVE_KEYS has its value masked."""

    @log_io(redact=SENSITIVE_KEYS, log_return=False)
    def login(user: str, password: str) -> bool:
        return True

    login("bob", password="hunter2")
    text = "".join(cap)
    assert "hunter2" not in text
    assert "***" in text
    assert "bob" in text  # non-sensitive args are untouched


def test_log_io_custom_redact_patterns(cap: List[str]) -> None:
    """A custom redact pattern masks a matching kwarg by name substring."""

    @log_io(redact=["pin"], log_return=False)
    def pay(amount: int, card_pin: str) -> None:
        return None

    pay(10, card_pin="4321")
    text = "".join(cap)
    assert "4321" not in text
    assert "***" in text


def test_log_io_truncates_long_values(cap: List[str]) -> None:
    """A value whose repr exceeds max_value_length is shortened with an ellipsis."""

    @log_io(max_value_length=8, log_args=True, log_return=True)
    def echo(blob: str) -> str:
        return blob

    echo("A" * 50)
    text = "".join(cap)
    assert "…" in text
    assert "A" * 50 not in text  # the full value never appears


def test_log_io_defaults_are_unchanged(cap: List[str]) -> None:
    """With no redact/truncation, values are logged verbatim."""

    @log_io()
    def add(a: int, b: int) -> int:
        return a + b

    add(3, 5)
    text = "".join(cap)
    assert "args=(3, 5)" in text
    assert "returned 8" in text


def test_log_timing_min_duration_suppresses_fast_calls(cap: List[str]) -> None:
    """With a high threshold, a fast call logs no exit message."""

    @log_timing(min_duration=10.0, show_enter=False)
    def fast() -> int:
        return 1

    fast()
    assert not any("Finished" in m for m in cap)


def test_log_timing_min_duration_zero_still_logs(cap: List[str]) -> None:
    """A threshold of 0 logs every call."""

    @log_timing(min_duration=0.0, show_enter=False)
    def fast() -> int:
        return 1

    fast()
    assert any("Finished" in m for m in cap)


def test_log_io_redacts_positional_secret(cap: List[str]) -> None:
    """A secret passed positionally is masked via the function signature (B1)."""

    @log_io(redact=SENSITIVE_KEYS, log_return=False)
    def login(user: str, password: str) -> bool:
        return True

    login("bob", "hunter2")  # password is POSITIONAL here
    text = "".join(cap)
    assert "hunter2" not in text
    assert "***" in text
    assert "bob" in text


def test_log_io_redacts_nested_dict_secret(cap: List[str]) -> None:
    """A secret nested in a dict argument is masked recursively (B1)."""

    @log_io(redact=SENSITIVE_KEYS, log_return=False)
    def configure(config: dict) -> None:
        return None

    configure(config={"password": "hunter2", "host": "db"})
    text = "".join(cap)
    assert "hunter2" not in text
    assert "host" in text  # non-sensitive nested keys are kept


def test_log_timing_times_and_reraises_on_failure(cap: List[str]) -> None:
    """A failing call still logs a timed failure message and re-raises (B2)."""

    @log_timing(show_enter=False)
    def boom() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        boom()
    text = "".join(cap)
    assert "Failed boom" in text
    assert "nope" in text  # {error!r}


def test_logging_never_aborts_the_decorated_function(cap: List[str]) -> None:
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
    )  # cap has a DEBUG sink -> build() runs -> repr raises -> swallowed
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
