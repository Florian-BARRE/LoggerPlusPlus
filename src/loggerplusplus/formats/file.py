# ====== Code Summary ======
# A detailed, uncolored format (the Classic layout without color tags), intended for
# file sinks: timestamp, level, identifier, source name:line, message. Selectable by name.

from __future__ import annotations

from typing import Any

from .classic import ClassicFormat

__all__: list[str] = ["FileFormat"]


class FileFormat(ClassicFormat):
    """
    The Classic layout (time, level, identifier, name:line, message) rendered without color.

    Defaults `colorized=False`, so `FileFormat()` is plain; pass `colorized=True` to
    reintroduce color tags. Useful as a named format for file sinks.
    """

    @classmethod
    def format(cls, *, colorized: bool = False, **overrides: Any) -> str:
        """Build the Classic layout, uncolored by default."""
        return super().format(colorized=colorized, **overrides)
