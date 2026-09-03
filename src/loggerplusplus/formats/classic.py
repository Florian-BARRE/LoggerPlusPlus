# ====== Code Summary ======
# Concrete implementation of `BaseFormat` that defines a console-friendly
# logging string format. Includes timestamp, log level, identifier, source location,
# and message, all with colorized and aligned styling for readability.

from __future__ import annotations

from typing import Union

from .base import BaseFormat
from .theme import DEFAULT_THEME, Theme, resolve_theme

__all__: list[str] = ["ClassicFormat"]


class ClassicFormat(BaseFormat):
    """
    Console-friendly log format with rich colorization and structural alignment.

    Format includes:
        - Timestamp (in italics and yellow)
        - Log level (center-aligned)
        - Identifier (in green, enclosed in brackets)
        - Source name and line number (in magenta variants)
        - Message (in level's color)

    All components are separated by a customizable, dimmed separator.

    This format is ideal for human-readable console output.
    """

    @classmethod
    def format(
        cls,
        *,
        colorized: bool = True,
        level_width: Union[int, str] = 8,
        identifier_width: Union[int, str] = "auto",
        name_width: Union[int, str] = "auto",
        line_width: Union[int, str] = "auto",
        sep: str = " | ",
        theme: Theme = DEFAULT_THEME,
    ) -> str:
        """
        Constructs the full log format string using stylized and aligned components.

        Args:
            colorized (bool): Whether to apply color/styling tags to the output (default: True).
            level_width (int | str): Width for the log level field (default: 8).
            identifier_width (int | str): Width for the identifier field (default: "auto").
            name_width (int | str): Width for the module name field (default: "auto").
            line_width (int | str): Width for the line number field (default: "auto").
            sep (str): Separator string between format components (default: " | ").
            theme (Theme): Color theme for the segments (default: DEFAULT_THEME).

        Returns:
            str: A fully constructed log format string compatible with the logging renderer.
        """

        theme = resolve_theme(theme)
        # Segments: timestamp | level | [identifier] | name:line | message
        return cls.build(
            cls._timestamp(colorized, theme),
            cls._sep(sep, True, colorized, theme),
            cls._level(level_width, colorized),
            cls._sep(sep, True, colorized, theme),
            cls._sep("[", True, colorized, theme),
            cls._identifier(identifier_width, colorized, theme),
            cls._sep("]" + sep, True, colorized, theme),
            cls._location(name_width, line_width, colorized, theme),
            cls._sep(sep, True, colorized, theme),
            cls._message(colorized),
        )
