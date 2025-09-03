# ====== Code Summary ======
# This module defines a neon-inspired ANSI color scheme for log formatting.
# It uses bright, high-contrast RGB colors to emphasize log levels and tokens.

from __future__ import annotations

# ====== Internal Project Imports ======
from ....loglevel.log_level import LogLevels
from ....formatter.layout.log_token import LogToken

# ====== Local Project Imports ======
from ..base import BaseColorScheme
from ..utils.ansi import ANSI as A


class NeonColorScheme(BaseColorScheme):
    """
    Neon-inspired ANSI color scheme for log formatting.

    Features:
        - Vibrant RGB-based colors for different log levels.
        - Distinct per-token mappings for identifiers, files, and threads.
        - Special coloring for MSG token depending on severity.
    """

    # Mapping from log levels to ANSI sequences
    _by_level: dict[int, str] = {
        LogLevels.DEBUG: A.rgb(0, 190, 255),
        LogLevels.INFO: A.rgb(0, 230, 90),
        LogLevels.WARNING: A.rgb(250, 220, 0),
        LogLevels.ERROR: A.rgb(255, 0, 70),
        LogLevels.CRITICAL: A.rgb(255, 0, 200),
        LogLevels.FATAL: A.compose(A.FG.BRIGHT_WHITE, A.BG.RED),
    }

    # Mapping from log tokens to ANSI sequences
    _by_token: dict[LogToken, str] = {
        LogToken.DATE: A.FG.BRIGHT_BLACK,
        LogToken.LEVEL: A.compose(A.STYLE.BOLD, A.rgb(0, 190, 255)),
        LogToken.IDENT: A.rgb(0, 200, 255),
        LogToken.FILENAME: A.rgb(255, 120, 255),
        LogToken.LINENO: A.rgb(0, 190, 255),
        LogToken.FUNCNAME: A.rgb(180, 130, 255),
        LogToken.MODULE: A.rgb(180, 130, 255),
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
                return A.rgb(255, 0, 70)
            if level == LogLevels.WARNING:
                return A.rgb(250, 220, 0)
            if level == LogLevels.DEBUG:
                return A.rgb(0, 190, 255)
            return ""
        return ""
