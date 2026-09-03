# ====== Code Summary ======
# Debug-oriented log format class extending `BaseFormat`.
# Adds detailed metadata such as process and thread identifiers, in addition to
# timestamp, level, identifier, and message. Designed for in-depth inspection
# during debugging, with full colorization and structured formatting.

from __future__ import annotations

# ====== Standard Library Imports ======
from typing import Union

# ====== Local Project Imports ======
from .base import BaseFormat

__all__: list[str] = ["DebugFormat"]


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
        level_width: Union[int, str] = 8,
        identifier_width: Union[int, str] = "auto",
        process_name_width: Union[int, str] = "auto",
        process_id_width: Union[int, str] = "auto",
        thread_name_width: Union[int, str] = "auto",
        thread_id_width: Union[int, str] = "auto",
        name_width: Union[int, str] = "auto",
        line_width: Union[int, str] = "auto",
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

        # Segments: timestamp | level | [identifier] | PID/TID | name:line | message
        return cls.build(
            cls._timestamp(),
            cls._sep(sep, True, colorized),
            cls._level(level_width),
            cls._sep(sep, True, colorized),
            cls._sep("[", True, colorized),
            cls._identifier(identifier_width),
            cls._sep("]" + sep, True, colorized),
            cls._process_thread(
                process_name_width,
                process_id_width,
                thread_name_width,
                thread_id_width,
            ),
            cls._sep(sep, True, colorized),
            cls._location(name_width, line_width),
            cls._sep(sep, True, colorized),
            cls._message(),
        )
