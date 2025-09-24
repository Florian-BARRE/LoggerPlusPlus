# ====== Code Summary ======
# Abstract base class for string-based formatting classes.
# Provides a structured interface for defining reusable, stylized text formats
# with optional colorization and separators, while preserving the ability to use
# the result as a plain string.

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFormat(str, ABC):
    """
    Abstract base class for reusable string-based formats.

    Subclasses inherit from both `str` and `ABC`, enabling the creation of
    stylized string objects while enforcing the implementation of a `format()` method.

    Attributes:
        colorized (bool): Whether the output should be colorized (default: True).
        separator (str): Default separator string between parts (default: '|').
        separator_dim (bool): Whether the separator should be rendered with dimmed styling (default: True).
    """

    colorized: bool = True
    separator: str = "|"
    separator_dim: bool = True

    @staticmethod
    def _sep(sep: str, dim: bool, colorized: bool) -> str:
        """
        Returns a formatted separator string with optional dimmed styling.

        Args:
            sep (str): The separator character(s).
            dim (bool): Whether to apply dimming.
            colorized (bool): Whether to apply colorization.

        Returns:
            str: The final separator string, potentially with style markup.
        """
        # If both colorization and dimming are enabled, apply light-black styling
        return f"<light-black>{sep}</light-black>" if colorized and dim else sep

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

    def __new__(cls, **overrides) -> BaseFormat:
        """
        Constructs a new instance of the format class as a `str`.

        The instantiation process involves:
        1. Calling the subclass-defined `format()` method to get a formatted string.
        2. Returning a new `str` instance of the subclass, initialized with the result.

        Args:
            **overrides: Optional keyword arguments passed to the subclass's `format()` method.

        Returns:
            BaseFormat: A string instance of the format class.
        """
        # 1. Ask subclass to construct the format string
        fmt = cls.format(**overrides)

        # 2. Create and return a string instance of the subclass
        return super().__new__(cls, fmt)

    @classmethod
    @abstractmethod
    def format(cls, **overrides) -> str:
        """
        Abstract method to be implemented by subclasses to construct the format string.

        Args:
            **overrides: Optional keyword arguments to customize the formatting.

        Returns:
            str: The constructed format string.
        """
        ...
