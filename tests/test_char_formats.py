# ====== Code Summary ======
# Characterisation safety-net for the formats + themes boundary.
#
# These tests pin the CURRENT rendered behaviour of the seven shipped formats
# (Classic, Short, Ops, Debug, Minimal, File, Plain) plus the Theme/DEFAULT_THEME
# overrides, at the public boundary, so a later behaviour-preserving refactor can
# prove it changed nothing.
#
# What is pinned (all captured by running the current code and reading the real
# output — do not "fix" a golden to make a refactor pass; a diff means downstream
# log output changed):
#   1. TEMPLATE goldens — str(cls()) and str(cls(colorized=False)) for every format.
#   2. FULL rendered line — one record through the public add() path (the only path
#      that runs the auto-width pipeline), plain, with frozen time/pid/tid/auto-width.
#   3. Alignment — identifiers of different visual widths render to the SAME column
#      width (the library's core purpose).
#   4. Theme overrides — a custom Theme changes the rendered template; colorized=False
#      drops theme colors; the default Theme renders the documented default.
#
# Determinism: no wall-clock, no real pid/tid, no dependence on the global auto-width
# registry left by other tests. The _frozen() context patches loguru's aware_now,
# os.getpid and threading.get_ident to fixed values and seeds the auto-width registry
# so every render is byte-stable across runs, machines and test order.

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, List, Mapping, Optional
from unittest import mock

import pytest

import loggerplusplus as lpp
from loggerplusplus import DEFAULT_THEME, Theme
from loggerplusplus import formats as F

# Frozen values (see _frozen). The rendered "YYYY-MM-DD HH:mm:ss.SSS" placeholder is
# emitted verbatim by loguru in test mode when aware_now is patched; pid/tid are the
# fixed integers. The thread name "Dummy-1" is loguru's _DummyThread name, derived
# from the patched get_ident() returning 1 (a non-main ident).
_FIXED_NOW = datetime(2020, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
_FIXED_PID = 4242
_FIXED_TID = 1

# Auto-width cap and the preset identifier width used for the full-render line. The
# preset is a FLOOR: the observed identifier width can grow it up to the cap. "app-0001"
# is 8 cells, so the preset of 8 keeps the column exactly 8 wide for the full-render
# line. The alignment test presets a width >= every identifier so they all align.
_DEFAULT_WIDTHS = {"identifier": 8}
_DEFAULT_CAP = 20

# Custom theme used by the theme-override tests (recolours timestamp/identifier/sep).
_THEME = Theme(timestamp="red", identifier="blue", separator="white")

# --------------------------------------------------------------------------- #
# Golden data — captured from the current code. Do not edit to make a refactor
# pass; a diff here means the rendered output (and thus downstream logs) changed.
# --------------------------------------------------------------------------- #

# Plain templates, str(cls(colorized=False)), keyed by format name.
_PLAIN_TEMPLATES = {
    "ClassicFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | {name:<auto~middle}:{line:<auto~middle}  | {message}"
    ),
    "DebugFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | "
        "PID:{process.name:<auto~middle}[{process.id:^auto~middle}] "
        "TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}] | "
        "{name:<auto~middle}:{line:<auto~middle}  | {message}"
    ),
    "FileFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | {name:<auto~middle}:{line:<auto~middle}  | {message}"
    ),
    "MinimalFormat": "{identifier:^auto~middle} -> {message}",
    "OpsFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | "
        "PID:{process.name:<auto~middle}[{process.id:^auto~middle}] "
        "TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}] | {message}"
    ),
    "PlainFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | {message}"
    ),
    "ShortFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | {message}"
    ),
}

# Colorized templates, str(cls()) (default theme), keyed by format name.
_COLORIZED_TEMPLATES = {
    "ClassicFormat": (
        "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>"
        "<light-black> | </light-black><level>{level.name:^8}</level>"
        "<light-black> | </light-black><light-black>[</light-black>"
        "<light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black>"
        "<magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta> "
        "<light-black> | </light-black><level>{message}</level>"
    ),
    "DebugFormat": (
        "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>"
        "<light-black> | </light-black><level>{level.name:^8}</level>"
        "<light-black> | </light-black><light-black>[</light-black>"
        "<light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black>"
        "<cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> "
        "<light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan>"
        "<light-black> | </light-black>"
        "<magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta> "
        "<light-black> | </light-black><level>{message}</level>"
    ),
    "FileFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | {name:<auto~middle}:{line:<auto~middle}  | {message}"
    ),
    "MinimalFormat": (
        "<light-green>{identifier:^auto~middle}</light-green>"
        "<light-black> -> </light-black><level>{message}</level>"
    ),
    "OpsFormat": (
        "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>"
        "<light-black> | </light-black><level>{level.name:^8}</level>"
        "<light-black> | </light-black><light-black>[</light-black>"
        "<light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black>"
        "<cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> "
        "<light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan>"
        "<light-black> | </light-black><level>{message}</level>"
    ),
    "PlainFormat": (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | "
        "[{identifier:^auto~middle}] | {message}"
    ),
    "ShortFormat": (
        "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>"
        "<light-black> | </light-black><level>{level.name:^8}</level>"
        "<light-black> | </light-black><light-black>[</light-black>"
        "<light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black>"
        "<level>{message}</level>"
    ),
}

