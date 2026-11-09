# ====== Code Summary ======
# LEGACY-SEAM: re-home — remove in R-00
# Re-export shim for the visual-width (terminal-cell) text metrics, now re-homed
# in `loggerplusplus.auto_width.width`. Keeps the historical import path
# `loggerplusplus.width` resolving while the internal layout moves.
#
# This file holds NO logic: it only re-exports the names the pre-move importers
# (registry, filter, and the test suite) still pull from this path, so `import
# loggerplusplus` and the full suite keep resolving byte-identically.
# Remove this file in ticket R-00 (the layout re-wiring).

from __future__ import annotations

from .auto_width.width import (
    hard_cut,
    pad,
    render_field,
    sanitize,
    truncate,
    visual_width,
)

# Re-exported names (mypy `strict` uses `--no_implicit_reexport`, so the
# shim's public surface is declared explicitly here).
__all__: list[str] = [
    "hard_cut",
    "pad",
    "render_field",
    "sanitize",
    "truncate",
    "visual_width",
]
