# ====== Code Summary ======
# Tests for color themes (audit item B12): the default theme reproduces the historical
# colors exactly (also guarded by the format snapshots), and a custom theme recolors the
# themeable segments while leaving structure and the dynamic level/message color intact.

from __future__ import annotations

import dataclasses

import pytest

from loggerplusplus import DEFAULT_THEME, Theme, formats


def test_default_theme_equals_no_theme() -> None:
    """Passing DEFAULT_THEME explicitly is identical to passing nothing."""
    assert str(formats.ClassicFormat()) == str(
        formats.ClassicFormat(theme=DEFAULT_THEME)
    )
    assert str(formats.DebugFormat()) == str(formats.DebugFormat(theme=DEFAULT_THEME))


def test_default_theme_uses_historical_colors() -> None:
    """The default theme keeps the exact color tags the formats shipped with."""
    out = str(formats.DebugFormat())
    for tag in (
        "<yellow>",
        "<light-green>",
        "<cyan>",
        "<light-cyan>",
        "<magenta>",
        "<light-magenta>",
        "<light-black>",
    ):
        assert tag in out


def test_custom_theme_recolors_segments() -> None:
    """A custom theme replaces the themeable colors and drops the defaults."""
    theme = Theme(timestamp="red", identifier="blue", separator="white")
    out = str(formats.ShortFormat(theme=theme))
    assert "<red>" in out
    assert "<blue>" in out
    assert "<white>" in out
    assert "<yellow>" not in out  # default timestamp color replaced
    assert "<light-green>" not in out  # default identifier color replaced
    # The dynamic level/message color is intentionally not themeable.
    assert "<level>" in out


def test_theme_is_immutable() -> None:
    """Theme is a frozen dataclass; attributes cannot be reassigned."""
    theme = Theme()
    with pytest.raises(dataclasses.FrozenInstanceError):
        theme.timestamp = "red"  # type: ignore[misc]


def test_theme_defaults() -> None:
    """The default theme exposes the documented color roles."""
    t = Theme()
    assert (t.timestamp, t.identifier, t.separator) == (
        "yellow",
        "light-green",
        "light-black",
    )
    assert (t.process, t.thread) == ("cyan", "light-cyan")
    assert (t.name, t.line) == ("magenta", "light-magenta")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"separator": "not-a-color"},
        {"identifier": ""},
        {"timestamp": "red>{message}<red"},
        {"name": "<script>"},
        {"line": "green>x</green"},
    ],
)
def test_invalid_color_rejected_at_construction(kwargs: dict) -> None:
    """An invalid/empty/markup-bearing color fails fast at Theme construction."""
    with pytest.raises(ValueError):
        Theme(**kwargs)


def test_invalid_color_error_names_the_field() -> None:
    """The validation error names the offending field."""
    with pytest.raises(ValueError, match="Theme.separator"):
        Theme(separator="bogus")


@pytest.mark.parametrize(
    "color",
    ["red", "light-green", "dim", "italic", "#ff8800", "fg 200", "bg red", "201"],
)
def test_valid_color_forms_accepted(color: str) -> None:
    """Named colors, attributes, hex, 8-bit, and fg/bg forms are accepted."""
    Theme(timestamp=color)  # must not raise


def test_theme_none_falls_back_to_default() -> None:
    """theme=None renders exactly like the default theme (no AttributeError)."""
    assert str(formats.ShortFormat(theme=None)) == str(formats.ShortFormat())
    assert str(formats.DebugFormat(theme=None)) == str(formats.DebugFormat())


def test_non_theme_object_rejected() -> None:
    """Passing a non-Theme object as theme raises a clear TypeError."""
    with pytest.raises(TypeError):
        formats.ShortFormat(theme="cyan")


def test_colorized_false_drops_theme_colors() -> None:
    """A custom theme with colorized=False still yields a fully tag-free template."""
    theme = Theme(timestamp="red", identifier="blue")
    out = str(formats.DebugFormat(theme=theme, colorized=False))
    assert "</" not in out  # no closing color tags (bare `<` is the align glyph)
