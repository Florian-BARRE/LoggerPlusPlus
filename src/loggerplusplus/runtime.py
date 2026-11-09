# ====== Code Summary ======
# LEGACY-SEAM: re-home — remove in R-00
# Re-export shim for the per-record auto-width filter composer, now re-homed in
# `loggerplusplus.auto_width.filter` (the root `runtime` was renamed: its role is
# the per-record auto-width filter composer, not a generic "runtime"). Keeps the
# historical import path `loggerplusplus.runtime` resolving while the internal
# layout moves.
#
# This file holds NO logic: it only re-exports the names the pre-move importers
# (api, and the test suite) still pull from this path, so `import loggerplusplus`
# and the full suite keep resolving byte-identically.
# Remove this file in ticket R-00 (the layout re-wiring).

from __future__ import annotations

from .auto_width.filter import _build_dict_filter, compose_filter

# Re-exported names (mypy `strict` uses `--no_implicit_reexport`, so the
# shim's public surface is declared explicitly here).
__all__: list[str] = [
    "_build_dict_filter",
    "compose_filter",
]
