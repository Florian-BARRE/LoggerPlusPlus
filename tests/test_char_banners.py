# ====== Code Summary ======
# Phase 3 characterization safety net for the `Banner` transform toolkit. Pins the EXACT
# current output of every public factory (box, rule, preset, figlet) at the public boundary,
# so a later refactoring ticket (re-homing Banner into transforms/) can prove it changed
# nothing byte-for-byte. Goldens were captured by running the current code, not invented.
# pyfiglet is an OPTIONAL extra and is ABSENT in the dev/CI env: the figlet ImportError hint
# path is pinned for sure, and the real figlet render stays importorskip-gated (skips in CI).

from __future__ import annotations

import sys

import pytest

from loggerplusplus import Banner, transforms

# --------------------------------------------------------------------------- box


def test_char_box_single_line_frame() -> None:
    """A single-line input is framed by the light box with one-space inner padding."""
    out = Banner.box()("hi")
    assert out == "┌────┐\n│ hi │\n└────┘"


def test_char_box_double_single_line_frame() -> None:
    """`double=True` switches the frame to the heavy double-line glyphs."""
    out = Banner.box(double=True)("hi")
    assert out == "╔════╗\n║ hi ║\n╚════╝"


def test_char_box_multiline_center() -> None:
    """Each input line becomes its own body row, centered in the widest line's width."""
    out = Banner.box()("one\ntwo")
    assert out == "┌─────┐\n│ one │\n│ two │\n└─────┘"


def test_char_box_multiline_left() -> None:
    """Left alignment pushes every line to the left edge of the inner width."""
    out = Banner.box(align="left")("one\ntwo")
    assert out == "┌─────┐\n│ one │\n│ two │\n└─────┘"


def test_char_box_align_left_center_right_explicit_width() -> None:
    """With a fixed inner width, the three alignments place the content deterministically."""
    assert Banner.box(align="left", width=5)("x") == "┌───────┐\n│ x     │\n└───────┘"
    assert Banner.box(align="center", width=5)("x") == "┌───────┐\n│   x   │\n└───────┘"
    assert Banner.box(align="right", width=5)("x") == "┌───────┐\n│     x │\n└───────┘"


def test_char_box_explicit_width_widens_frame() -> None:
    """A fixed inner width drives the frame length regardless of the content length."""
    out = Banner.box(width=10)("hi")
    assert out == "┌────────────┐\n│     hi     │\n└────────────┘"


# --------------------------------------------------------------------------- rule


def test_char_rule_message_as_label() -> None:
    """With label=None the message is centered as the rule's label, total width kept."""
    out = Banner.rule(char="-", width=30)("SECTION")
    assert out == "---------- SECTION -----------"
    assert len(out) == 30


def test_char_rule_explicit_label_overrides_message() -> None:
    """An explicit label wins; the message text is dropped entirely."""
    out = Banner.rule(char="-", width=24, label="LBL")("ignored")
    assert out == "--------- LBL ----------"
    assert "ignored" not in out


def test_char_rule_blank_message_is_full_rule() -> None:
    """A blank label degrades to a solid rule of exactly the requested width."""
    out = Banner.rule(char="=", width=12)("")
    assert out == "============"


def test_char_rule_overwide_label_degrades_to_stripped_label() -> None:
    """A label too wide for the rule degrades to the bare, stripped label."""
    out = Banner.rule(char="-", width=8)("a very long label")
    assert out == "a very long label"


# --------------------------------------------------------------------------- preset


def test_char_preset_known_zero_dep_names_are_working_transforms() -> None:
    """The zero-dependency presets each resolve to a working transform callable."""
    for name in ("box", "double", "line"):
        assert callable(Banner.preset(name))


def test_char_preset_box_renders_without_pyfiglet() -> None:
    """The `box` preset renders a framed line with no optional extra installed."""
    out = Banner.preset("box")("ok")
    assert out == "┌────┐\n│ ok │\n└────┘"


def test_char_preset_double_renders_without_pyfiglet() -> None:
    """The `double` preset renders a double-framed line with no optional extra installed."""
    out = Banner.preset("double")("ok")
    assert out == "╔════╗\n║ ok ║\n╚════╝"


def test_char_preset_line_renders_without_pyfiglet() -> None:
    """The `line` preset renders the default-width rule (60) around the message."""
    out = Banner.preset("line")("hi")
    assert out == "──────────────────────────── hi ────────────────────────────"


def test_char_preset_unknown_name_raises_value_error() -> None:
    """An unknown preset name raises ValueError carrying the available-names list."""
    with pytest.raises(ValueError) as excinfo:
        Banner.preset("nope")
    assert (
        str(excinfo.value)
        == "unknown banner preset 'nope'; available: ['big', 'box', 'double', 'line', 'small', 'title']"
    )


def test_char_preset_banner_reexport_identity() -> None:
    """`loggerplusplus.Banner` and `loggerplusplus.transforms.Banner` are the same object."""
    assert transforms.Banner is Banner


# --------------------------------------------------------------------------- figlet


def test_char_figlet_without_pyfiglet_raises_install_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling a figlet transform with pyfiglet forced absent raises the exact ImportError."""
    # A None entry in sys.modules makes `from pyfiglet import ...` raise ImportError even
    # if the extra happened to be installed, pinning the hint text deterministically.
    monkeypatch.setitem(sys.modules, "pyfiglet", None)
    render = Banner.figlet()
    with pytest.raises(ImportError) as excinfo:
        render("BOOM")
    assert (
        str(excinfo.value)
        == "Banner.figlet requires pyfiglet. Install it with: pip install 'loggerplusplus[banners]'"
    )


def test_char_figlet_renders_when_pyfiglet_present() -> None:
    """When pyfiglet IS installed, a figlet transform yields multi-line ASCII art."""
    pytest.importorskip("pyfiglet")
    out = Banner.figlet(font="standard")("Hi")
    assert "\n" in out
    assert out == out.rstrip("\n")  # trailing newlines are stripped by the transform
