# ====== Code Summary ======
# This module defines the `LoggerConfig` dataclass, which centralizes configuration
# for logger behavior including formatting, file handling, levels, outputs, and
# stack inspection performance options.

# ====== Standard Library Imports ======
from __future__ import annotations
from dataclasses import dataclass, field

# ====== Local Project Imports ======
from .format import FormatConfig
from .file import FileConfig
from .level import LevelConfig
from .output import OutputConfig


@dataclass(slots=True)
class LoggerConfig:
    """
    Configuration container for logger settings.

    This dataclass encapsulates settings for log formatting, file logging, log levels,
    output destinations, and stack inspection behavior. It is intended to provide a
    centralized configuration structure for initializing and controlling logging behavior.

    Attributes:
        identifier (str): Unique identifier for the logger (default: "unknown").
        fmt (FormatConfig | None): Optional log formatting configuration.
        files (FileConfig): File logging configuration, defaults to a new `FileConfig`.
        levels (LevelConfig): Log level configuration, defaults to a new `LevelConfig`.
        outputs (OutputConfig): Output destination configuration, defaults to a new `OutputConfig`.
        propagate (bool): Whether logs should propagate to parent loggers (default: True).
        fast_stacklevel (bool): If True, forces `stacklevel=1` for faster but less accurate
            file:line reporting (default: False).
        default_stacklevel (int): Stacklevel used when `fast_stacklevel` is False and
            no explicit stacklevel is provided (default: 2).
    """

    identifier: str = "unknown"
    fmt: FormatConfig | None = None
    files: FileConfig = field(default_factory=FileConfig)
    levels: LevelConfig = field(default_factory=LevelConfig)
    outputs: OutputConfig = field(default_factory=OutputConfig)
    propagate: bool = True

    # Performance/stack inspection
    fast_stacklevel: bool = False  # if True, force stacklevel=1 (faster, less accurate file:line)
    default_stacklevel: int = 2  # used if fast_stacklevel is False and no explicit stacklevel is given
