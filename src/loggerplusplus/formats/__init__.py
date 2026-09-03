from __future__ import annotations

from .base import BaseFormat as BaseFormat
from .classic import ClassicFormat
from .debug import DebugFormat
from .file import FileFormat
from .minimal import MinimalFormat
from .ops import OpsFormat
from .plain import PlainFormat
from .short import ShortFormat
from .theme import DEFAULT_THEME as DEFAULT_THEME
from .theme import Theme as Theme

# ------------------- Public API ------------------- #
# NOTE: __all__ lists exactly the concrete, name-resolvable formats (a downstream
# contract). BaseFormat / Theme / DEFAULT_THEME are re-exported (redundant-alias form)
# so they are importable from this namespace, but kept out of __all__ on purpose.
__all__ = [
    "ClassicFormat",
    "DebugFormat",
    "FileFormat",
    "MinimalFormat",
    "OpsFormat",
    "PlainFormat",
    "ShortFormat",
]
