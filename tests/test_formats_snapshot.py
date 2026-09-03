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
        "plain": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic> | <level>{level.name:^8}</level> | [<light-green>{identifier:^auto~middle}</light-green>] | <level>{message}</level>",
    },
    "OpsFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> <light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan><light-black> | </light-black><level>{message}</level>",
        "plain": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic> | <level>{level.name:^8}</level> | [<light-green>{identifier:^auto~middle}</light-green>] | <cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> <light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan> | <level>{message}</level>",
    },
    "DebugFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> <light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan><light-black> | </light-black><magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta> <light-black> | </light-black><level>{message}</level>",
        "plain": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic> | <level>{level.name:^8}</level> | [<light-green>{identifier:^auto~middle}</light-green>] | <cyan>PID:{process.name:<auto~middle}[{process.id:^auto~middle}]</cyan> <light-cyan>TID:{thread.name:<auto~middle}[{thread.id:^auto~middle}]</light-cyan> | <magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta>  | <level>{message}</level>",
    },
    "MinimalFormat": {
        "colorized": "<light-green>{identifier:^auto~middle}</light-green><light-black> -> </light-black><level>{message}</level>",
        "plain": "<light-green>{identifier:^auto~middle}</light-green> -> <level>{message}</level>",
    },
    "ClassicFormat": {
        "colorized": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic><light-black> | </light-black><level>{level.name:^8}</level><light-black> | </light-black><light-black>[</light-black><light-green>{identifier:^auto~middle}</light-green><light-black>] | </light-black><magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta> <light-black> | </light-black><level>{message}</level>",
        "plain": "<italic><yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow></italic> | <level>{level.name:^8}</level> | [<light-green>{identifier:^auto~middle}</light-green>] | <magenta>{name:<auto~middle}:</magenta><light-magenta>{line:<auto~middle}</light-magenta>  | <level>{message}</level>",
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


def test_snapshot_covers_every_shipped_format() -> None:
    """Every name in formats.__all__ has a locked snapshot (guards against a new, untested format)."""
    assert set(F.__all__) == set(_GOLDEN)
