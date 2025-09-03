# ====== Code Summary ======
# This module defines a configuration dataclass for formatting log output.
# It specifies layout, color scheme, formatting rules, tokens, color overrides,
# auto-sizing behavior, and separators.

from __future__ import annotations

# ====== Standard Library Imports ======
from dataclasses import dataclass, field

# ====== Internal Project Imports ======
from ...formatter.layout.base import BaseLayout
from ...formatter.color.base import BaseColorScheme
from ...formatter.layout.rules import FieldRule
from ...formatter.layout.log_token import LogToken

# ====== Local Project Imports ======
from .format_enums import SeparatorConfig


@dataclass(slots=True)
class FormatConfig:
    """
    Configuration for log formatting, including layout, color scheme, rules,
    token behavior, and separators.

    Attributes:
        layout_model (type[BaseLayout]): The layout class used for formatting.
        color_scheme (type[BaseColorScheme]): The color scheme class applied to tokens and levels.
        time_format (str): `strftime`-compatible string for rendering timestamps.
        template (str | None): Optional format string for log lines.
        extra_placeholders (dict[str, str]): Additional placeholder values for formatting.
        rules (dict[LogToken, FieldRule]): Custom field rules mapped by log tokens.
        enable_level_color (bool): Whether log levels should be colorized.
        enable_token_color (bool): Whether tokens should be colorized.
        token_color_overrides (dict[LogToken, str]): Custom color overrides for tokens.
        token_color_disabled (set[LogToken]): Tokens excluded from colorization.
        autosize_sample_period (int): Sample frequency for autosizing fields.
        enable_fast_assembly (bool): Whether to use optimized assembly for log lines.
        separators (SeparatorConfig): Configuration for separators between log sections.
    """

    layout_model: type[BaseLayout]
    color_scheme: type[BaseColorScheme]
    time_format: str = "%H:%M:%S.%f"
    template: str | None = None
    extra_placeholders: dict[str, str] = field(default_factory=dict)
    rules: dict[LogToken, FieldRule] = field(default_factory=dict)
    enable_level_color: bool = True
    enable_token_color: bool = True
    token_color_overrides: dict[LogToken, str] = field(default_factory=dict)
    token_color_disabled: set[LogToken] = field(default_factory=set)
    autosize_sample_period: int = 1
    enable_fast_assembly: bool = False
    separators: SeparatorConfig = field(default_factory=SeparatorConfig)
