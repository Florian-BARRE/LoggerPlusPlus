# ====== Code Summary ======
# Minimalistic log format class designed for concise output.
# Focuses on displaying only the identifier and the log message,
# suitable for lightweight logs or simplified console traces.

from __future__ import annotations

# ====== Standard Library Imports ======
from typing import Union

# ====== Local Project Imports ======
from .base import BaseFormat

__all__: list[str] = ["MinimalFormat"]


class MinimalFormat(BaseFormat):
    """
    Minimalist log format for compact output with only essential context.

    This format includes:
        - Identifier (center-aligned and colorized)
        - Log message (with level-based colorization)

    Best suited for environments where screen space or visual noise must be reduced.
    """

    @classmethod
    def format(
        cls,
        *,
        colorized: bool = True,
        identifier_width: Union[int, str] = "auto",
        sep: str = " | ",
    ) -> str:
        """
        Constructs a minimal log format with only identifier and message.

        Args:
            colorized (bool): Whether to apply color/styling tags to the output (default: True).
            identifier_width (int | str): Width for the identifier field (default: "auto").
            sep (str): Separator string (not directly used here but accepted for API compatibility).

        Returns:
            str: A compact log format string.
        """

        # Segments: identifier -> message
        return cls.build(
            cls._identifier(identifier_width),
            cls._sep(" -> ", True, colorized),
            cls._message(),
        )
