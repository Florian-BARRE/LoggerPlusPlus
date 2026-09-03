# ====== Code Summary ======
# Smoke test: every example script runs to completion (exit 0) in a fresh subprocess.
# Keeps the documented examples honest — they can never silently rot.

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
_SCRIPTS = sorted(_EXAMPLES_DIR.glob("*.py"))


@pytest.mark.parametrize("script", _SCRIPTS, ids=lambda p: p.name)
def test_example_runs(script: Path) -> None:
    """The example script exits cleanly."""
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_examples_are_present() -> None:
    """The examples directory holds the expected runnable scripts."""
    assert len(_SCRIPTS) >= 6
