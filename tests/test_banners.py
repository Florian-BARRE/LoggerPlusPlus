# ====== Code Summary ======
# Tests for the `Banner` toolkit: the zero-dependency box/rule renderers, the `preset`
# registry, and the figlet ImportError path (pyfiglet is an OPTIONAL extra, absent in CI).
# A real figlet render only runs when pyfiglet happens to be installed (importorskip).

from __future__ import annotations

import sys

import pytest

from loggerplusplus import Banner

# --------------------------------------------------------------------------- box


def test_box_single_frame_glyphs() -> None:
    """A single-line box uses the light frame glyphs and pads content by one space."""
    out = Banner.box()("hi")
    assert out == "┌────┐\n│ hi │\n└────┘"


def test_box_double_frame_glyphs() -> None:
    """`double=True` switches to the heavy double-line frame."""
    out = Banner.box(double=True)("hi")
    assert out == "╔════╗\n║ hi ║\n╚════╝"


def test_box_align_left_center_right() -> None:
    """Explicit width plus alignment position the content deterministically."""
    left = Banner.box(align="left", width=5)("x")
    center = Banner.box(align="center", width=5)("x")
    right = Banner.box(align="right", width=5)("x")
    assert left.splitlines()[1] == "│ x     │"
    assert center.splitlines()[1] == "│   x   │"
    assert right.splitlines()[1] == "│     x │"


def test_box_explicit_width_widens_frame() -> None:
    """A fixed inner width drives the frame length regardless of content length."""
    out = Banner.box(width=10)("hi")
    top = out.splitlines()[0]
    # inner (10) + 2 padding spaces + 2 corners = 14 chars.
    assert len(top) == 14
    assert top == "┌" + "─" * 12 + "┐"


def test_box_multiline_input() -> None:
    """Every input line gets its own framed body row, sized to the widest line."""
    out = Banner.box(align="left")("a\nbbb")
    lines = out.splitlines()
    assert len(lines) == 4  # top + 2 body + bottom
    assert lines[1] == "│ a   │"
    assert lines[2] == "│ bbb │"


# --------------------------------------------------------------------------- rule


def test_rule_uses_message_as_label() -> None:
    """With label=None the message centers as the rule's label."""
    out = Banner.rule(char="-", width=20)("hi")
    assert out == "-------- hi --------"
    assert len(out) == 20


def test_rule_explicit_label_overrides_message() -> None:
    """An explicit label wins; the message is ignored."""
    out = Banner.rule(char="-", width=20, label="LBL")("ignored")
    assert " LBL " in out
    assert "ignored" not in out


def test_rule_blank_message_is_full_rule() -> None:
    """An empty label degrades to a solid rule of the requested width."""
    out = Banner.rule(char="=", width=12)("")
    assert out == "=" * 12


def test_rule_overwide_label_degrades_to_stripped_label() -> None:
    """A label wider than the rule degrades to the bare, stripped label."""
    out = Banner.rule(char="-", width=8)("a very long label")
    assert out == "a very long label"


# --------------------------------------------------------------------------- figlet


def test_figlet_without_pyfiglet_raises_with_install_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling a figlet transform without the extra raises ImportError with the hint."""
    # Force the absent-extra path deterministically: a None entry in sys.modules makes
    # `from pyfiglet import ...` raise ImportError even when the extra IS installed.
    monkeypatch.setitem(sys.modules, "pyfiglet", None)
    render = Banner.figlet()
    with pytest.raises(ImportError) as excinfo:
        render("BOOM")
    assert "loggerplusplus[banners]" in str(excinfo.value)


def test_figlet_renders_when_pyfiglet_present() -> None:
    """When pyfiglet IS installed, a figlet transform produces multi-line ASCII art."""
    pytest.importorskip("pyfiglet")
    out = Banner.figlet(font="standard")("Hi")
    # Big ASCII art spans multiple lines and never keeps the raw text verbatim.
    assert "\n" in out
    assert out == out.rstrip("\n")  # trailing newlines stripped for raw-mode re-add


# --------------------------------------------------------------------------- preset


@pytest.mark.parametrize("name", ["title", "big", "small", "box", "double", "line"])
def test_preset_known_names_return_callables(name: str) -> None:
    """Every known preset resolves to a transform callable."""
    transform = Banner.preset(name)
    assert callable(transform)


def test_preset_zero_dep_names_render_without_pyfiglet() -> None:
    """The box/double/line presets render immediately (no optional extra needed)."""
    assert Banner.preset("box")("k").splitlines()[0].startswith("┌")
    assert Banner.preset("double")("k").splitlines()[0].startswith("╔")
    assert Banner.preset("line")("k").count(" k ") == 1


def test_preset_unknown_name_raises_value_error() -> None:
    """An unknown preset name raises ValueError listing the available names."""
    with pytest.raises(ValueError) as excinfo:
        Banner.preset("nope")
    msg = str(excinfo.value)
    assert "nope" in msg
    assert "box" in msg  # the available-names list is surfaced
