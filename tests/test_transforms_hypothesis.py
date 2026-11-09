# ====== Code Summary ======
# Property-based tests (Hypothesis) for the message-transform toolkit
# (`loggerplusplus.transforms`): case helpers, `chain` associativity, and `indent`'s
# "only adds the prefix" guarantee, plus the width-aware `truncate` the transforms
# are used with. They assert invariants across a wide input space instead of a
# handful of hand-picked cases.

from __future__ import annotations

from typing import List

from hypothesis import given, settings
from hypothesis import strategies as st

from loggerplusplus.transforms import chain, indent, lower, upper
from loggerplusplus.width import truncate, visual_width

# ASCII only: str.upper/str.lower round-trips are exact there (Unicode special-casing,
# e.g. 'ß' -> 'SS', makes the arbitrary-text version of these identities false).
_ascii = st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127))
# One physical line: no character that str.splitlines() treats as a line break.
_LINE_BREAKS = "\n\r\x0b\x0c\x1c\x1d\x1e\x85  "
_line = st.text(
    alphabet=st.characters(
        blacklist_characters=_LINE_BREAKS, blacklist_categories=("Cs",)
    ),
    min_size=1,
)


@settings(max_examples=50)
@given(s=_ascii)
def test_upper_lower_are_inverse_up_to_case(s: str) -> None:
    """`upper(lower(s))` restores the uppercase form: they undo each other's case change."""
    assert upper(lower(s)) == s.upper()
    assert lower(upper(s)) == s.lower()
    # Full inverse whenever the input was already uppercase (resp. lowercase).
    assert upper(lower(s.upper())) == s.upper()
    assert lower(upper(s.lower())) == s.lower()


@settings(max_examples=50)
@given(s=st.text())
def test_case_helpers_are_idempotent_and_total(s: str) -> None:
    """Any text goes through `upper`/`lower` and stays stable on a second pass."""
    assert upper(upper(s)) == upper(s)
    assert lower(lower(s)) == lower(s)


@settings(max_examples=50)
@given(
    s=st.text(),
    w=st.integers(min_value=-5, max_value=100),
    mode=st.sampled_from(["left", "right", "middle"]),
)
def test_truncate_never_exceeds_width(s: str, w: int, mode: str) -> None:
    """Truncated text never exceeds the cell width (a negative width yields nothing)."""
    out = truncate(s, w, mode)
    assert visual_width(out) <= max(w, 0)
    if w < 0:
        assert out == ""


@settings(max_examples=50)
@given(s=st.text(), w=st.integers(min_value=0, max_value=100))
def test_truncate_is_identity_when_text_fits(s: str, w: int) -> None:
    """Text already within the width is returned unchanged, whatever the mode."""
    if visual_width(s) <= w:
        assert truncate(s, w, "right") == s
        assert truncate(s, w, "left") == s
        assert truncate(s, w, "middle") == s


@settings(max_examples=50)
@given(s=_ascii)
def test_chain_is_associative(s: str) -> None:
    """Grouping does not matter: chain(f, chain(g, h)) == chain(chain(f, g), h)."""
    f, g, h = upper, indent("> "), lower
    assert chain(f, chain(g, h))(s) == chain(chain(f, g), h)(s)
    assert chain(g, chain(f, h))(s) == chain(chain(g, f), h)(s)
    # And both equal the flat chain, applied in declaration order.
    assert chain(f, chain(g, h))(s) == chain(f, g, h)(s)


@settings(max_examples=50)
@given(
    s=st.text(
        alphabet=st.characters(
            blacklist_characters=_LINE_BREAKS, blacklist_categories=("Cs",)
        )
    ),
    prefix=st.text(min_size=1, max_size=3),
)
def test_indent_single_line_only_adds_the_prefix(s: str, prefix: str) -> None:
    """A single line grows by exactly one prefix and keeps its content (empty -> prefix)."""
    out = indent(prefix)(s)
    assert len(out) == len(s) + len(prefix)
    assert out == prefix + s


@settings(max_examples=50)
@given(
    lines=st.lists(_line, min_size=1, max_size=6),
    prefix=st.text(min_size=1, max_size=3),
)
def test_indent_adds_one_prefix_per_line(lines: List[str], prefix: str) -> None:
    """The result length is len(s) plus one prefix per line; the content is untouched."""
    s = "\n".join(lines)
    out = indent(prefix)(s)
    assert len(out) == len(s) + len(lines) * len(prefix)
    assert out.splitlines() == [prefix + line for line in lines]
