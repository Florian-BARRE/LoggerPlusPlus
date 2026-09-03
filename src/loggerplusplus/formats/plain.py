# ====== Code Summary ======
# A compact, uncolored format (the Short layout without color tags), intended for file
# sinks where ANSI markup is undesirable. Selectable by name like the other formats.

from __future__ import annotations

from typing import Any

from .short import ShortFormat

__all__: list[str] = ["PlainFormat"]


class PlainFormat(ShortFormat):
    """
    The Short layout (time, level, identifier, message) rendered without color.

    Defaults `colorized=False`, so `PlainFormat()` is plain; pass `colorized=True` to
    reintroduce color tags. Useful as a named format for file sinks.
    """

    @classmethod
    def format(cls, *, colorized: bool = False, **overrides: Any) -> str:
        """Build the Short layout, uncolored by default."""
        return super().format(colorized=colorized, **overrides)
