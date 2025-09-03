# ====== Code Summary ======
# This module defines the `ShortLayout`, a compact implementation of BaseLayout.
# It produces a minimal log format with timestamp, level, identifier, and message,
# using concise field widths and truncation rules.

from __future__ import annotations

# ====== Local Project Imports ======
from ..base import BaseLayout
from ..rules import FieldRule, Align, Truncate
from ..log_token import LogToken


class ShortLayout(BaseLayout):
    """
    A short/minimal log layout: `time, level, ident, message`.

    Default Template:
        "{date} [{level}] {id} | {msg}"

    Notes:
        - Provides concise defaults for level and ident fields.
        - Falls back to standard timestamp format if not provided.
    """

    def __init__(
            self,
            template: str | None = None,
            rules: dict[LogToken, FieldRule] | None = None,
            time_fmt: str | None = None,
    ) -> None:
        """
        Initialize the ShortLayout with optional overrides.

        Args:
            template (str | None): Custom log line template.
            rules (dict[LogToken, FieldRule] | None): Custom field formatting rules.
            time_fmt (str | None): Custom strftime format for date/time fields.
        """
        super().__init__(
            template=(
                    template
                    or f"{LogToken.DATE} [{LogToken.LEVEL}] [{LogToken.IDENT}] | {LogToken.MSG}"
            ),
            rules=(
                    rules
                    or {
                        LogToken.LEVEL: FieldRule(
                            7,
                            align=Align.CENTER,
                            truncate=Truncate.TAIL,
                        ),
                        LogToken.IDENT: FieldRule(
                            15,
                            align=Align.CENTER,
                            truncate=Truncate.MIDDLE,
                            auto_width=True,
                            min_width=6,
                            max_width=24,
                        ),
                    }
            ),
            time_fmt=(time_fmt or "%H:%M:%S.%f"),
        )
