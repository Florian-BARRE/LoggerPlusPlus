# ====== Code Summary ======
# Tests for the visual-width text engine: measuring, truncating, padding, and the
# full render pipeline for CJK/full-width and combining characters (bug B9).

from __future__ import annotations

import pytest

from loggerplusplus.width import (
    hard_cut,
    pad,
    render_field,
    truncate,
    visual_width,
)

# 漢 字 語 : each is East-Asian Wide -> 2 cells. "a" + U+0301 combining acute -> 1 cell.
_WIDE = "漢字語"  # visual width 6
_COMBINING = "á"  # 'á' as base + combining mark -> 1 cell, 2 code points


def test_visual_width_ascii_equals_len() -> None:
    """ASCII width equals code-point length."""
    assert visual_width("hello") == 5


def test_visual_width_wide_chars_count_two() -> None:
    """East-Asian wide/full-width characters count as two cells each."""
    assert visual_width(_WIDE) == 6
    assert visual_width("１２３") == 6  # full-width digits


def test_visual_width_combining_counts_zero() -> None:
    """Combining marks and zero-width characters add no cells."""
    assert visual_width(_COMBINING) == 1
    assert visual_width("a​b") == 2  # zero-width space between two letters


def test_hard_cut_respects_cells_not_codepoints() -> None:
    """hard_cut never exceeds the cell budget, even splitting wide runs."""
    assert visual_width(hard_cut(_WIDE, 3)) <= 3
    assert hard_cut(_WIDE, 4) == "漢字"  # exactly two wide chars fill 4 cells


@pytest.mark.parametrize("mode", ["left", "right", "middle"])
def test_truncate_wide_never_exceeds_width(mode: str) -> None:
    """Truncation of wide text stays within the cell width and adds an ellipsis."""
    out = truncate("漢字語漢字語", 5, mode)
    assert visual_width(out) <= 5
    assert "…" in out


def test_truncate_wide_middle_keeps_both_ends() -> None:
    """Middle truncation of wide text keeps a head and a tail around the ellipsis."""
    assert truncate("漢字語", 5, "middle") == "漢…語"


def test_pad_wide_fills_to_cells() -> None:
    """Padding accounts for wide cells, not code points."""
    assert pad("漢", 4, "<") == "漢  "  # 2 cells + 2 spaces
    assert pad("漢", 4, ">") == "  漢"
    assert pad("漢", 5, "^") == " 漢  "  # gap 3 -> 1 left, 2 right


@pytest.mark.parametrize(
    "value,width,align,trunc",
    [
        ("漢字語漢", 6, "<", None),
        ("漢字語漢", 6, ">", "right"),
        ("漢字語漢", 5, "^", "middle"),
        ("漢字", 7, "<", None),
        (_COMBINING, 4, "<", None),
        ("x", 1, "<", "middle"),
    ],
)
def test_render_field_fills_exactly_width_cells(
    value: str, width: int, align: str, trunc: str
) -> None:
    """render_field always produces a column of exactly `width` visual cells."""
    assert visual_width(render_field(value, width, align, trunc)) == width


def test_render_field_ascii_is_unchanged_behavior() -> None:
    """For ASCII, render_field matches the classic pad/precision behavior."""
    assert render_field("ab", 5, "<", None) == "ab   "
    assert render_field("ab", 5, ">", None) == "   ab"
    assert render_field("abcdef", 4, "<", None) == "abcd"
    assert render_field("abcdef", 5, "<", "right") == "abcd…"
    assert render_field("abcdef", 5, "<", "left") == "…cdef"
    assert render_field("abcdef", 5, "<", "middle") == "ab…ef"
