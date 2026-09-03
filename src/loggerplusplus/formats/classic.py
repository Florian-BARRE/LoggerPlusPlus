# ====== Code Summary ======
# Concrete implementation of `BaseFormat` that defines a console-friendly
# logging string format. Includes timestamp, log level, identifier, source location,
# and message, all with colorized and aligned styling for readability.

from __future__ import annotations

# ====== Standard Library Imports ======
from typing import Union

# ====== Local Project Imports ======
from .base import BaseFormat

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

        Returns:
            str: A fully constructed log format string compatible with the logging renderer.
        """

        # Segments: timestamp | level | [identifier] | name:line | message
        return cls.build(
            cls._timestamp(),
            cls._sep(sep, True, colorized),
            cls._level(level_width),
            cls._sep(sep, True, colorized),
            cls._sep("[", True, colorized),
            cls._identifier(identifier_width),
            cls._sep("]" + sep, True, colorized),
            cls._location(name_width, line_width),
            cls._sep(sep, True, colorized),
            cls._message(),
        )
