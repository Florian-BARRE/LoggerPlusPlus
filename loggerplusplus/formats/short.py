# ====== Code Summary ======
# Short-format log class extending `BaseFormat`.
# Provides a compact layout with timestamp, level, identifier, and message.
# Ideal for quick inspection of logs where source location and thread/process
# metadata are not required.

from __future__ import annotations

# ====== Local Project Imports ======
from .base import BaseFormat


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
            level_width: int | str = 8,
            identifier_width: int | str = "auto",
            name_width: int | str = "auto",  # Placeholder argument for API compatibility
            line_width: int | str = "auto",  # Placeholder argument for API compatibility
            sep: str = " | ",
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

        # 1. Format timestamp (italic + yellow)
        # 2. Add separator
        # 3. Format log level (center-aligned + colorized)
        # 4. Add separator
        # 5. Format identifier (in brackets + light green)
        # 6. Add separator
        # 7. Format log message (colored by level)

        return cls.build(
            "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>",
            cls._sep(sep, True, colorized),

            f"<level>{{level.name:^{level_width}}}</level>",
            cls._sep(sep, True, colorized),

            cls._sep("[", True, colorized),
            f"<light-green>{{identifier:^{identifier_width}~middle}}</light-green>",
            cls._sep("]" + sep, True, colorized),

            "<level>{message}</level>",
        )
