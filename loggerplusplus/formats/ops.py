# ====== Code Summary ======
# Operations-oriented log format extending `BaseFormat`.
# Provides timestamp, log level, identifier, process and thread details,
# and the message body. Designed for operational monitoring where
# contextual metadata is required but source location is not critical.

from __future__ import annotations

# ====== Local Project Imports ======
from .base import BaseFormat


class OpsFormat(BaseFormat):
    """
    Operations-focused log format with timestamp, identifier, process/thread metadata,
    and message. Omits source file and line number for more concise output.

    This format includes:
        - Timestamp (italic and yellow)
        - Log level (center-aligned and colorized)
        - Identifier (in brackets, light green)
        - Process name and ID (cyan)
        - Thread name and ID (light cyan)
        - Log message (colorized by level)

    Suitable for production or operations logs where process/thread context is
    more relevant than source code location.
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
            sep: str = " | ",
    ) -> str:
        """
        Constructs the operations log format string including timestamp,
        identifier, process, and thread details.

        Args:
            colorized (bool): Whether to apply color/styling tags to the output (default: True).
            level_width (int | str): Width for the log level field (default: 8).
            identifier_width (int | str): Width for the identifier field (default: "auto").
            process_name_width (int | str): Width for the process name field (default: "auto").
            process_id_width (int | str): Width for the process ID field (default: "auto").
            thread_name_width (int | str): Width for the thread name field (default: "auto").
            thread_id_width (int | str): Width for the thread ID field (default: "auto").
            sep (str): Separator string between format components (default: " | ").

        Returns:
            str: A fully constructed operations log format string.
        """

        # 1. Format timestamp (italic + yellow)
        # 2. Add separator
        # 3. Format log level (center-aligned + colorized)
        # 4. Add separator
        # 5. Format identifier (in brackets + light green)
        # 6. Add separator
        # 7. Format process info (cyan, with name and ID)
        # 8. Format thread info (light cyan, with name and ID)
        # 9. Add separator
        # 10. Format log message (colored by level)

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

            "<level>{message}</level>",
        )
