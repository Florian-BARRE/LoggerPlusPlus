# ====== Code Summary ======
# Property-based tests (Hypothesis) for the pure parser/runtime core. These assert
# invariants across a wide input space instead of a handful of hand-picked cases.

from __future__ import annotations

from typing import Any, Dict

from hypothesis import given
from hypothesis import strategies as st

from loggerplusplus.parser import prepare_auto_format
from loggerplusplus.runtime import compose_filter

_MODES = ["left", "right", "middle"]


def _render(token: str, value: str) -> str:
    """Render one fixed-width token for `value` and return the padded placeholder."""
    _fmt, mappings = prepare_auto_format(token)
    rec: Dict[str, Any] = {"extra": {"x": value}}
    compose_filter(None, mappings)(rec)
    return rec["extra"]["__lp_auto_0__"]


@given(
    value=st.text(max_size=120),
    width=st.integers(min_value=1, max_value=60),
    mode=st.sampled_from(_MODES),
)
def test_fixed_width_output_is_exactly_width(value: str, width: int, mode: str) -> None:
    """A fixed-width truncating token always yields a string of exactly `width` chars."""
    out = _render(f"{{extra[x]:<{width}~{mode}}}", value)
    assert len(out) == width


@given(
    value=st.text(min_size=3, max_size=120),
    width=st.integers(min_value=2, max_value=40),
)
def test_right_truncation_keeps_the_prefix(value: str, width: int) -> None:
    """`~right` on an overlong value keeps the head and ends with the ellipsis."""
    if len(value) <= width:
        return
    out = _render(f"{{extra[x]:<{width}~right}}", value)
    assert out.endswith("…")
    assert out[:-1] == value[: width - 1]


@given(
    value=st.text(min_size=3, max_size=120),
    width=st.integers(min_value=2, max_value=40),
)
def test_left_truncation_keeps_the_suffix(value: str, width: int) -> None:
    """`~left` on an overlong value keeps the tail and starts with the ellipsis."""
    if len(value) <= width:
        return
    out = _render(f"{{extra[x]:<{width}~left}}", value)
    assert out.startswith("…")
    assert out[1:] == value[-(width - 1) :]


@given(n=st.integers(min_value=0, max_value=25))
def test_parser_emits_one_sequential_mapping_per_token(n: int) -> None:
    """N auto tokens produce N mappings with unique, sequential placeholder keys."""
    fmt = " ".join(f"{{f{i}:<auto}}" for i in range(n))
    new_fmt, mappings = prepare_auto_format(fmt)
    assert len(mappings) == n
    assert [m[1] for m in mappings] == [f"__lp_auto_{i}__" for i in range(n)]
    for i in range(n):
        assert f"{{extra[__lp_auto_{i}__]}}" in new_fmt
