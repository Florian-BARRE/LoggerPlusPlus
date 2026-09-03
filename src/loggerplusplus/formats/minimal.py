# ====== Code Summary ======
# Minimalistic log format class designed for concise output.
# Focuses on displaying only the identifier and the log message,
# suitable for lightweight logs or simplified console traces.

from __future__ import annotations

from typing import Union

from .base import BaseFormat
from .theme import DEFAULT_THEME, Theme, resolve_theme

__all__: list[str] = ["MinimalFormat"]


class MinimalFormat(BaseFormat):
    """
    Minimalist log format for compact output with only essential context.

    This format includes:
        - Identifier (center-aligned and colorized)
        - Log message (with level-based colorization)

    Best suited for environments where screen space or visual noise must be reduced.
    """

    @classmethod
    def format(
        cls,
        *,
        colorized: bool = True,
        identifier_width: Union[int, str] = "auto",
        sep: str = " | ",
        theme: Theme = DEFAULT_THEME,
    ) -> str:
        """
        Constructs a minimal log format with only identifier and message.

        Args:
            colorized (bool): Whether to apply color/styling tags to the output (default: True).
            identifier_width (int | str): Width for the identifier field (default: "auto").
            sep (str): Separator string (not directly used here but accepted for API compatibility).
            theme (Theme): Color theme for the segments (default: DEFAULT_THEME).

        Returns:
            str: A compact log format string.
        """

        theme = resolve_theme(theme)
        # Segments: identifier -> message
        return cls.build(
            cls._identifier(identifier_width, colorized, theme),
            cls._sep(" -> ", True, colorized, theme),
            cls._message(colorized),
        )
