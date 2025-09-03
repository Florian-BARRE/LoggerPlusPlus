# ====== Code Summary ======
# This module defines ANSI escape sequences for styling console output.
# It includes predefined foreground, background, and style codes, as well as helpers
# for composing sequences and generating custom RGB codes.

from __future__ import annotations


class ANSI:
    """
    ANSI escape sequences for styling text in console output.

    Provides:
        - RESET: Reset all attributes.
        - STYLE: Bold, dim, italic, underline, inverse.
        - FG: Foreground colors (standard and bright).
        - BG: Background colors (standard and bright).
        - compose(): Combine multiple ANSI parts.
        - rgb(): Build custom RGB foreground color.
        - bg_rgb(): Build custom RGB background color.
    """

    RESET: str = "\x1b[0m"

    class STYLE:
        BOLD: str = "\x1b[1m"
        DIM: str = "\x1b[2m"
        ITALIC: str = "\x1b[3m"
        UNDERLINE: str = "\x1b[4m"
        INVERSE: str = "\x1b[7m"

    class FG:
        BLACK: str = "\x1b[30m"
        RED: str = "\x1b[31m"
        GREEN: str = "\x1b[32m"
        YELLOW: str = "\x1b[33m"
        BLUE: str = "\x1b[34m"
        MAGENTA: str = "\x1b[35m"
        CYAN: str = "\x1b[36m"
        WHITE: str = "\x1b[37m"
        BRIGHT_BLACK: str = "\x1b[90m"
        BRIGHT_RED: str = "\x1b[91m"
        BRIGHT_GREEN: str = "\x1b[92m"
        BRIGHT_YELLOW: str = "\x1b[93m"
        BRIGHT_BLUE: str = "\x1b[94m"
        BRIGHT_MAGENTA: str = "\x1b[95m"
        BRIGHT_CYAN: str = "\x1b[96m"
        BRIGHT_WHITE: str = "\x1b[97m"

    class BG:
        BLACK: str = "\x1b[40m"
        RED: str = "\x1b[41m"
        GREEN: str = "\x1b[42m"
        YELLOW: str = "\x1b[43m"
        BLUE: str = "\x1b[44m"
        MAGENTA: str = "\x1b[45m"
        CYAN: str = "\x1b[46m"
        WHITE: str = "\x1b[47m"
        BRIGHT_BLACK: str = "\x1b[100m"
        BRIGHT_RED: str = "\x1b[101m"
        BRIGHT_GREEN: str = "\x1b[102m"
        BRIGHT_YELLOW: str = "\x1b[103m"
        BRIGHT_BLUE: str = "\x1b[104m"
        BRIGHT_MAGENTA: str = "\x1b[105m"
        BRIGHT_CYAN: str = "\x1b[106m"
        BRIGHT_WHITE: str = "\x1b[107m"

    @staticmethod
    def compose(*parts: str) -> str:
        """
        Combine multiple ANSI sequences into one.

        Args:
            *parts (str): One or more ANSI strings.

        Returns:
            str: Concatenated ANSI sequence.
        """
        return "".join(parts)

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """
        Create a foreground RGB color ANSI sequence.

        Args:
            r (int): Red component [0-255].
            g (int): Green component [0-255].
            b (int): Blue component [0-255].

        Returns:
            str: ANSI sequence for the RGB foreground color.
        """
        return f"\x1b[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """
        Create a background RGB color ANSI sequence.

        Args:
            r (int): Red component [0-255].
            g (int): Green component [0-255].
            b (int): Blue component [0-255].

        Returns:
            str: ANSI sequence for the RGB background color.
        """
        return f"\x1b[48;2;{r};{g};{b}m"
