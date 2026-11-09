# ====== Code Summary ======
# Behavioural coverage for `compose_filter`: placeholder padding, the three
# truncation modes, hard-cut fallback, cap logic, auto-width growth, and
# delegation to the user-supplied filter. Also the exhaustive edge coverage of
# runtime rendering: every alignment x truncation mode, the no-truncation
# precision hard-cut, degenerate widths, and field resolution (extra[...], bare
# fallback, dotted path with a missing step).

from __future__ import annotations

# ====== Standard Library Imports ======
from types import SimpleNamespace
from typing import Any, Dict, Optional, Tuple

import pytest

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


def _render(token: str, record: Dict[str, Any]) -> str:
    """Render a single-token format against `record` and return the computed placeholder."""
    _fmt, mappings = prepare_auto_format(token)
    compose_filter(None, mappings)(record)
    return record["extra"]["__lp_auto_0__"]


def _rec(**extra: Any) -> Dict[str, Any]:
    """Record carrying only an extra bag."""
    return {"extra": dict(extra)}


# --- truncation x alignment (value longer than width) --------------------------------


@pytest.mark.parametrize(
    "token, expected",
    [
        ("{extra[x]:<5~right}", "abcd…"),
        ("{extra[x]:>5~right}", "abcd…"),  # already width chars -> no extra padding
        ("{extra[x]:^5~right}", "abcd…"),
        ("{extra[x]:<5~left}", "…wxyz"),
        ("{extra[x]:>5~left}", "…wxyz"),
        ("{extra[x]:^5~left}", "…wxyz"),
        ("{extra[x]:<5~middle}", "ab…yz"),
        ("{extra[x]:>5~middle}", "ab…yz"),
        ("{extra[x]:^5~middle}", "ab…yz"),
    ],
)
def test_truncation_modes_and_alignment(token: str, expected: str) -> None:
    """Every mode x alignment truncates to exactly the width with an ellipsis."""
    out = _render(token, _rec(x="abcdefghijklmnopqrstuvwxyz"))
    assert out == expected
    assert len(out) == 5


# --- no-trunc precision hard-cut x alignment -----------------------------------------


@pytest.mark.parametrize("align, glyph", [("<", "<"), (">", ">"), ("^", "^")])
def test_hard_cut_without_trunc_mode_for_every_alignment(
    align: str, glyph: str
) -> None:
    """Without a trunc mode, overlong text is hard-cut to width by format precision."""
    out = _render(f"{{extra[x]:{align}4}}", _rec(x="abcdefgh"))
    assert out == "abcd"


# --- degenerate widths ---------------------------------------------------------------


@pytest.mark.parametrize("mode", ["left", "right", "middle"])
def test_degenerate_width_one(mode: str) -> None:
    """Width 1 with a trunc mode falls back to a single-char hard cut (no ellipsis)."""
    out = _render(f"{{extra[x]:<1~{mode}}}", _rec(x="abcdef"))
    assert out == "a"


def test_padding_shorter_than_width() -> None:
    """A value shorter than the width is padded, not truncated."""
    assert _render("{extra[x]:<6~middle}", _rec(x="ab")) == "ab    "
    assert _render("{extra[x]:>6~middle}", _rec(x="ab")) == "    ab"
    assert _render("{extra[x]:^6~middle}", _rec(x="ab")) == "  ab  "


# --- field resolution ----------------------------------------------------------------


def test_explicit_extra_lookup() -> None:
    """`extra[key]` resolves from the record's extra bag."""
    assert _render("{extra[svc]:<3}", _rec(svc="db")) == "db "


def test_bare_field_falls_back_to_extra() -> None:
    """A bare field name resolves from extra when it is not a top-level record key."""
    assert _render("{identifier:<3}", _rec(identifier="ab")) == "ab "


def test_dotted_path_resolves_through_attributes() -> None:
    """A dotted spec walks nested record objects."""
    rec = {"extra": {}, "level": SimpleNamespace(name="INFO")}
    assert _render("{level.name:<6}", rec) == "INFO  "


def test_dotted_path_missing_step_becomes_dash() -> None:
    """An unresolvable dotted path yields the '-' sentinel."""
    rec = {"extra": {}, "level": SimpleNamespace(name="INFO")}
    assert _render("{level.color.hex:<3}", rec) == "-  "


def test_missing_value_is_dash() -> None:
    """A field absent everywhere renders the '-' sentinel."""
    assert _render("{extra[nope]:<3}", _rec()) == "-  "


def test_none_intermediate_in_path_returns_dash() -> None:
    """A None value mid-path stops resolution and yields the sentinel."""
    rec = {"extra": {}, "obj": SimpleNamespace(child=None)}
    assert _render("{obj.child.deep:<3}", rec) == "-  "


def test_fixed_width_with_cap_limits_width() -> None:
    """A fixed width combined with a cap uses the smaller of the two."""
    assert _render("{extra[x]:<5[3]}", _rec(x="abcdefgh")) == "abc"


def test_dict_filter_accepts_integer_level_value() -> None:
    """An int value in a dict filter is compared directly against record level.no."""
    flt = compose_filter({"": 25}, [])
    assert flt({"name": "m", "level": SimpleNamespace(no=20), "extra": {}}) is False
    assert flt({"name": "m", "level": SimpleNamespace(no=30), "extra": {}}) is True


def test_unknown_trunc_mode_falls_back_to_hard_cut() -> None:
    """A mapping carrying an unknown trunc mode hard-cuts instead of raising."""
    mapping = ("extra[x]", "__lp_auto_0__", "<", "5", None, "weird")
    rec = _rec(x="abcdefgh")
    compose_filter(None, [mapping])(rec)
    assert rec["extra"]["__lp_auto_0__"] == "abcde"