# Full rendered line, one record through the public add() path, plain (colorize=False),
# frozen time/pid/tid, identifier "app-0001", message "hello world". The "<MOD>:<LINE>"
# in Classic/Debug/File is the module name + the .info() call's line number in THIS file
# (see _emit below). The line number is pinned to the actual emit line; if this file is
# edited so _emit moves, the golden must be re-captured (the test fails loudly, not
# silently). The thread name "Dummy-1" is derived from _FIXED_TID (see module note).
_FULL_RENDER = {
    "ClassicFormat": (
        "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [app-0001] | test_char_formats:239  | hello world\n"
    ),
    "DebugFormat": (
        "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [app-0001] | "
        "PID:MainProcess[4242] TID:Dummy-1[1] | test_char_formats:239  | hello world\n"
    ),
    "FileFormat": (
        "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [app-0001] | test_char_formats:239  | hello world\n"
    ),
    "MinimalFormat": "app-0001 -> hello world\n",
    "OpsFormat": (
        "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [app-0001] | "
        "PID:MainProcess[4242] TID:Dummy-1[1] | hello world\n"
    ),
    "PlainFormat": ("YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [app-0001] | hello world\n"),
    "ShortFormat": ("YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [app-0001] | hello world\n"),
}

# Alignment: ShortFormat, preset identifier width 9 (>= the widest identifier below),
# so every identifier renders to the SAME 9-cell column. The identifier field is the
# text between the brackets in each line.
_ALIGN_IDENTS = ("ab", "abcdef", "abcdefghi")
_ALIGN_GOLDEN = {
    "ab": "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [   ab    ] | hello world\n",
    "abcdef": "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [ abcdef  ] | hello world\n",
    "abcdefghi": "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [abcdefghi] | hello world\n",
}
_ALIGN_WIDTH = 9

# An identifier wider than the cap (22 cells > cap 20) is middle-truncated with the
# ellipsis U+2026; the rendered column is exactly the cap wide.
_WIDE_IDENT = "a-very-long-identifier-1"
_WIDE_GOLDEN = (
    "YYYY-MM-DD HH:mm:ss.SSS |   INFO   | [a-very-lo…entifier-1] | hello world\n"
)

# Theme override: a custom Theme recolours the themeable segments in the colorized
# template. Plain (colorized=False) output is unaffected by the theme (no color tags).
_THEME_COLORIZED = (
    "<italic><red>{time:YYYY-MM-DD HH:mm:ss.SSS}</red></italic>"
    "<white> | </white><level>{level.name:^8}</level>"
    "<white> | </white><white>[</white>"
    "<blue>{identifier:^auto~middle}</blue><white>] | </white>"
    "<level>{message}</level>"
)

# --------------------------------------------------------------------------- #
# Determinism harness
# --------------------------------------------------------------------------- #


@contextmanager
def _frozen(widths: Optional[Mapping[str, int]] = None) -> Iterator[None]:
    """Freeze time/pid/tid and seed the auto-width registry for one render.

    Patches loguru's aware_now, os.getpid and threading.get_ident to fixed values
    and seeds the global auto-width registry (reset + import_widths + cap) so a
    render is byte-stable across runs, machines and test order. The global
    registry is reset on entry; widths set here do not leak to other tests because
    each call re-seeds from scratch.
    """
    with (
        mock.patch("loguru._logger.aware_now", return_value=_FIXED_NOW),
        mock.patch("os.getpid", return_value=_FIXED_PID),
        mock.patch("threading.get_ident", return_value=_FIXED_TID),
    ):
        lpp.reset_widths()
        lpp.import_widths(dict(widths) if widths else dict(_DEFAULT_WIDTHS))
        lpp.set_max_auto_width(_DEFAULT_CAP)
        try:
            yield
        finally:
            # Leave the global registry as we found it: no leftover cap or widths,
            # so neither these tests read nor leave cross-test auto-width state.
            lpp.reset_widths()
            lpp.set_max_auto_width(None)


def _emit(out: List[str], identifier: str, message: str) -> None:
    """Emit one line through the enhanced singleton.

    This is the ONLY line whose location matters for the Classic/Debug/File
    name:line field: the module name is this test module and the line number is
    the .info() call below. Keep the call on a single, stable line.
    """
    lpp.logger.bind(identifier=identifier).info(message)


