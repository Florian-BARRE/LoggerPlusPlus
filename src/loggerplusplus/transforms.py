# ====== Code Summary ======
# The generalised "transform the message string before it is emitted" concept: the `Transform`
# type alias plus a few small, composable helpers. Banners (`Banner`) are the flagship transform
# toolkit and are re-exported here so `transforms.Banner` and top-level `Banner` both work. A
# transform is any `Callable[[str], str]`, so `str.upper`, a lambda, or a user function all plug
# into the `transform=` keyword of every level method.

from __future__ import annotations

from typing import Callable

from .banners import Banner

__all__: list[str] = ["Transform", "Banner", "chain", "indent", "upper", "lower"]

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
