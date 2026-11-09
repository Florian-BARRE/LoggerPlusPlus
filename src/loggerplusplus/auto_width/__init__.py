# ====== Code Summary ======
# Internal facade of the auto-width engine sub-package. Re-exports the pieces
# the rest of the package imports from the engine (the public width controls,
# the format parser, the per-record filter composer and the width metrics),
# and makes the four sub-modules (width / parser / filter / registry) importable
# as `loggerplusplus.auto_width.<name>`.
#
# This is an INTERNAL facade: it is not part of the frozen public surface
# (`loggerplusplus.__all__`). It exists so internal importers depend on one
# stable home for the engine, and so the sub-modules resolve as attributes.

from __future__ import annotations

from .filter import compose_filter
from .parser import prepare_auto_format
from .registry import (
    import_widths,
    observed_widths,
    register_identifier,
    reset_widths,
    set_max_auto_width,
)
from .width import visual_width

# ------------------- Internal engine surface ------------------- #
# Public width controls (the same five the frozen `loggerplusplus.__all__`
# exposes) plus the engine pieces internal importers reach for directly.
# The four sub-modules (width, parser, filter, registry) are also importable
# as `loggerplusplus.auto_width.<name>` (the `from .X import ...` above imports
# each sub-module, which sets it as an attribute of this package).
__all__: list[str] = [
    "register_identifier",
    "reset_widths",
    "observed_widths",
    "set_max_auto_width",
    "import_widths",
    "prepare_auto_format",
    "compose_filter",
    "visual_width",
]