def render(
    fmt: str,
    identifier: str,
    message: str = "hello world",
    widths: Optional[Mapping[str, int]] = None,
) -> str:
    """Render one record through the public add() path and return the captured text.

    The public add() is the only path that rewrites the auto-width tokens into
    per-record filters, so this exercises the real auto-width pipeline. colorize
    is forced False so the captured line is plain and byte-stable.
    """
    out: List[str] = []
    with _frozen(widths):
        sid = lpp.add(out.append, format=fmt, colorize=False, level="DEBUG")
        try:
            _emit(out, identifier, message)
        finally:
            lpp.logger.remove(sid)
    return "".join(out)


def _identifier_column(line: str) -> str:
    """Return the identifier field (text between the first bracket pair) of a line."""
    return line.split("[", 1)[1].split("]", 1)[0]


# --------------------------------------------------------------------------- #
# 1. TEMPLATE goldens — the rendered format skeleton, byte-for-byte.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", sorted(F.__all__))
def test_colorized_template_golden(name: str) -> None:
    """str(cls()) matches the locked colorized template (default theme)."""
    cls = getattr(F, name)
    assert str(cls()) == _COLORIZED_TEMPLATES[name]


@pytest.mark.parametrize("name", sorted(F.__all__))
def test_plain_template_golden(name: str) -> None:
    """str(cls(colorized=False)) matches the locked plain template."""
    cls = getattr(F, name)
    assert str(cls(colorized=False)) == _PLAIN_TEMPLATES[name]


def test_template_covers_every_shipped_format() -> None:
    """Both golden tables cover every name in formats.__all__ (guards a new format)."""
    assert set(F.__all__) == set(_COLORIZED_TEMPLATES) == set(_PLAIN_TEMPLATES)


# --------------------------------------------------------------------------- #
# 2. FULL rendered line — one record through the public add() path.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", sorted(F.__all__))
def test_full_rendered_line_default_theme(name: str) -> None:
    """A fully rendered line (default theme, plain) matches the locked golden."""
    cls = getattr(F, name)
    assert render(str(cls(colorized=False)), "app-0001") == _FULL_RENDER[name]


@pytest.mark.parametrize("name", sorted(F.__all__))
def test_full_rendered_line_custom_theme(name: str) -> None:
    """A fully rendered line with a custom theme (plain) matches the locked golden.

    Plain output carries no color tags, so the theme does not change the bytes;
    the golden therefore equals the default-theme golden, which also confirms the
    theme does not leak into plain (file-sink) output.
    """
    cls = getattr(F, name)
    fmt = str(cls(colorized=False, theme=_THEME))
    assert render(fmt, "app-0001") == _FULL_RENDER[name]


# --------------------------------------------------------------------------- #
# 3. Alignment — identifiers of different visual widths share one column width.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("ident", _ALIGN_IDENTS)
def test_alignment_identifier_column_fixed_width(ident: str) -> None:
    """Identifiers of different widths render to the SAME identifier-column width."""
    fmt = str(F.ShortFormat(colorized=False))
    line = render(fmt, ident, widths={"identifier": _ALIGN_WIDTH})
    assert line == _ALIGN_GOLDEN[ident]
    assert len(_identifier_column(line)) == _ALIGN_WIDTH


def test_alignment_wider_identifier_is_middle_truncated_to_cap() -> None:
    """An identifier wider than the cap is middle-truncated; the column stays at the cap."""
    fmt = str(F.ShortFormat(colorized=False))
    line = render(fmt, _WIDE_IDENT)
    assert line == _WIDE_GOLDEN
    assert len(_identifier_column(line)) == _DEFAULT_CAP


# --------------------------------------------------------------------------- #
# 4. Theme overrides — a custom Theme changes the rendered template.
# --------------------------------------------------------------------------- #


def test_custom_theme_changes_colorized_template() -> None:
    """A custom Theme recolours the themeable segments in the colorized template."""
    assert str(F.ShortFormat(theme=_THEME)) == _THEME_COLORIZED
    # The recolored template differs from the default-theme template.
    assert str(F.ShortFormat(theme=_THEME)) != str(F.ShortFormat())


def test_colorized_false_drops_theme_colors() -> None:
    """colorized=False drops every color tag, including the theme's, for any theme."""
    themed_plain = str(F.ShortFormat(theme=_THEME, colorized=False))
    assert themed_plain == _PLAIN_TEMPLATES["ShortFormat"]
    # No closing color tag (a bare "<" is only the align glyph, never a tag).
    assert "</" not in themed_plain


def test_default_theme_renders_documented_default() -> None:
    """The default theme renders the documented historical colors in the template."""
    out = str(F.ClassicFormat())
    for tag in (
        "<yellow>",
        "<light-black>",
        "<light-green>",
        "<magenta>",
        "<light-magenta>",
    ):
        assert tag in out
    # Passing DEFAULT_THEME explicitly is identical to passing nothing.
    assert str(F.ClassicFormat(theme=DEFAULT_THEME)) == str(F.ClassicFormat())
