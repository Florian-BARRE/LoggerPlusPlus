# ====== Code Summary ======
# Tests for the uncolored file formats (audit item A6): PlainFormat / FileFormat render
# without color by default and are resolvable by name; color can be re-enabled.

from __future__ import annotations

from loggerplusplus import formats


def test_plain_and_file_are_uncolored_by_default() -> None:
    """PlainFormat and FileFormat carry no color tags by default."""
    assert "</" not in str(formats.PlainFormat())
    assert "</" not in str(formats.FileFormat())


def test_plain_format_can_be_recolored() -> None:
    """Passing colorized=True re-introduces the color tags."""
    assert "<light-green>" in str(formats.PlainFormat(colorized=True))
    assert "<magenta>" in str(formats.FileFormat(colorized=True))


def test_file_format_includes_source_location() -> None:
    """FileFormat keeps the Classic source name:line segment; Plain omits it."""
    assert "{name:" in str(formats.FileFormat())
    assert "{name:" not in str(formats.PlainFormat())


def test_new_formats_resolvable_by_name() -> None:
    """The new formats are exported and resolvable by name (for config-driven selection)."""
    assert {"PlainFormat", "FileFormat"} <= set(formats.__all__)
    assert issubclass(formats.PlainFormat, formats.BaseFormat)
    assert issubclass(formats.FileFormat, formats.BaseFormat)
