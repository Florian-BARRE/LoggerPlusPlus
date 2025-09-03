# ====== Code Summary ======
# This module defines the `DetailedLayout`, a concrete implementation of BaseLayout.
# It produces a verbose log format with timestamp, level, identifier, module/function,
# filename/line, thread, process, and message, with sensible field rules.

from __future__ import annotations

# ====== Local Project Imports ======
from ..base import BaseLayout
from ..rules import FieldRule, Align, Truncate
from ..log_token import LogToken


class DetailedLayout(BaseLayout):
    """
    A detailed log layout:
    `time, level, ident, module.func, filename:lineno, thread, process, message`.

    Default Template:
        "{date} [ {level} ] [ {id} ] {module}.{func} | {file}:{line} | T{thread} P{process} | {msg}"

    Notes:
        - Provides default field rules for ident, level, module, funcname, filename, lineno,
          thread, and process.
        - Falls back to standard timestamp format if not provided.
    """

    def __init__(
            self,
            template: str | None = None,
            rules: dict[LogToken, FieldRule] | None = None,
            time_fmt: str | None = None,
    ) -> None:
        """
        Initialize the DetailedLayout with optional overrides.

        Args:
            template (str | None): Custom log line template.
            rules (dict[LogToken, FieldRule] | None): Custom field formatting rules.
            time_fmt (str | None): Custom strftime format for date/time fields.
        """
        super().__init__(
            template=(
                    template
                    or f"{LogToken.DATE} [ {LogToken.LEVEL} ] [ {LogToken.IDENT} ] "
                       f"{LogToken.MODULE}.{LogToken.FUNCNAME} | "
                       f"{LogToken.FILENAME}:{LogToken.LINENO} | "
                       f"T{LogToken.THREAD} P{LogToken.PROCESS} | {LogToken.MSG}"
            ),
            rules=(
                    rules
                    or {
                        LogToken.IDENT: FieldRule(
                            16,
                            align=Align.CENTER,
                            truncate=Truncate.MIDDLE,
                            auto_width=True,
                            min_width=8,
                            max_width=40,
                        ),
                        LogToken.LEVEL: FieldRule(
                            9,
                            align=Align.CENTER,
                            truncate=Truncate.TAIL,
                        ),
                        LogToken.MODULE: FieldRule(
                            14,
                            align=Align.LEFT,
                            truncate=Truncate.MIDDLE,
                        ),
                        LogToken.FUNCNAME: FieldRule(
                            16,
                            align=Align.LEFT,
                            truncate=Truncate.MIDDLE,
                        ),
                        LogToken.FILENAME: FieldRule(
                            24,
                            align=Align.LEFT,
                            truncate=Truncate.MIDDLE,
                            reserve_lineno=True,
                        ),
                        LogToken.LINENO: FieldRule(
                            3,
                            align=Align.LEFT,
                            truncate=Truncate.TAIL,
                        ),
                        LogToken.THREAD: FieldRule(
                            5,
                            align=Align.RIGHT,
                            truncate=Truncate.HEAD,
                        ),
                        LogToken.PROCESS: FieldRule(
                            5,
                            align=Align.RIGHT,
                            truncate=Truncate.HEAD,
                        ),
                    }
            ),
            time_fmt=(time_fmt or "%H:%M:%S.%f"),
        )
