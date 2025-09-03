# ====== Code Summary ======
# This module defines the base color scheme for the formatter.
# It provides default no-op implementations and a default separator style.
# Subclasses are expected to override these methods with actual color behavior.

from __future__ import annotations

# ====== Local Project Imports ======
from .utils.ansi import ANSI as A
from ..layout.log_token import LogToken


class BaseColorScheme:
    """
    Base color scheme defining hooks for level and token colorization.

    Notes:
        - All methods are defined as instance methods (not static) on purpose.
        - Subclasses are expected to override them with self-dependent behavior.
        - IDE static analysis warnings about "method could be static"
          are intentionally suppressed.
    """

    def level_color(self, level: int) -> str:  # noqa: PLR6301
        """
        Return an ANSI sequence representing the color for a given log level.

        Args:
            level (int): The numeric log level.

        Returns:
            str: ANSI color sequence (empty string by default).
        """
        return ""

    def token_color(self, token: LogToken) -> str:  # noqa: PLR6301
        """
        Return an ANSI sequence representing the color for a given token.

        Args:
            token (LogToken): The log token.

        Returns:
            str: ANSI color sequence (empty string by default).
        """
        return ""

    def token_color_for_level(self, token: LogToken, level: int) -> str:  # noqa: PLR6301
        """
        Return an ANSI sequence for a token, potentially varying by log level.

        Args:
            token (LogToken): The log token.
            level (int): The numeric log level.

        Returns:
            str: ANSI color sequence (empty string by default).
        """
        return ""

    def separator_default(self) -> str:  # noqa: PLR6301
        """
        Return the ANSI sequence for the default separator style.

        Returns:
            str: ANSI color sequence (bright black by default).
        """
        return A.FG.BRIGHT_BLACK

    def reset(self) -> str:  # noqa: PLR6301
        """
        Return the ANSI reset sequence.

        Returns:
            str: ANSI reset sequence.
        """
        return A.RESET
