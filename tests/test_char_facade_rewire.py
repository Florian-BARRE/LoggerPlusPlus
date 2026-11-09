# ====== Code Summary ======
# Characterization test for ticket R-00 (facade re-wiring, Wave 2): the
# `__init__.py` facade now pulls two objects from their new homes.
#
#   * `SENSITIVE_KEYS`   comes from `loggerplusplus.redact`
#     (carved out of `decorators.py` by R-03), not from `decorators`.
#   * the auto-width registry names (incl. `import_widths`) come from
#     `loggerplusplus.auto_width.registry` (re-homed by R-02), not from the
#     legacy root `loggerplusplus.registry` shim.
#
# These pin that the re-wiring is byte-identical in behaviour: the same
# objects are reachable as before, and the legacy seams still hold
# (`decorators.SENSITIVE_KEYS` re-exports the very same object `redact` owns).

from __future__ import annotations

import loggerplusplus
from loggerplusplus import decorators, redact
from loggerplusplus.auto_width import registry as auto_width_registry


def test_facade_sensitive_keys_comes_from_redact() -> None:
    """The facade's `SENSITIVE_KEYS` is the object owned by `redact`."""
    assert loggerplusplus.SENSITIVE_KEYS is redact.SENSITIVE_KEYS


def test_facade_import_widths_comes_from_auto_width_registry() -> None:
    """The facade's `import_widths` is the object owned by `auto_width.registry`."""
    assert loggerplusplus.import_widths is auto_width_registry.import_widths


def test_decorators_seam_still_holds() -> None:
    """`decorators.SENSITIVE_KEYS` still re-exports the same object (seam intact)."""
    assert loggerplusplus.SENSITIVE_KEYS is decorators.SENSITIVE_KEYS
