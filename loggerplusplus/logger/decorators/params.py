# ====== Code Summary ======
# This module provides utilities for annotating function parameters with
# metadata (`ParamMeta`) that influences logging behavior. It includes the
# `LogParam` wrapper for marking parameters as sensitive or setting a maximum
# representation length, and helper functions for extracting parameter metadata.

# ====== Standard Library Imports ======
from dataclasses import dataclass
from typing import Any, Type, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ParamMeta:
    """
    Metadata associated with a function parameter for logging.

    Attributes:
        sensitive (bool): Whether the parameter should be masked in logs.
        max_repr_len (int | None): Maximum length of repr() when logged, or None for default.
    """

    sensitive: bool = False
    max_repr_len: int | None = None


# Cache of dynamically created subclasses used for wrapping parameters
_SUBCLASS_CACHE: dict[Type[Any], Type[Any]] = {}


def _subclass_for(base: Type[Any]) -> Type[Any]:
    """
    Get or create a dynamic subclass of a given base type with an extra
    `__lpp_meta__` slot for storing parameter metadata.

    Args:
        base (Type[Any]): The base type to wrap.

    Returns:
        Type[Any]: A dynamically created subclass with metadata support.
    """
    cls = _SUBCLASS_CACHE.get(base)
    if cls is not None:
        return cls

    cls = type(
        f"_LPPParam_{base.__name__}",
        (base,),
        {"__slots__": ("__lpp_meta__",)},
    )
    _SUBCLASS_CACHE[base] = cls
    return cls


def LogParam(
        default: T, *, sensitive: bool = False, max_repr_len: int | None = None
) -> T:
    """
    Wrap a default parameter value with metadata for logging.

    Args:
        default (T): The original default parameter value.
        sensitive (bool): Whether to mask this parameter in logs.
        max_repr_len (int | None): Maximum repr() length for the parameter.

    Returns:
        T: A wrapped instance of the original value with metadata attached.
    """
    if default is None:
        return default  # type: ignore[return-value]

    base = type(default)
    cls = _subclass_for(base)

    # Create wrapped instance and attach metadata
    wrapped = cls(default)  # type: ignore[call-arg]
    setattr(
        wrapped,
        "__lpp_meta__",
        ParamMeta(sensitive=sensitive, max_repr_len=max_repr_len),
    )
    return wrapped  # type: ignore[return-value]


def extract_param_meta(default_value: Any) -> ParamMeta | None:
    """
    Extract parameter metadata from a wrapped default value.

    Args:
        default_value (Any): Default value that may be wrapped with metadata.

    Returns:
        ParamMeta | None: The extracted metadata, or None if not present.
    """
    if default_value is None:
        return None
    return getattr(default_value, "__lpp_meta__", None)
