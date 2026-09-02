# ====== Code Summary ======
# Grammar coverage for the auto-width token parser: every branch of
# `{field:<align><width>[cap~trunc]}` and the placeholder-rewrite contract.

from __future__ import annotations

# ====== Standard Library Imports ======
import re

# ====== Local Project Imports ======
from loggerplusplus.parser import _TOKEN_RE, prepare_auto_format


def test_plain_format_is_untouched() -> None:
    """A format with no auto-width token is returned verbatim with no mappings."""
    fmt = "{time} | {level} | {message}"
    new_fmt, mappings = prepare_auto_format(fmt)
    assert new_fmt == fmt
    assert mappings == []


def test_auto_token_defaults_to_left_align() -> None:
    """`{identifier:<auto}` records left align, auto width, no cap, no trunc."""
    new_fmt, mappings = prepare_auto_format("{identifier:<auto}")
    assert new_fmt == "{extra[__lp_auto_0__]}"
    field, key, align, width, cap, trunc = mappings[0]
    assert (field, key, align, width, cap, trunc) == (
        "identifier",
        "__lp_auto_0__",
        "<",
        "auto",
        None,
        None,
    )


def test_missing_align_falls_back_to_left() -> None:
    """A token without an explicit alignment glyph defaults to '<'."""
    _, mappings = prepare_auto_format("{identifier:auto}")
    assert mappings[0][2] == "<"


def test_fixed_width_with_align() -> None:
    """A numeric width and explicit alignment are captured as-is."""
    _, mappings = prepare_auto_format("{level.name:^15}")
    field, _key, align, width, cap, trunc = mappings[0]
    assert (field, align, width, cap, trunc) == ("level.name", "^", "15", None, None)


def test_cap_and_inner_trunc() -> None:
    """`[18~middle]` yields cap=18 and trunc='middle'."""
    _, mappings = prepare_auto_format("{identifier:<auto[18~middle]}")
    _field, _key, _align, _width, cap, trunc = mappings[0]
    assert cap == 18
    assert trunc == "middle"


def test_cap_without_trunc() -> None:
    """A bare `[10]` cap sets cap=10 and leaves trunc unset."""
    _, mappings = prepare_auto_format("{identifier:<auto[10]}")
    assert mappings[0][4] == 10
    assert mappings[0][5] is None


def test_outer_trunc_form() -> None:
    """The `~right` suffix form (no cap brackets) sets trunc without a cap."""
    _, mappings = prepare_auto_format("{identifier:>auto~right}")
    assert mappings[0][4] is None
    assert mappings[0][5] == "right"


def test_extra_field_spec() -> None:
    """An `extra[...]` field spec is preserved intact."""
    _, mappings = prepare_auto_format("{extra[service]:>auto[12~left]}")
    assert mappings[0][0] == "extra[service]"
    assert mappings[0][5] == "left"


def test_multiple_tokens_get_incrementing_keys() -> None:
    """Each token gets a unique positional placeholder key, in order."""
    new_fmt, mappings = prepare_auto_format("{identifier:<auto} {extra[svc]:>10}")
    assert [m[1] for m in mappings] == ["__lp_auto_0__", "__lp_auto_1__"]
    assert new_fmt == "{extra[__lp_auto_0__]} {extra[__lp_auto_1__]}"


def test_token_regex_rejects_bad_trunc() -> None:
    """An unknown trunc mode is not matched by the grammar."""
    assert _TOKEN_RE.search("{identifier:<auto[10~sideways]}") is None


def test_regex_is_compiled_pattern() -> None:
    """`_TOKEN_RE` is a compiled pattern (import-shape guard for downstream)."""
    assert isinstance(_TOKEN_RE, re.Pattern)
