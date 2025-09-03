"""
Top-level public API surface.
Keep it small, obvious, and stable.
"""

from .factory import LoggerPlusPlus
from .logger.manager import LoggerManager
from .config import LoggerConfig, FormatConfig, SeparatorConfig, LevelConfig, OutputConfig, FileConfig


from .loglevel import install_fatal_level

install_fatal_level()

__all__ = [
    "LoggerPlusPlus",
    "LoggerManager",
    "LoggerConfig",
]
