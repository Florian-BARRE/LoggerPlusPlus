# ====== Code Summary ======
# Phase 5 structure-resolves check for the `auto_width/` sub-package (ticket R-02).
#
# The auto-width engine (width / parser / filter / registry) moved from four flat
# root modules into the `loggerplusplus.auto_width` sub-package; `runtime.py` was
# renamed `filter.py`. The old root modules are now thin LEGACY-SEAM re-export
# shims (removed in ticket R-00) so the non-re-wired importers (`__init__`, `api`,
# `logger_class`, the existing test suite) keep resolving byte-identically.
#
# This test pins that STRUCTURE, not behaviour: the new home resolves, the internal
# facade and the four sub-modules expose the engine pieces, the root shims still
# expose the pre-move names, and every root/facade export IS the very same object as
# its defining home in `auto_width/` (a pure re-export, never a copy). It performs no
# rendering, so no golden bytes are pinned here.

from __future__ import annotations

import loggerplusplus
import loggerplusplus.auto_width.filter as aw_filter
import loggerplusplus.auto_width.parser as aw_parser
import loggerplusplus.auto_width.registry as aw_registry
import loggerplusplus.auto_width.width as aw_width
import loggerplusplus.parser as root_parser
import loggerplusplus.registry as root_registry
import loggerplusplus.runtime as root_runtime
import loggerplusplus.width as root_width
from loggerplusplus.auto_width import (
    compose_filter,
    import_widths,
    observed_widths,
    prepare_auto_format,
    register_identifier,
    reset_widths,
    set_max_auto_width,
    visual_width,
)

# ====== 1. the new home resolves: the four sub-modules exist ====== #


def test_submodules_resolve_and_carry_their_units() -> None:
    """Each of the four sub-modules is importable and carries its defining units."""
    # parser: prepare_auto_format + _AutoMap (+ the token regex the parser is built from)
    assert hasattr(aw_parser, "prepare_auto_format")
    assert hasattr(aw_parser, "_AutoMap")
    assert hasattr(aw_parser, "_TOKEN_RE")
    # filter: compose_filter + the dict-filter helper
    assert hasattr(aw_filter, "compose_filter")
    assert hasattr(aw_filter, "_build_dict_filter")
    # registry: the five public controls + the registry class + its private singletons
    assert hasattr(aw_registry, "register_identifier")
    assert hasattr(aw_registry, "reset_widths")
    assert hasattr(aw_registry, "observed_widths")
    assert hasattr(aw_registry, "set_max_auto_width")
    assert hasattr(aw_registry, "import_widths")
    assert hasattr(aw_registry, "_AutoWidthRegistry")
    assert hasattr(aw_registry, "_AUTO")
    assert hasattr(aw_registry, "_IDENTIFIER_SPEC")
    # width: the visual-width (terminal-cell) metrics
    assert hasattr(aw_width, "visual_width")
    assert hasattr(aw_width, "sanitize")
    assert hasattr(aw_width, "truncate")
    assert hasattr(aw_width, "pad")
    assert hasattr(aw_width, "hard_cut")
    assert hasattr(aw_width, "render_field")


# ====== 2. the internal facade re-exports the same objects as the sub-modules ====== #


def test_facade_reexports_are_the_same_objects_as_the_submodules() -> None:
    """Names imported from the `auto_width` facade ARE the sub-module definitions."""
    assert aw_parser.prepare_auto_format is prepare_auto_format
    assert aw_filter.compose_filter is compose_filter
    assert aw_width.visual_width is visual_width
    assert aw_registry.register_identifier is register_identifier
    assert aw_registry.reset_widths is reset_widths
    assert aw_registry.observed_widths is observed_widths
    assert aw_registry.set_max_auto_width is set_max_auto_width
    assert aw_registry.import_widths is import_widths


# ====== 3. the root LEGACY-SEAM shims still expose the pre-move names ====== #


def test_root_shims_still_expose_the_premove_names() -> None:
    """The historical root modules resolve to the very same objects as the new home."""
    # parser (shim of auto_width.parser)
    assert root_parser.prepare_auto_format is prepare_auto_format
    assert root_parser._AutoMap is aw_parser._AutoMap
    assert root_parser._TOKEN_RE is aw_parser._TOKEN_RE
    # runtime (shim of auto_width.filter, renamed)
    assert root_runtime.compose_filter is compose_filter
    assert root_runtime._build_dict_filter is aw_filter._build_dict_filter
    # registry (shim of auto_width.registry)
    assert root_registry.register_identifier is register_identifier
    assert root_registry.reset_widths is reset_widths
    assert root_registry.observed_widths is observed_widths
    assert root_registry.set_max_auto_width is set_max_auto_width
    assert root_registry.import_widths is import_widths
    assert root_registry._AutoWidthRegistry is aw_registry._AutoWidthRegistry
    assert root_registry._AUTO is aw_registry._AUTO
    assert root_registry._IDENTIFIER_SPEC is aw_registry._IDENTIFIER_SPEC
    # width (shim of auto_width.width)
    assert root_width.visual_width is visual_width
    assert root_width.sanitize is aw_width.sanitize
    assert root_width.truncate is aw_width.truncate
    assert root_width.pad is aw_width.pad
    assert root_width.hard_cut is aw_width.hard_cut
    assert root_width.render_field is aw_width.render_field


# ====== 4. the frozen public surface is unchanged and resolves to the new home ====== #


def test_frozen_public_surface_is_unchanged() -> None:
    """The five auto-width controls stay in `__all__` and resolve to the new home."""
    frozen_controls = {
        "register_identifier",
        "reset_widths",
        "observed_widths",
        "set_max_auto_width",
        "import_widths",
    }
    assert frozen_controls.issubset(set(loggerplusplus.__all__))
    # The top-level facade names ARE the same objects now defined in auto_width/registry.
    assert loggerplusplus.register_identifier is register_identifier
    assert loggerplusplus.reset_widths is reset_widths
    assert loggerplusplus.observed_widths is observed_widths
    assert loggerplusplus.set_max_auto_width is set_max_auto_width
    assert loggerplusplus.import_widths is import_widths
