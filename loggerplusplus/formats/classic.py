# ====== Code Summary ======
# Concrete implementation of `BaseFormat` that defines a console-friendly
# logging string format. Includes timestamp, log level, identifier, source location,
# and message, all with colorized and aligned styling for readability.

from __future__ import annotations

# ====== Local Project Imports ======
from .base import BaseFormat


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
            level_width: int | str = 8,
            identifier_width: int | str = "auto",
            name_width: int | str = "auto",
            line_width: int | str = "auto",
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

        # 1. Format timestamp (italic + yellow)
        # 2. Add separator
        # 3. Format log level (center-aligned + colorized)
        # 4. Add separator
        # 5. Format identifier (in brackets + light green)
        # 6. Add separator
        # 7. Format name and line (magenta and light-magenta)
        # 8. Add separator
        # 9. Format log message (colored by level)

        return cls.build(
            "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>",
            cls._sep(sep, True, colorized),
            f"<level>{{level.name:^{level_width}}}</level>",
            cls._sep(sep, True, colorized),
            cls._sep("[", True, colorized),
            f"<light-green>{{identifier:^{identifier_width}~middle}}</light-green>",
            cls._sep("]" + sep, True, colorized),
            f"<magenta>{{name:<{name_width}~middle}}:</magenta>",
            f"<light-magenta>{{line:<{line_width}~middle}}</light-magenta> ",
            cls._sep(sep, True, colorized),
            "<level>{message}</level>",
        )
