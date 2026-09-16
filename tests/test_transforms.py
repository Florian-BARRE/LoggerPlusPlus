# ====== Code Summary ======
# Tests for the `transforms` toolkit: the small composable string helpers (chain, indent,
# upper, lower) and the `Transform` type alias re-exports. Banners have their own module
# (test_banners.py); the transform-keyword plumbing lives in test_transform_proxy.py.

from __future__ import annotations

from loggerplusplus import transforms
from loggerplusplus.transforms import Banner, Transform, chain, indent, lower, upper


def test_upper_and_lower() -> None:
    """`upper`/`lower` are plain string transforms."""
    assert upper("Hello") == "HELLO"
    assert lower("Hello") == "hello"


def test_chain_applies_in_declaration_order() -> None:
    """`chain` composes left-to-right: the first transform runs first."""
    # A lowercase prefix makes ordering observable: only the transforms that run AFTER
    # `indent` see (and could uppercase) the prefix.
    upper_then_indent = chain(upper, indent("p:"))
    assert upper_then_indent("ab") == "p:AB"  # prefix stays lowercase

    indent_then_upper = chain(indent("p:"), upper)
    assert indent_then_upper("ab") == "P:AB"  # prefix uppercased too


def test_chain_empty_is_identity() -> None:
    """`chain()` with no transforms returns the text unchanged."""
    assert chain()("unchanged") == "unchanged"


def test_indent_prefixes_every_line() -> None:
    """`indent` prepends the prefix to each line of a multi-line message."""
    assert indent(">> ")("a\nb") == ">> a\n>> b"


def test_indent_default_prefix() -> None:
    """`indent` defaults to a four-space prefix."""
    assert indent()("x") == "    x"


def test_indent_empty_text_yields_the_bare_prefix() -> None:
    """An empty message has no lines, so `indent` degrades to just the prefix."""
    assert indent("# ")("") == "# "


def test_transform_alias_and_reexports() -> None:
    """`Transform` is the Callable alias and `Banner` is re-exported here."""
    # The alias is usable as an annotation target and is the documented Callable[[str], str].
    f: Transform = upper
    assert f("q") == "Q"
    # Banner is re-exported so both `transforms.Banner` and top-level `Banner` resolve.
    assert transforms.Banner is Banner
