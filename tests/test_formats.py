# ====== Code Summary ======
# Coverage for the formats package: BaseFormat helpers (_sep / build / __new__),
# every concrete format's `format()` output and override branches, and the
# by-name resolution the downstream projects rely on.

from __future__ import annotations

import pytest

from loggerplusplus import formats as lpp_formats
from loggerplusplus.formats import (
    ClassicFormat,
    DebugFormat,
    MinimalFormat,
    OpsFormat,
    ShortFormat,
)
from loggerplusplus.formats.base import BaseFormat

ALL_FORMATS = [ClassicFormat, DebugFormat, MinimalFormat, OpsFormat, ShortFormat]


@pytest.mark.parametrize("fmt_cls", ALL_FORMATS)
def test_format_instance_is_a_str(fmt_cls: type) -> None:
    """Every format instance is itself a usable format string (BaseFormat inherits str)."""
    instance = fmt_cls()
    assert isinstance(instance, str)
    assert isinstance(instance, BaseFormat)
    assert "{message}" in instance


@pytest.mark.parametrize("fmt_cls", ALL_FORMATS)
def test_format_carries_identifier_and_message(fmt_cls: type) -> None:
    """Each format renders the identifier field and the level-colored message."""
    text = fmt_cls.format()
    assert "identifier" in text
    assert "<level>{message}</level>" in text


@pytest.mark.parametrize("fmt_cls", ALL_FORMATS)
def test_colorized_false_drops_color_markup_on_separators(fmt_cls: type) -> None:
    """With colorized=False the dimmed separator markup is omitted."""
    plain = fmt_cls.format(colorized=False)
    assert "<light-black>" not in plain


def test_public_formats_resolve_by_name() -> None:
    """Downstream selects formats by name via getattr on the formats module."""
    for name in lpp_formats.__all__:
        resolved = getattr(lpp_formats, name)
        assert issubclass(resolved, BaseFormat)


def test_sep_applies_dim_markup_only_when_colorized_and_dim() -> None:
    """_sep wraps the separator only when both colorized and dim are true."""
    assert (
        BaseFormat._sep("|", dim=True, colorized=True) == "<light-black>|</light-black>"
    )
    assert BaseFormat._sep("|", dim=False, colorized=True) == "|"
    assert BaseFormat._sep("|", dim=True, colorized=False) == "|"


def test_build_joins_non_empty_parts_only() -> None:
    """build concatenates truthy parts and skips empty strings."""
    assert BaseFormat.build("a", "", "b", "") == "ab"


def test_custom_separator_is_threaded_into_output() -> None:
    """A custom separator argument appears in the rendered format string."""
    text = ClassicFormat.format(sep=" :: ")
    assert " :: " in text


def test_fixed_identifier_width_is_honored() -> None:
    """Passing a numeric identifier_width bakes that width into the token."""
    text = MinimalFormat.format(identifier_width=12)
    assert "{identifier:^12~middle}" in text


def test_base_format_declares_format_abstract() -> None:
    """BaseFormat marks `format` abstract, forcing subclasses to implement it."""
    assert "format" in BaseFormat.__abstractmethods__
