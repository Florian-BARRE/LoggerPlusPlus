# ====== Code Summary ======
# This module defines a classic ANSI color scheme for log formatting.
# It provides per-level and per-token coloring rules, with emphasis on readability
# and severity highlighting (e.g., WARNING with yellow background, FATAL with red background).

from __future__ import annotations

# ====== Internal Project Imports ======
from ....loglevel.log_level import LogLevels
from ....formatter.layout.log_token import LogToken

# ====== Local Project Imports ======
from ..base import BaseColorScheme
from ..utils.ansi import ANSI as A


class ClassicColorScheme(BaseColorScheme):
    """
    Classic ANSI color scheme for log formatting.

    Features:
        - Per-level mappings (DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL).
        - Per-token mappings for date, level, identifier, file info, etc.
        - Special treatment of LEVEL and MSG tokens depending on log severity.
    """

    # Mapping from log levels to ANSI sequences
    _by_level: dict[int, str] = {
        LogLevels.DEBUG: A.FG.BRIGHT_BLACK,
        LogLevels.INFO: A.FG.BRIGHT_BLUE + A.STYLE.DIM,
        LogLevels.WARNING: A.BG.YELLOW + A.STYLE.BOLD + A.rgb(30, 30, 30),
        LogLevels.ERROR: A.FG.RED + A.STYLE.BOLD,
        LogLevels.CRITICAL: A.BG.RED + A.FG.WHITE,
        LogLevels.FATAL: A.compose(A.FG.BRIGHT_WHITE, A.BG.RED),
    }

    # Mapping from log tokens to ANSI sequences
    _by_token: dict[LogToken, str] = {
        LogToken.DATE: A.FG.YELLOW,
        LogToken.LEVEL: A.STYLE.BOLD,
        LogToken.IDENT: A.FG.BRIGHT_GREEN + A.STYLE.DIM,
        LogToken.FILENAME: A.FG.BLUE,
        LogToken.LINENO: A.FG.MAGENTA + A.STYLE.DIM,
        LogToken.FUNCNAME: A.FG.BRIGHT_BLACK,
        LogToken.MODULE: A.FG.BRIGHT_BLACK,
        LogToken.THREAD: A.FG.MAGENTA,
        LogToken.PROCESS: A.FG.MAGENTA,
        LogToken.MSG: "",
    }

    def level_color(self, level: int) -> str:
        """
        Return the ANSI color for a given log level.

        Args:
            level (int): Numeric log level.

        Returns:
            str: ANSI color sequence (empty string if unknown).
        """
        return (
            self._by_level.get(LogLevels(level), "")
            if level in LogLevels._value2member_map_
            else ""
        )

    def token_color(self, token: LogToken) -> str:
        """
        Return the ANSI color for a specific log token.

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
            return self.level_color(level)
        if token == LogToken.MSG:
            if level >= LogLevels.ERROR:
                return A.FG.RED
            if level == LogLevels.WARNING:
                return A.FG.YELLOW
            if level == LogLevels.DEBUG:
                return A.FG.CYAN
            return ""
        return ""

    def separator_default(self) -> str:
        """
        Return the default ANSI separator color.

        Returns:
            str: Bright black ANSI sequence.
        """
        return A.FG.BRIGHT_BLACK
