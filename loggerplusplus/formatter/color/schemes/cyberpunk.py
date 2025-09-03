# ====== Code Summary ======
# This module defines a "cyberpunk" ANSI color scheme for log formatting.
# It uses vibrant neon-inspired colors for log levels and tokens.

from __future__ import annotations

# ====== Internal Project Imports ======
from ....loglevel.log_level import LogLevels
from ....formatter.layout.log_token import LogToken

# ====== Local Project Imports ======
from ..base import BaseColorScheme
from ..utils.ansi import ANSI as A


class CyberpunkColorScheme(BaseColorScheme):
    """
    Cyberpunk-inspired ANSI color scheme for log formatting.

    Features:
        - Neon-style colors per log level (DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL).
        - Distinct per-token colors for identifiers, file info, threads, etc.
        - Special handling for MSG token depending on severity.
    """

    # Mapping from log levels to ANSI sequences
    _by_level: dict[int, str] = {
        LogLevels.DEBUG: A.FG.BRIGHT_MAGENTA,
        LogLevels.INFO: A.FG.BRIGHT_CYAN,
        LogLevels.WARNING: A.FG.BRIGHT_YELLOW,
        LogLevels.ERROR: A.FG.BRIGHT_RED,
        LogLevels.CRITICAL: A.compose(A.FG.BRIGHT_MAGENTA, A.BG.RED),
        LogLevels.FATAL: A.compose(A.FG.BRIGHT_WHITE, A.BG.MAGENTA),
    }

    # Mapping from log tokens to ANSI sequences
    _by_token: dict[LogToken, str] = {
        LogToken.DATE: A.rgb(255, 128, 200),
        LogToken.LEVEL: A.compose(A.STYLE.BOLD, A.FG.BRIGHT_CYAN),
        LogToken.IDENT: A.FG.BRIGHT_BLUE,
        LogToken.FILENAME: A.rgb(255, 120, 255),
        LogToken.LINENO: A.FG.BRIGHT_CYAN,
        LogToken.FUNCNAME: A.FG.BRIGHT_MAGENTA,
        LogToken.MODULE: A.FG.BRIGHT_MAGENTA,
        LogToken.THREAD: A.rgb(255, 160, 0),
        LogToken.PROCESS: A.rgb(255, 160, 0),
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
                return A.FG.BRIGHT_RED
            if level == LogLevels.WARNING:
                return A.FG.BRIGHT_YELLOW
            if level == LogLevels.DEBUG:
                return A.FG.BRIGHT_CYAN
            return ""
        return ""
