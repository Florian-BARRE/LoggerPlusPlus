# ====== Code Summary ======
# Debug-oriented log format class extending `BaseFormat`.
# Adds detailed metadata such as process and thread identifiers, in addition to
# timestamp, level, identifier, and message. Designed for in-depth inspection
# during debugging, with full colorization and structured formatting.

from __future__ import annotations

# ====== Local Project Imports ======
from .base import BaseFormat


class DebugFormat(BaseFormat):
    """
    Debug-focused log format with rich metadata and full colorization.

    This format includes:
        - Timestamp
        - Log level
        - Identifier
        - Process name and ID
        - Thread name and ID
        - Source name and line number
        - Log message

    All components are visually distinct and separated by a dimmed separator
    for enhanced readability in console output during debugging.
    """

    @classmethod
    def format(
            cls,
            *,
            colorized: bool = True,
            level_width: int | str = 8,
            identifier_width: int | str = "auto",
            process_name_width: int | str = "auto",
            process_id_width: int | str = "auto",
            thread_name_width: int | str = "auto",
            thread_id_width: int | str = "auto",
            name_width: int | str = "auto",
            line_width: int | str = "auto",
            sep: str = " | ",
    ) -> str:
        """
        Constructs a debug log format string including process/thread details.

        Args:
            colorized (bool): Whether to apply color/styling tags to the output (default: True).
            level_width (int | str): Width for the log level field (default: 8).
            identifier_width (int | str): Width for the identifier field (default: "auto").
            process_name_width (int | str): Width for the process name field (default: "auto").
            process_id_width (int | str): Width for the process ID field (default: "auto").
            thread_name_width (int | str): Width for the thread name field (default: "auto").
            thread_id_width (int | str): Width for the thread ID field (default: "auto").
            name_width (int | str): Width for the module name field (default: "auto").
            line_width (int | str): Width for the line number field (default: "auto").
            sep (str): Separator string between format components (default: " | ").

        Returns:
            str: A fully constructed debug log format string.
        """

        # 1. Format timestamp (italic + yellow)
        # 2. Add separator
        # 3. Format log level (center-aligned + colorized)
        # 4. Add separator
        # 5. Format identifier (in brackets + light green)
        # 6. Add separator
        # 7. Format process and thread info (cyan and light-cyan)
        # 8. Add separator
        # 9. Format source location (magenta and light-magenta)
        # 10. Add separator
        # 11. Format log message (colored by level)

        return cls.build(
            "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic>",
            cls._sep(sep, True, colorized),

            f"<level>{{level.name:^{level_width}}}</level>",
            cls._sep(sep, True, colorized),

            cls._sep("[", True, colorized),
            f"<light-green>{{identifier:^{identifier_width}~middle}}</light-green>",
            cls._sep("]" + sep, True, colorized),

            f"<cyan>PID:{{process.name:<{process_name_width}~middle}}[{{process.id:^{process_id_width}~middle}}]</cyan> ",
            f"<light-cyan>TID:{{thread.name:<{thread_name_width}~middle}}[{{thread.id:^{thread_id_width}~middle}}]</light-cyan>",
            cls._sep(sep, True, colorized),

            f"<magenta>{{name:<{name_width}~middle}}:</magenta>",
            f"<light-magenta>{{line:<{line_width}~middle}}</light-magenta> ",
            cls._sep(sep, True, colorized),

            "<level>{message}</level>",
        )
