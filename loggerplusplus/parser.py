# ====== Code Summary ======
# Token parser for "auto-width" formatting placeholders used in logging formats.
# Rewrites custom tokens to `extra[...]` placeholders and returns metadata needed
# at runtime to compute widths and truncation.

from __future__ import annotations

# ====== Standard Library Imports ======
import re

__all__: list[str] = [
    "_TOKEN_RE",
    "_AutoMap",
    "prepare_auto_format",
]

# Supported examples:
#   {identifier:<auto}
#   {identifier:<auto[18~middle]}
#   {level.name:^15[10~right]}
#   {extra[service]:>auto[12~left]}
_TOKEN_RE: re.Pattern[str] = re.compile(
    r"\{"
    r"(?P<field>(?:extra\[[^\]]+\]|[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*))"
    r":"
    r"(?P<align>[<>\^])?"
    r"(?P<width>auto|\d+)"
    r"(?:\[(?P<cap>\d+)(?:~(?P<trunc_in>left|right|middle))?\])?"
    r"(?:~(?P<trunc_out>left|right|middle))?"
    r"\}",
    flags=re.UNICODE,
)

# Mapping: (field, placeholder_key, align, width_spec, cap, trunc)
type _AutoMap = tuple[str, str, str, str, int | None, str | None]


def prepare_auto_format(fmt: str) -> tuple[str, list[_AutoMap]]:
    """
    Replace custom auto-width tokens with `extra` placeholders and capture metadata.

    The function scans `fmt` for tokens matching `_TOKEN_RE` (see "Supported examples"
    above), replaces each with a unique `{extra[__lp_auto_i__]}` placeholder, and
    returns both the rewritten format string and a list of mappings used later at
    runtime to compute widths and truncation behavior.

    Args:
        fmt (str): The original format string containing auto-width tokens.

    Returns:
        tuple[str, list[_AutoMap]]: A pair of:
            - The rewritten format string using `extra[...]` placeholders.
            - A list of mappings `(field, placeholder_key, align, width_spec, cap, trunc)`.
    """
    # 1. Initialize state for collected mappings and placeholder indexing
    mappings: list[_AutoMap] = []
    idx: int = 0

    # 2. Define a regex replacement function capturing token components
    def repl(m: re.Match[str]) -> str:
        nonlocal idx
        field_spec: str = m.group("field")
        align: str = m.group("align") or "<"
        width_spec: str = m.group("width")
        cap: int | None = int(m.group("cap")) if m.group("cap") else None
        trunc: str | None = m.group("trunc_in") or m.group("trunc_out")

        # 2.1. Allocate a unique placeholder key for this token
        placeholder_key: str = f"__lp_auto_{idx}__"
        idx += 1

        # 2.2. Record mapping metadata for runtime width/truncation processing
        mappings.append((field_spec, placeholder_key, align, width_spec, cap, trunc))

        # 2.3. Substitute the token with an extra-bound placeholder
        return "{extra[" + placeholder_key + "]}"

    # 3. Rewrite the format string by replacing all tokens
    new_fmt: str = _TOKEN_RE.sub(repl, fmt)

    # 4. Return the rewritten format and the collected mappings
    return new_fmt, mappings
