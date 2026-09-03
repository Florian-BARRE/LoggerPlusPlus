# ====== Code Summary ======
# Abstract base class for string-based formatting classes.
# Provides a structured interface for defining reusable, stylized text formats
# with optional colorization and separators, plus shared segment builders so the
# concrete formats don't each re-spell the timestamp / level / identifier blocks.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union

from .theme import DEFAULT_THEME, Theme

__all__: list[str] = ["BaseFormat"]

_WidthT = Union[int, str]


class BaseFormat(str, ABC):
    """
    Abstract base class for reusable string-based formats.

    Why inherit from `str`: an instance must be usable *directly* as a loguru format
    (`add(format=ClassicFormat())`). `__new__` runs the subclass `format()` to produce the
    template and returns a real `str` initialized with it — so `ClassicFormat()` IS the
    format string while still being a class you can subclass and override.

    Attributes:
        colorized (bool): Whether the output should be colorized (default: True).
        separator (str): Default separator string between parts (default: '|').
        separator_dim (bool): Whether the separator should be rendered dimmed (default: True).
    """

    colorized: bool = True
    separator: str = "|"
    separator_dim: bool = True

    # ---- Shared segment builders (keep concrete formats DRY) ---- #

    @staticmethod
    def _paint(content: str, color: str, colorized: bool) -> str:
        """Wrap `content` in a `<color>` tag when colorized, else return it unstyled."""
        return f"<{color}>{content}</{color}>" if colorized else content

    @staticmethod
    def _sep(sep: str, dim: bool, colorized: bool, theme: Theme = DEFAULT_THEME) -> str:
        """
        Returns a formatted separator string with optional dimmed styling.

        Args:
            sep (str): The separator character(s).
            dim (bool): Whether to apply dimming.
            colorized (bool): Whether to apply colorization.
            theme (Theme): Color theme supplying the separator color.

        Returns:
            str: The final separator string, potentially with style markup.
        """
        # If both colorization and dimming are enabled, apply the theme's separator color
        c = theme.separator
        return f"<{c}>{sep}</{c}>" if colorized and dim else sep

    @classmethod
    def _timestamp(cls, colorized: bool = True, theme: Theme = DEFAULT_THEME) -> str:
        """Return the timestamp segment, italic + theme-colored when colorized."""
        ts = "{time:YYYY-MM-DD HH:mm:ss.SSS}"
        return (
            f"<italic>{cls._paint(ts, theme.timestamp, colorized)}</italic>"
            if colorized
            else ts
        )

    @classmethod
    def _level(cls, width: _WidthT, colorized: bool = True) -> str:
        """Return the center-aligned log-level segment (level-colored when colorized)."""
        return cls._paint(f"{{level.name:^{width}}}", "level", colorized)

    @classmethod
    def _identifier(
        cls, width: _WidthT, colorized: bool = True, theme: Theme = DEFAULT_THEME
    ) -> str:
        """Return the middle-truncated identifier segment (theme-colored when colorized)."""
        return cls._paint(
            f"{{identifier:^{width}~middle}}", theme.identifier, colorized
        )

    @classmethod
    def _process_thread(
        cls,
        process_name_width: _WidthT,
        process_id_width: _WidthT,
        thread_name_width: _WidthT,
        thread_id_width: _WidthT,
        colorized: bool = True,
        theme: Theme = DEFAULT_THEME,
    ) -> str:
        """Return the process (PID) + thread (TID) metadata segment."""
        pid_part = (
            f"PID:{{process.name:<{process_name_width}~middle}}"
            f"[{{process.id:^{process_id_width}~middle}}]"
        )
        tid_part = (
            f"TID:{{thread.name:<{thread_name_width}~middle}}"
            f"[{{thread.id:^{thread_id_width}~middle}}]"
        )
        return (
            cls._paint(pid_part, theme.process, colorized)
            + " "
            + cls._paint(tid_part, theme.thread, colorized)
        )

    @classmethod
    def _location(
        cls,
        name_width: _WidthT,
        line_width: _WidthT,
        colorized: bool = True,
        theme: Theme = DEFAULT_THEME,
    ) -> str:
        """Return the source name + line-number segment."""
        name_part = f"{{name:<{name_width}~middle}}:"
        line_part = f"{{line:<{line_width}~middle}}"
        return (
            cls._paint(name_part, theme.name, colorized)
            + cls._paint(line_part, theme.line, colorized)
            + " "
        )

    @classmethod
    def _message(cls, colorized: bool = True) -> str:
        """Return the message segment (level-colored when colorized)."""
        return cls._paint("{message}", "level", colorized)

    @classmethod
    def build(cls, *parts: str) -> str:
        """
        Constructs the final formatted string by joining non-empty parts.

        Args:
            *parts (str): Variable number of string components to concatenate.

        Returns:
            str: Concatenated string built from non-empty components.
        """
        # 1. Filter out empty parts and join them into one string
        return "".join(p for p in parts if p)

    def __new__(cls, **overrides: Any) -> BaseFormat:
        """
        Constructs a new instance of the format class as a `str`.

        Args:
            **overrides: Optional keyword arguments passed to the subclass's `format()`.

        Returns:
            BaseFormat: A string instance of the format class.
        """
        # 1. Ask subclass to construct the format string
        fmt = cls.format(**overrides)

        # 2. Create and return a string instance of the subclass
        return super().__new__(cls, fmt)

    @classmethod
    @abstractmethod
    def format(cls, **overrides: Any) -> str:
        """
        Abstract method implemented by subclasses to construct the format string.

        Args:
            **overrides: Optional keyword arguments to customize the formatting.

        Returns:
            str: The constructed format string.
        """
        ...
