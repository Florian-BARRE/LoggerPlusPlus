# ====== Code Summary ======
# Short-format log class extending `BaseFormat`.
# Provides a compact layout with timestamp, level, identifier, and message.
# Ideal for quick inspection of logs where source location and thread/process
# metadata are not required.

from __future__ import annotations

from typing import Union

from .base import BaseFormat
from .theme import DEFAULT_THEME, Theme, resolve_theme

__all__: list[str] = ["ShortFormat"]


class ShortFormat(BaseFormat):
    """
    Short-format log with timestamp, log level, identifier, and message.
    This layout reduces noise by excluding source, process, and thread metadata.

    Format includes:
        - Timestamp (italic and yellow)
        - Log level (center-aligned and colorized)
        - Identifier (in brackets, light green)
        - Message (colorized by level)

    Useful for streamlined log output in lightweight console contexts.
    """

    @classmethod
    def format(
        cls,
        *,
        colorized: bool = True,
        level_width: Union[int, str] = 8,
        identifier_width: Union[int, str] = "auto",
        name_width: Union[
            int, str
        ] = "auto",  # Placeholder argument for API compatibility
        line_width: Union[
            int, str
        ] = "auto",  # Placeholder argument for API compatibility
        sep: str = " | ",
        theme: Theme = DEFAULT_THEME,
    ) -> str:
        """
        Constructs the short log format string with timestamp, log level,
        identifier, and message.

        Args:
            colorized (bool): Whether to apply color/styling tags to the output (default: True).
            level_width (int | str): Width for the log level field (default: 8).
            identifier_width (int | str): Width for the identifier field (default: "auto").
            name_width (int | str): Width for the module name field (not used here, default: "auto").
            line_width (int | str): Width for the line number field (not used here, default: "auto").
            sep (str): Separator string between format components (default: " | ").

        Returns:
            str: A fully constructed short-format log string.
        """

        theme = resolve_theme(theme)
        # Segments: timestamp | level | [identifier] | message
        return cls.build(
            cls._timestamp(colorized, theme),
            cls._sep(sep, True, colorized, theme),
            cls._level(level_width, colorized),
            cls._sep(sep, True, colorized, theme),
            cls._sep("[", True, colorized, theme),
            cls._identifier(identifier_width, colorized, theme),
            cls._sep("]" + sep, True, colorized, theme),
            cls._message(colorized),
        )
