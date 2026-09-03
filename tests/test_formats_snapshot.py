# ====== Code Summary ======
# Golden-string snapshots of every shipped format. These lock the EXACT rendered
# format string (colorized and plain) so any refactor of the format skeleton stays
# byte-identical — the formats are resolved by name downstream and a silent change
# would alter every consumer's log output.

from __future__ import annotations

import pytest

from loggerplusplus import formats as F

# Golden strings captured from the shipped formats. Do NOT edit to make a refactor
# pass — a diff here means the rendered output changed and downstream logs changed.
_GOLDEN = {
    "ShortFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><level>{message}</level>",
        "plain": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | [{identifier:^auto~middle}] | {message}",
    },
    "OpsFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> <light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan><light-black> | </light-black><level>{message}</level>",
        "plain": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | [{identifier:^auto~middle}] | PID:{process.name:<auto~middle}[{process.id:^auto~middle}] TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}] | {message}",
    },
    "DebugFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> <light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan><light-black> | </light-black><magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta> <light-black> | </light-black><level>{message}</level>",
        "plain": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | [{identifier:^auto~middle}] | PID:{process.name:<auto~middle}[{process.id:^auto~middle}] TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}] | {name:<auto~middle}:{line:<auto~middle}  | {message}",
    },
    "MinimalFormat": {
        "colorized": "<light-green>{identifier:^auto~middle}</light-green><light-black> -> </light-black><level>{message}</level>",
        "plain": "{identifier:^auto~middle} -> {message}",
    },
    "ClassicFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta> <light-black> | </light-black><level>{message}</level>",
        "plain": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name:^8} | [{identifier:^auto~middle}] | {name:<auto~middle}:{line:<auto~middle}  | {message}",
    },
}


@pytest.mark.parametrize("name", sorted(_GOLDEN))
def test_colorized_output_is_byte_identical(name: str) -> None:
    """The colorized rendered string matches its locked golden exactly."""
    cls = getattr(F, name)
    assert str(cls()) == _GOLDEN[name]["colorized"]


@pytest.mark.parametrize("name", sorted(_GOLDEN))
def test_plain_output_is_byte_identical(name: str) -> None:
    """The plain (colorized=False) rendered string matches its locked golden exactly."""
    cls = getattr(F, name)
    assert str(cls(colorized=False)) == _GOLDEN[name]["plain"]


@pytest.mark.parametrize("name", sorted(_GOLDEN))
def test_plain_output_has_no_color_tags(name: str) -> None:
    """colorized=False must drop every color tag (no ANSI leaks into file sinks)."""
    cls = getattr(F, name)
    # Color tags always have a closing `</...>`; a bare `<` is only the align glyph.
    assert "</" not in str(cls(colorized=False))


def test_snapshot_covers_every_shipped_format() -> None:
    """Every name in formats.__all__ has a locked snapshot (guards against a new, untested format)."""
    assert set(F.__all__) == set(_GOLDEN)
