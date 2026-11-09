# ====== Code Summary ======
# The small, composable message-transform helpers: the `Transform` type alias (any
# `Callable[[str], str]`) plus `chain`, `indent`, `upper` and `lower`. A transform is the
# "transform the message string before it is emitted" concept — a plain `str -> str` you hand to
# the `transform=` keyword of every level method, so `str.upper`, a lambda or a user function all
# plug in. `Banner` (the flagship transform toolkit) lives in the sibling `banners` module and is
# re-exported by the package `__init__`, not here.

from __future__ import annotations

from typing import Callable

__all__: list[str] = ["Transform", "chain", "indent", "upper", "lower"]

# A message transform: takes the (already-substituted) message string, returns the string to emit.
Transform = Callable[[str], str]


def chain(*transforms: Transform) -> Transform:
    """
    Compose transforms left-to-right into a single transform.

    Args:
        *transforms (Transform): Transforms applied in order (the first runs first).

    Returns:
        Transform: The composed transform.
    """

    def _composed(text: str) -> str:
        # Apply each transform in declaration order.
        for transform in transforms:
            text = transform(text)
        return text

    return _composed


def indent(prefix: str = "    ") -> Transform:
    """
    Build a transform that prefixes every line of the message.

    Args:
        prefix (str): The string prepended to each line.

    Returns:
        Transform: The indenting transform.
    """

    def _indent(text: str) -> str:
        return "\n".join(f"{prefix}{line}" for line in text.splitlines()) or prefix

    return _indent


def upper(text: str) -> str:
    """
    Uppercase the message.

    Args:
        text (str): The message.

    Returns:
        str: The uppercased message.
    """
    return text.upper()


def lower(text: str) -> str:
    """
    Lowercase the message.

    Args:
        text (str): The message.

    Returns:
        str: The lowercased message.
    """
    return text.lower()
