"""Doc<->code coherence ratchets — the mechanical guard against divergence-doc rot.

Instantiated from claude-setup-kit for LoggerPlusPlus. These turn the largest rot class found in the
2026-09 retrofit (the src-layout + Poetry migration never propagated into the docs) into gate-red.

Objective, string-level facts only (a name, a path). Prose accuracy stays a review concern. Every
check carries an EXCEPTIONS set with a required reason, so a deliberate divergence is an explicit
decision, not a silent one.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

import loggerplusplus
from loggerplusplus import formats as lpp_formats

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# Backticked repo paths in tracked docs must exist. Prefixes = this project's top-level dirs.
_PATH_REF = re.compile(r"`((?:src|tests|docs|examples|test_module)/[A-Za-z0-9_.\-/]+)`")

# Public names deliberately not documented in README/docs, each WITH A REASON.
_UNDOCUMENTED_NAMES: frozenset[str] = frozenset(
    {
        "__version__",  # metadata, not an API name
        "logger",  # documented as the `loggerplusplus` singleton it aliases
        "LoggerPlusPlus",  # the proxy class; README documents the `loggerplusplus` singleton instance
    }
)

_UNDOCUMENTED_FORMATS: frozenset[str] = frozenset()  # add ONLY with a reason


def _is_deliberately_local(ref: str) -> bool:
    """Absent-but-legitimate: a tracked `.example` template exists, or git declares it ignored."""
    if (_REPO_ROOT / f"{ref}.example").exists():
        return True
    probe = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "check-ignore", "-q", ref],
        capture_output=True,
        check=False,
    )
    return probe.returncode == 0


def _dead_refs_in(path: pathlib.Path) -> list[str]:
    """Return a 'doc: ref' string for every backticked repo path in *path* that does not exist."""
    dead: list[str] = []
    for match in _PATH_REF.finditer(path.read_text(encoding="utf-8")):
        ref = match.group(1).rstrip("/").rstrip(".")
        if (_REPO_ROOT / ref).exists() or _is_deliberately_local(ref):
            continue
        dead.append(f"{path.relative_to(_REPO_ROOT)}: `{ref}`")
    return dead


def _doc_corpus() -> str:
    """Concatenated text of every user-facing doc (README + tracked docs/*.md)."""
    parts: list[str] = []
    readme = _REPO_ROOT / "README.md"
    if readme.exists():
        parts.append(readme.read_text(encoding="utf-8"))
    for doc in sorted((_REPO_ROOT / "docs").glob("*.md")):
        parts.append(doc.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_tracked_docs_path_references_exist() -> None:
    """Every backticked repo path in README + docs/*.md points at something on disk."""
    docs = [_REPO_ROOT / "README.md"] + sorted((_REPO_ROOT / "docs").glob("*.md"))
    dead = [ref for doc in docs if doc.exists() for ref in _dead_refs_in(doc)]
    assert not dead, (
        "Dead repo-path reference(s) in tracked docs — update the doc in the same change that "
        f"moved/removed the path: {dead}"
    )


def test_every_public_format_is_documented() -> None:
    """Every concrete format class (resolved BY NAME downstream) appears in the docs corpus."""
    corpus = _doc_corpus()
    concrete = [
        name
        for name in lpp_formats.__all__
        if name.endswith("Format") and name != "BaseFormat"
    ]
    missing = sorted(
        name
        for name in concrete
        if name not in corpus and name not in _UNDOCUMENTED_FORMATS
    )
    assert not missing, (
        f"Format class(es) absent from README/docs: {missing}. Downstream selects formats by name "
        "from LOGGING_LPP_FORMAT — document each (name VERBATIM) in the README formats table and "
        "docs/FORMATS.md, or exempt it in _UNDOCUMENTED_FORMATS with a reason."
    )


def test_every_public_name_is_documented() -> None:
    """Every exported name in loggerplusplus.__all__ appears literally in the docs corpus."""
    corpus = _doc_corpus()
    missing = sorted(
        name
        for name in loggerplusplus.__all__
        if name not in corpus and name not in _UNDOCUMENTED_NAMES
    )
    assert not missing, (
        f"Public name(s) absent from README/docs: {missing}. Document each (name VERBATIM) in "
        "README.md or docs/REFERENCE.md in the same change that exports it, or exempt it in "
        "_UNDOCUMENTED_NAMES with a reason."
    )


@pytest.mark.skipif(
    not (_REPO_ROOT / "CLAUDE.md").exists(),
    reason="CLAUDE.md is git-excluded (local-only); nothing to check on CI",
)
def test_claude_md_referenced_paths_exist() -> None:
    """A stale CLAUDE.md path misleads every future session — the src-layout drift lived here."""
    dead = _dead_refs_in(_REPO_ROOT / "CLAUDE.md")
    assert (
        not dead
    ), f"CLAUDE.md references dead repo path(s) — fix the Structure tree: {dead}"
