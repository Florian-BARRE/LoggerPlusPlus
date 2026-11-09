# ====== Code Summary ======
# LEGACY-SEAM: re-home — remove in R-00
# Re-export shim for the auto-width token parser, now re-homed in
# `loggerplusplus.auto_width.parser`. Keeps the historical import path
# `loggerplusplus.parser` resolving while the internal layout moves.
#
# This file holds NO logic: it only re-exports the names the pre-move
# importers (api, and the test suite) still reach for, so `import
# loggerplusplus` and the full suite keep resolving byte-identically.
# Remove this file in ticket R-00 (the layout re-wiring).

from __future__ import annotations

from .auto_width.parser import _TOKEN_RE, _AutoMap, prepare_auto_format

# Re-exported names (mypy `strict` uses `--no_implicit_reexport`, so the
# shim's public surface is declared explicitly here).
__all__: list[str] = [
    "_AutoMap",
    "_TOKEN_RE",
    "prepare_auto_format",
]
