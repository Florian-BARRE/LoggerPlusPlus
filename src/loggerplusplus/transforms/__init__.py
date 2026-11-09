# ====== Code Summary ======
# The message-transform toolkit, now a sub-package. This is the FROZEN public surface: it exposes
# exactly the names the old root `transforms` module used to (the `Transform` alias plus the
# `chain`/`indent`/`upper`/`lower` helpers, and the `Banner` toolkit re-exported from the sibling
# `banners` module), so `transforms.Banner`, top-level `Banner` and every dotted `transforms.*`
# name keep resolving after the module->package move. Import from this facade, not the internals.

from __future__ import annotations

from .banners import Banner as Banner
from .helpers import Transform as Transform
from .helpers import chain as chain
from .helpers import indent as indent
from .helpers import lower as lower
from .helpers import upper as upper

# ------------------- Public API -------------------
__all__ = ["Transform", "Banner", "chain", "indent", "upper", "lower"]
