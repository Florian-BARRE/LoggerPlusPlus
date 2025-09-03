# ====== Code Summary ======
# This module defines the `ClassicLayout`, a concrete implementation of BaseLayout.
# It provides a traditional log format including time, level, identifier,
# source filename/line number, and the message, with sensible field rules.

from __future__ import annotations

# ====== Local Project Imports ======
from ..base import BaseLayout
from ..rules import FieldRule, Align, Truncate
from ..log_token import LogToken


class ClassicLayout(BaseLayout):
    """
    A classic log layout: `time, level, ident, filename:lineno, message`.

    Default Template:
        "{date} [ {level} ] [ {id} ] {file}:{line} | {msg}"

    Notes:
        - Provides default field rules for ident, filename, level, and lineno.
        - Falls back to standard timestamp format if not provided.
    """

    def __init__(
            self,
            template: str | None = None,
            rules: dict[LogToken, FieldRule] | None = None,
            time_fmt: str | None = None,
    ) -> None:
        """
        Initialize the ClassicLayout with optional overrides.

        Args:
            template (str | None): Custom log line template.
            rules (dict[LogToken, FieldRule] | None): Custom field formatting rules.
            time_fmt (str | None): Custom strftime format for date/time fields.
        """
        super().__init__(
            template=(
                    template
                    or f"{LogToken.DATE} [ {LogToken.LEVEL} ] [ {LogToken.IDENT} ] "
                       f"{LogToken.FILENAME}:{LogToken.LINENO} | {LogToken.MSG}"
            ),
            rules=(
                    rules
                    or {
                        LogToken.IDENT: FieldRule(
                            12,
                            align=Align.CENTER,
                            truncate=Truncate.MIDDLE,
                            auto_width=True,
                            min_width=6,
                            max_width=32,
                        ),
                        LogToken.FILENAME: FieldRule(
                            24,
                            align=Align.LEFT,
                            truncate=Truncate.MIDDLE,
                            reserve_lineno=True,
                        ),
                        LogToken.LEVEL: FieldRule(
                            9,
                            align=Align.CENTER,
                            truncate=Truncate.TAIL,
                        ),
                        LogToken.LINENO: FieldRule(
                            3,
                            align=Align.LEFT,
                            truncate=Truncate.TAIL,
                        ),
                    }
            ),
            time_fmt=(time_fmt or "%H:%M:%S.%f"),
        )
