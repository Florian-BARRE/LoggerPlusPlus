# ====== Code Summary ======
# Behavioural coverage for `compose_filter`: placeholder padding, the three
# truncation modes, hard-cut fallback, cap logic, auto-width growth, and
# delegation to the user-supplied filter.

from __future__ import annotations

# ====== Standard Library Imports ======
from typing import Any, Dict, Optional, Tuple

# ====== Local Project Imports ======
from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.runtime import compose_filter

_AutoMap = Tuple[str, str, str, str, Optional[int], Optional[str]]


def _record(extra: Optional[Dict[str, Any]] = None, **fields: Any) -> Dict[str, Any]:
    """Build a minimal loguru-like record dict with an `extra` bag."""
    rec: Dict[str, Any] = {"extra": dict(extra or {})}
    rec.update(fields)
    return rec


def _run(fmt: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Parse `fmt`, compose the filter, run it against `record`, return record.extra."""
    _new_fmt, mappings = prepare_auto_format(fmt)
    flt = compose_filter(None, mappings)
    flt(record)
    return record["extra"]


def test_none_filter_passes() -> None:
    """With no user filter and no mappings the record always passes."""
    assert compose_filter(None, [])(_record()) is True


def test_callable_filter_is_delegated() -> None:
    """A callable user filter decides the verdict after placeholders are computed."""
    veto = compose_filter(lambda r: False, [])
    keep = compose_filter(lambda r: True, [])
    assert veto(_record()) is False
    assert keep(_record()) is True


def test_dict_filter_returns_true() -> None:
    """A dict user filter is handled by loguru elsewhere, so the wrapper returns True."""
    flt = compose_filter({"a": "INFO"}, [])
    assert flt(_record()) is True


def test_fixed_width_left_pads_right() -> None:
    """Left align pads on the right up to the fixed width."""
    extra = _run("{extra[svc]:<6}", _record({"svc": "ab"}))
    assert extra["__lp_auto_0__"] == "ab    "


def test_fixed_width_right_pads_left() -> None:
    """Right align pads on the left up to the fixed width."""
    extra = _run("{extra[svc]:>6}", _record({"svc": "ab"}))
    assert extra["__lp_auto_0__"] == "    ab"


def test_none_value_renders_dash() -> None:
    """A missing value is normalised to the '-' sentinel before padding."""
    extra = _run("{extra[missing]:<3}", _record())
    assert extra["__lp_auto_0__"] == "-  "


def test_truncate_right_appends_ellipsis() -> None:
    """`~right` keeps the head and appends an ellipsis."""
    extra = _run("{extra[svc]:<5~right}", _record({"svc": "abcdefgh"}))
    assert extra["__lp_auto_0__"] == "abcd…"


def test_truncate_left_prepends_ellipsis() -> None:
    """`~left` keeps the tail and prepends an ellipsis."""
    extra = _run("{extra[svc]:<5~left}", _record({"svc": "abcdefgh"}))
    assert extra["__lp_auto_0__"] == "…efgh"


def test_truncate_middle_keeps_both_ends() -> None:
    """`~middle` keeps head and tail around a single ellipsis."""
    extra = _run("{extra[svc]:<5~middle}", _record({"svc": "abcdefgh"}))
    assert extra["__lp_auto_0__"] == "ab…gh"
    assert len(extra["__lp_auto_0__"]) == 5


def test_hard_cut_without_trunc_mode() -> None:
    """Without a trunc mode, precision formatting hard-cuts overlong text."""
    extra = _run("{extra[svc]:<4}", _record({"svc": "abcdefgh"}))
    assert extra["__lp_auto_0__"] == "abcd"


def test_dotted_record_attribute_resolves() -> None:
    """A dotted field spec resolves through nested record objects."""

    class _Level:
        name = "INFO"

    extra = _run("{level.name:<6}", _record(level=_Level()))
    assert extra["__lp_auto_0__"] == "INFO  "


def test_auto_width_grows_monotonically() -> None:
    """Auto width tracks the widest value seen and never shrinks afterwards."""
    _fmt, mappings = prepare_auto_format("{extra[grow]:<auto}")
    flt = compose_filter(None, mappings)

    r1 = _record({"grow": "ab"})
    flt(r1)
    assert r1["extra"]["__lp_auto_0__"] == "ab"

    r2 = _record({"grow": "abcdef"})
    flt(r2)
    assert r2["extra"]["__lp_auto_0__"] == "abcdef"

    # 3. A shorter value is now padded to the previously observed maximum (6).
    r3 = _record({"grow": "xy"})
    flt(r3)
    assert r3["extra"]["__lp_auto_0__"] == "xy    "


def test_cap_limits_auto_width() -> None:
    """A cap bounds the auto width even when a longer value is observed."""
    _fmt, mappings = prepare_auto_format("{extra[capped]:<auto[3]}")
    flt = compose_filter(None, mappings)
    rec = _record({"capped": "abcdefgh"})
    flt(rec)
    assert len(rec["extra"]["__lp_auto_0__"]) == 3
