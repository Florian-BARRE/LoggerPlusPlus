# ====== Code Summary ======
# Phase 5 structure-resolves net for the R-01 move: the transform layer was re-homed from the two
# flat root modules (`transforms.py`, `banners.py`) into the `transforms/` sub-package. This file
# is NOT a behaviour re-test (the Phase-3 char nets already pin that) — it documents the NEW home:
# the package `__init__` exposes the same public names the old root module did, and `Banner` is the
# same object at both the top level and the submodule path.

from __future__ import annotations

import loggerplusplus
from loggerplusplus import transforms
from loggerplusplus.transforms import Banner, Transform, chain, indent, lower, upper

# The FROZEN submodule surface: exactly the names the old root `transforms` module exported.
_EXPECTED_NAMES = ("Transform", "Banner", "chain", "indent", "upper", "lower")


def test_package_exposes_the_frozen_surface() -> None:
    """`transforms` (now a package) resolves every name the old root module used to."""
    for name in _EXPECTED_NAMES:
        assert hasattr(transforms, name), f"transforms.{name} is missing after the move"
    # The package advertises the same `__all__` the old module had.
    assert sorted(transforms.__all__) == sorted(_EXPECTED_NAMES)


def test_banner_is_the_same_object_at_both_paths() -> None:
    """`loggerplusplus.Banner` and `loggerplusplus.transforms.Banner` are one object."""
    assert loggerplusplus.Banner is loggerplusplus.transforms.Banner
    assert Banner is loggerplusplus.Banner


def test_moved_units_render_unchanged() -> None:
    """A couple of the moved helpers still produce the same output at their new home."""
    assert upper("hi") == "HI"
    assert lower("Hi") == "hi"
    assert indent(">> ")("a\nb") == ">> a\n>> b"
    assert chain(upper, indent("p:"))("ab") == "p:AB"
    # The `Transform` alias remains a plain `str -> str` annotation target.
    f: Transform = upper
    assert f("q") == "Q"
