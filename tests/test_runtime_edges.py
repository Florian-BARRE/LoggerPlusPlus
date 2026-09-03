# ====== Code Summary ======
# Exhaustive edge coverage for runtime rendering: every alignment x truncation mode,
# the no-truncation precision hard-cut, degenerate widths, and field resolution
# (extra[...], bare fallback, dotted path with a missing step).

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pytest

from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.runtime import compose_filter


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
def test_hard_cut_without_trunc_mode(align: str, glyph: str) -> None:
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
