# ====== Code Summary ======
# This module defines a pastel-themed ANSI color scheme for log formatting.
# It uses soft, muted RGB colors for log levels and tokens to achieve a gentle aesthetic.

from __future__ import annotations

# ====== Internal Project Imports ======
from ....loglevel.log_level import LogLevels
from ....formatter.layout.log_token import LogToken

# ====== Local Project Imports ======
from ..base import BaseColorScheme
from ..utils.ansi import ANSI as A


class PastelColorScheme(BaseColorScheme):
    """
    Pastel ANSI color scheme for log formatting.

    Features:
        - Soft, muted RGB-based colors for different log levels.
        - Gentle per-token mappings to maintain readability.
        - Special coloring for MSG token depending on severity.
    """

    # Mapping from log levels to ANSI sequences
    _by_level: dict[int, str] = {
        LogLevels.DEBUG: A.rgb(160, 200, 220),
        LogLevels.INFO: A.rgb(180, 220, 200),
        LogLevels.WARNING: A.rgb(230, 210, 140),
        LogLevels.ERROR: A.rgb(230, 150, 150),
        LogLevels.CRITICAL: A.compose(A.rgb(230, 180, 220), A.BG.RED),
        LogLevels.FATAL: A.compose(A.FG.BRIGHT_WHITE, A.BG.RED),
    }

    # Mapping from log tokens to ANSI sequences
    _by_token: dict[LogToken, str] = {
        LogToken.DATE: A.rgb(160, 160, 180),
        LogToken.LEVEL: A.compose(A.STYLE.BOLD, A.rgb(180, 220, 200)),
        LogToken.IDENT: A.rgb(120, 160, 200),
        LogToken.FILENAME: A.rgb(130, 170, 210),
        LogToken.LINENO: A.rgb(130, 170, 210),
        LogToken.FUNCNAME: A.rgb(160, 160, 190),
        LogToken.MODULE: A.rgb(160, 160, 190),
        LogToken.THREAD: A.rgb(170, 140, 190),
        LogToken.PROCESS: A.rgb(170, 140, 190),
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
                return A.rgb(230, 150, 150)
            if level == LogLevels.WARNING:
                return A.rgb(230, 210, 140)
            if level == LogLevels.DEBUG:
                return A.rgb(160, 200, 220)
            return ""
        return ""
