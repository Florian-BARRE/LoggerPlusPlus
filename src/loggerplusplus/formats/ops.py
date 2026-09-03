# ====== Code Summary ======
# Operations-oriented log format extending `BaseFormat`.
# Provides timestamp, log level, identifier, process and thread details,
# and the message body. Designed for operational monitoring where
# contextual metadata is required but source location is not critical.

from __future__ import annotations

from typing import Union

from .base import BaseFormat
from .theme import DEFAULT_THEME, Theme, resolve_theme

__all__: list[str] = ["OpsFormat"]


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
        level_width: Union[int, str] = 8,
        identifier_width: Union[int, str] = "auto",
        process_name_width: Union[int, str] = "auto",
        process_id_width: Union[int, str] = "auto",
        thread_name_width: Union[int, str] = "auto",
        thread_id_width: Union[int, str] = "auto",
        sep: str = " | ",
        theme: Theme = DEFAULT_THEME,
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

        theme = resolve_theme(theme)
        # Segments: timestamp | level | [identifier] | PID/TID | message
        return cls.build(
            cls._timestamp(colorized, theme),
            cls._sep(sep, True, colorized, theme),
            cls._level(level_width, colorized),
            cls._sep(sep, True, colorized, theme),
            cls._sep("[", True, colorized, theme),
            cls._identifier(identifier_width, colorized, theme),
            cls._sep("]" + sep, True, colorized, theme),
            cls._process_thread(
                process_name_width,
                process_id_width,
                thread_name_width,
                thread_id_width,
                colorized,
                theme,
            ),
            cls._sep(sep, True, colorized, theme),
            cls._message(colorized),
        )
