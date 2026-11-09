# ====== Code Summary ======
# LEGACY-SEAM: re-home — remove in R-00
# Re-export shim for the auto-width registry, now re-homed in
# `loggerplusplus.auto_width.registry`. Keeps the historical import path
# `loggerplusplus.registry` resolving while the internal layout moves.
#
# This file holds NO logic: it only re-exports the names the pre-move
# importers (the `__init__` facade, `logger_class`, and the test suite,
# which also reaches the private `_AUTO` / `_IDENTIFIER_SPEC` /
# `_AutoWidthRegistry`) still pull from this path, so `import loggerplusplus`
# and the full suite keep resolving byte-identically.
# Remove this file in ticket R-00 (the layout re-wiring).

from __future__ import annotations

from .auto_width.registry import (
    _AUTO,
    _IDENTIFIER_SPEC,
    _AutoWidthRegistry,
    import_widths,
    observed_widths,
    register_identifier,
    reset_widths,
    set_max_auto_width,
)

# Re-exported names (mypy `strict` uses `--no_implicit_reexport`, so the
# shim's public surface is declared explicitly here).
__all__: list[str] = [
    "_AUTO",
    "_AutoWidthRegistry",
    "_IDENTIFIER_SPEC",
    "import_widths",
    "observed_widths",
    "register_identifier",
    "reset_widths",
    "set_max_auto_width",
]
