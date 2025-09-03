# ====== Code Summary ======
# Factory function for constructing a LoggerPlusPlusFormatter using a FormatConfig.
# It initializes the layout, optional color scheme, and passes configuration flags
# to the formatter.

from __future__ import annotations

# ====== Local Project Imports ======
from .core import LoggerPlusPlusFormatter
from .layout.base import BaseLayout
from .color.base import BaseColorScheme
from ..config.format import FormatConfig


def build_formatter(cfg: FormatConfig) -> LoggerPlusPlusFormatter:
    """
    Build a `LoggerPlusPlusFormatter` instance based on the provided FormatConfig.

    Args:
        cfg (FormatConfig): The configuration specifying layout, color scheme,
            token/color options, and other formatting behavior.

    Returns:
        LoggerPlusPlusFormatter: Fully initialized formatter ready for use.
    """
    # 1. Instantiate the layout using the configured template, rules, and time format
    layout: BaseLayout = cfg.layout_model(
        template=cfg.template,
        rules=cfg.rules,
        time_fmt=cfg.time_format,
    )

    # 2. Conditionally create a color scheme if colorization is enabled
    scheme: BaseColorScheme | None = (
        cfg.color_scheme() if (cfg.enable_level_color or cfg.enable_token_color) else None
    )

    # 3. Build and return the formatter
    return LoggerPlusPlusFormatter(
        layout=layout,
        scheme=scheme,
        enable_level_color=cfg.enable_level_color,
        enable_token_color=cfg.enable_token_color,
        cfg=cfg,
    )
