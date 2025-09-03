# ====== Code Summary ======
# This module defines a "dark" ANSI color scheme for log formatting.
# It uses high-contrast colors designed for readability on dark backgrounds.

from __future__ import annotations

# ====== Internal Project Imports ======
from ....loglevel.log_level import LogLevels
from ....formatter.layout.log_token import LogToken

# ====== Local Project Imports ======
from ..base import BaseColorScheme
from ..utils.ansi import ANSI as A


class DarkColorScheme(BaseColorScheme):
    """
    Dark-themed ANSI color scheme for log formatting.

    Features:
        - High-contrast level colors suitable for dark backgrounds.
        - Distinct token mappings for identifiers, filenames, and process info.
        - Special handling for MSG token depending on severity.
    """

    # Mapping from log levels to ANSI sequences
    _by_level: dict[int, str] = {
        LogLevels.DEBUG: A.FG.CYAN,
        LogLevels.INFO: A.FG.BRIGHT_WHITE,
        LogLevels.WARNING: A.FG.YELLOW,
        LogLevels.ERROR: A.FG.RED,
        LogLevels.CRITICAL: A.FG.MAGENTA,
        LogLevels.FATAL: A.compose(A.FG.BRIGHT_WHITE, A.BG.RED),
    }

    # Mapping from log tokens to ANSI sequences
    _by_token: dict[LogToken, str] = {
        LogToken.DATE: A.FG.BRIGHT_BLACK,
        LogToken.LEVEL: A.STYLE.BOLD,
        LogToken.IDENT: A.FG.BRIGHT_BLUE,
        LogToken.FILENAME: A.FG.BRIGHT_CYAN,
        LogToken.LINENO: A.FG.BRIGHT_CYAN,
        LogToken.FUNCNAME: A.FG.BRIGHT_BLACK,
        LogToken.MODULE: A.FG.BRIGHT_BLACK,
        LogToken.THREAD: A.FG.BRIGHT_MAGENTA,
        LogToken.PROCESS: A.FG.BRIGHT_MAGENTA,
        LogToken.MSG: "",
    }

    def level_color(self, level: int) -> str:
        """
        Return the ANSI color for a given log level.

        Args:
            level (int): Numeric log level.

        Returns:
            str: ANSI color sequence (empty string if not mapped).
        """
        return self._by_level.get(LogLevels(level), "")

    def token_color(self, token: LogToken) -> str:
        """
        Return the ANSI color for a given token.

        Args:
            token (LogToken): The token.

        Returns:
            str: ANSI color sequence (empty string if not mapped).
        """
        return self._by_token.get(token, "")

    def token_color_for_level(self, token: LogToken, level: int) -> str:
        """
        Return the ANSI color for a token, possibly varying by log level.

        Args:
            token (LogToken): The token being rendered.
            level (int): The numeric log level.

        Returns:
            str: ANSI color sequence (empty string if not applicable).
        """
        if token == LogToken.LEVEL:
            return self._by_level.get(LogLevels(level), "")
        if token == LogToken.MSG:
            if level >= LogLevels.ERROR:
                return A.FG.RED
            if level == LogLevels.WARNING:
                return A.FG.YELLOW
            if level == LogLevels.DEBUG:
                return A.FG.CYAN
            return ""
        return ""
