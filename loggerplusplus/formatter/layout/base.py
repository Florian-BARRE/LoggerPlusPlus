# ====== Code Summary ======
# This module defines the `BaseLayout` class, which is responsible for formatting
# log records based on customizable templates. It supports both a legacy
# placeholder-based formatting system and a faster intermediate representation (IR)
# path with optional color schemes for terminal output. The class integrates with
# `FieldRule`, `TimeFormatter`, and color schemes to handle shaping, truncation,
# alignment, and coloring of log fields.

# ====== Standard Library Imports ======
from __future__ import annotations
import re

# ====== Local Project Imports ======
from .log_token import LogToken
from .rules import FieldRule, fit_text
from .base_time_formatter import TimeFormatter
from .utils.sizer import GlobalFieldSizer
from ..color.base import BaseColorScheme

# Type alias for intermediate representation items in compiled format
_IRItem = str | LogToken


class BaseLayout:
    """
    Provides a flexible logging layout system that formats log messages according
    to a user-defined template. Supports both legacy `str % mapping` formatting
    and a faster IR-based rendering path with optional ANSI color schemes.

    Attributes:
        raw_template (str): The original user-provided format string.
        rules (dict[LogToken, FieldRule]): Formatting rules for specific log tokens.
        placeholder_map (dict[LogToken, str]): Maps tokens to legacy-style placeholders.
        compiled_fmt (str): The compiled template with placeholders replaced.
        _time (TimeFormatter): Time formatter for date fields.
        _present (set[LogToken]): Set of tokens present in the compiled template.
        _ir (list[_IRItem]): Intermediate representation of the template for fast formatting.
        _lineno_present (bool): Whether line number tokens are present in the IR.
    """

    def __init__(
            self,
            template: str,
            rules: dict[LogToken, FieldRule] | None = None,
            time_fmt: str = "%H:%M:%S.%f",
    ) -> None:
        """
        Initialize a BaseLayout with the given template, field rules, and time format.

        Args:
            template (str): Format template with tokens (e.g., "{LEVEL} {MSG}").
            rules (dict[LogToken, FieldRule] | None): Optional formatting rules for tokens.
            time_fmt (str): Time format string for date formatting.
        """
        self.raw_template = template
        self.rules = rules or {}

        # Mapping between log tokens and legacy placeholder strings
        self.placeholder_map: dict[LogToken, str] = {
            LogToken.DATE: "%(DATE)s",
            LogToken.LEVEL: "%(LEVEL)s",
            LogToken.IDENT: "%(IDENT)s",
            LogToken.FILENAME: "%(FILENAME)s",
            LogToken.LINENO: "%(LINENO)s",
            LogToken.FUNCNAME: "%(FUNCNAME)s",
            LogToken.MODULE: "%(MODULE)s",
            LogToken.THREAD: "%(THREAD)d",
            LogToken.PROCESS: "%(PROCESS)d",
            LogToken.MSG: "%(MSG)s",
        }

        # Compile legacy template format and time formatter
        self.compiled_fmt = self._compile(self.raw_template)
        self._time = TimeFormatter(time_fmt)

        # Detect presence of tokens for legacy formatting path
        self._present: set[LogToken] = {
            tok for tok, ph in self.placeholder_map.items() if ph in self.compiled_fmt
        }

        # Build IR (Intermediate Representation) for fast assembly
        self._ir: list[_IRItem] = self._build_ir(self.raw_template)
        self._lineno_present: bool = LogToken.LINENO in self._ir

    def _compile(self, tpl: str) -> str:
        """
        Replace token placeholders in the template with legacy-style placeholders.

        Args:
            tpl (str): Input template string.

        Returns:
            str: Template with placeholders replaced by legacy-compatible format specifiers.
        """
        out = tpl
        for tok, ph in self.placeholder_map.items():
            out = out.replace("{" + tok.value + "}", ph)
        return out

    @staticmethod
    def _build_ir(tpl: str) -> list[_IRItem]:
        """
        Build an intermediate representation of the template for faster rendering.

        Args:
            tpl (str): Template string with tokens.

        Returns:
            list[_IRItem]: A list containing strings and `LogToken` objects in sequence.
        """
        parts: list[_IRItem] = []
        token_by_val = {t.value: t for t in LogToken.__members__.values()}
        last = 0

        # 1. Iterate through regex matches for tokens
        for m in re.finditer(r"\{([a-z]+)\}", tpl):
            if m.start() > last:
                parts.append(tpl[last:m.start()])  # literal text

            name = m.group(1)
            tok = token_by_val.get(name)
            if tok:
                parts.append(tok)
            else:
                # Keep unknown tokens as-is
                parts.append(tpl[m.start(): m.end()])
            last = m.end()

        # 2. Add remaining literal if present
        if last < len(tpl):
            parts.append(tpl[last:])
        return parts

    @staticmethod
    def _effective_width(tok: LogToken, val: str, rule: FieldRule) -> int:
        """
        Compute the effective width of a field based on rules and observed sizes.

        Args:
            tok (LogToken): The token being formatted.
            val (str): The raw string value of the token.
            rule (FieldRule): The rule specifying width and constraints.

        Returns:
            int: The effective field width.
        """
        w = rule.width
        if rule.auto_width:
            obs = GlobalFieldSizer.observe(tok, len(val))
            w = max(obs, rule.min_width)
            if rule.max_width is not None:
                w = min(w, rule.max_width)
        return w

    def _shape_value(self, tok: LogToken, raw: str, rule: FieldRule | None) -> str:
        """
        Shape and format a raw value according to the provided rule.

        Args:
            tok (LogToken): The token being shaped.
            raw (str): The raw value to format.
            rule (FieldRule | None): Formatting rule, if available.

        Returns:
            str: Shaped and formatted string value.
        """
        if not rule:
            return raw

        # Add extra width if reserving space for line number after filename
        extra = (
            1
            if (tok is LogToken.FILENAME and rule.reserve_lineno and self._lineno_present)
            else 0
        )

        eff = FieldRule(
            width=self._effective_width(tok, raw, rule) + extra,
            align=rule.align,
            truncate=rule.truncate,
            reserve_lineno=rule.reserve_lineno,
        )
        return fit_text(raw, eff)

    def format_fields(
            self,
            *,
            created: float,
            levelname: str,
            identifier: str,
            filename: str,
            lineno: int,
            func: str,
            module: str,
            thread: int,
            process: int,
            msg: str,
    ) -> tuple[str, dict[str, object]]:
        """
        Legacy path: Return compiled format string and mapping for `%` operator.

        Args:
            created (float): Log record creation time.
            levelname (str): Log level name.
            identifier (str): Log identifier.
            filename (str): Source filename.
            lineno (int): Line number.
            func (str): Function name.
            module (str): Module name.
            thread (int): Thread ID.
            process (int): Process ID.
            msg (str): Log message.

        Returns:
            tuple[str, dict[str, object]]: Compiled format string and mapping.
        """
        mapping: dict[str, object] = {}

        # 1. Fill mapping with only present tokens
        if LogToken.DATE in self._present:
            mapping["DATE"] = self._time.format(created)
        if LogToken.LEVEL in self._present:
            mapping["LEVEL"] = self._shape_value(
                LogToken.LEVEL, levelname, self.rules.get(LogToken.LEVEL)
            )
        if LogToken.IDENT in self._present:
            mapping["IDENT"] = self._shape_value(
                LogToken.IDENT, identifier, self.rules.get(LogToken.IDENT)
            )
        if LogToken.FILENAME in self._present:
            mapping["FILENAME"] = self._shape_value(
                LogToken.FILENAME, filename, self.rules.get(LogToken.FILENAME)
            )
        if LogToken.LINENO in self._present:
            mapping["LINENO"] = self._shape_value(
                LogToken.LINENO, str(lineno), self.rules.get(LogToken.LINENO)
            )
        if LogToken.FUNCNAME in self._present:
            mapping["FUNCNAME"] = self._shape_value(
                LogToken.FUNCNAME, func, self.rules.get(LogToken.FUNCNAME)
            )
        if LogToken.MODULE in self._present:
            mapping["MODULE"] = self._shape_value(
                LogToken.MODULE, module, self.rules.get(LogToken.MODULE)
            )
        if LogToken.THREAD in self._present:
            mapping["THREAD"] = thread
        if LogToken.PROCESS in self._present:
            mapping["PROCESS"] = process
        if LogToken.MSG in self._present:
            mapping["MSG"] = self._shape_value(
                LogToken.MSG, msg, self.rules.get(LogToken.MSG)
            )

        return self.compiled_fmt, mapping

    def format_fast(
            self,
            *,
            created: float,
            levelno: int,
            levelname: str,
            identifier: str,
            filename: str,
            lineno: int,
            func: str,
            module: str,
            thread: int,
            process: int,
            msg: str,
            scheme: BaseColorScheme | None,
            enable_token_color: bool,
            enable_level_color: bool,
            sep: str,
            reset: str,
    ) -> str:
        """
        Fast-assembly path: Use IR + inline shaping and optional colorization.

        Args:
            created (float): Log record creation time.
            levelno (int): Numeric log level.
            levelname (str): Log level name.
            identifier (str): Log identifier.
            filename (str): Source filename.
            lineno (int): Line number.
            func (str): Function name.
            module (str): Module name.
            thread (int): Thread ID.
            process (int): Process ID.
            msg (str): Log message.
            scheme (BaseColorScheme | None): Color scheme for token/level coloring.
            enable_token_color (bool): Whether to color individual tokens.
            enable_level_color (bool): Whether to color entire line based on log level.
            sep (str): Separator inserted between colored tokens.
            reset (str): Reset sequence for ANSI colors.

        Returns:
            str: The formatted log string.
        """
        has_color = bool(scheme and (enable_token_color or enable_level_color))

        # Ultra-fast path: no colors, no separator -> inline shaping only
        if not has_color and not sep:
            parts: list[str] = []
            rules = self.rules

            # 1. Iterate through IR and inline shape values if rules exist
            for it in self._ir:
                if isinstance(it, str):
                    parts.append(it)
                    continue
                if it is LogToken.DATE:
                    parts.append(self._time.format(created))
                elif it is LogToken.LEVEL:
                    r = rules.get(LogToken.LEVEL)
                    parts.append(
                        self._shape_value(LogToken.LEVEL, levelname, r) if r else levelname
                    )
                elif it is LogToken.IDENT:
                    r = rules.get(LogToken.IDENT)
                    parts.append(
                        self._shape_value(LogToken.IDENT, identifier, r)
                        if r
                        else identifier
                    )
                elif it is LogToken.FILENAME:
                    r = rules.get(LogToken.FILENAME)
                    parts.append(
                        self._shape_value(LogToken.FILENAME, filename, r)
                        if r
                        else filename
                    )
                elif it is LogToken.LINENO:
                    r = rules.get(LogToken.LINENO)
                    s = str(lineno)
                    parts.append(
                        self._shape_value(LogToken.LINENO, s, r) if r else s
                    )
                elif it is LogToken.FUNCNAME:
                    r = rules.get(LogToken.FUNCNAME)
                    parts.append(
                        self._shape_value(LogToken.FUNCNAME, func, r) if r else func
                    )
                elif it is LogToken.MODULE:
                    r = rules.get(LogToken.MODULE)
                    parts.append(
                        self._shape_value(LogToken.MODULE, module, r)
                        if r
                        else module
                    )
                elif it is LogToken.THREAD:
                    parts.append(str(thread))
                elif it is LogToken.PROCESS:
                    parts.append(str(process))
                elif it is LogToken.MSG:
                    r = rules.get(LogToken.MSG)
                    parts.append(
                        self._shape_value(LogToken.MSG, msg, r) if r else msg
                    )
            return "".join(parts)

        parts: list[str] = []
        if scheme and sep:
            parts.append(sep)

        # Token-level coloring
        if enable_token_color and scheme:
            rules = self.rules
            for it in self._ir:
                if isinstance(it, str):
                    parts.append(it)
                    continue

                # 1. Compute value inline
                if it is LogToken.DATE:
                    val = self._time.format(created)
                elif it is LogToken.LEVEL:
                    r = rules.get(LogToken.LEVEL)
                    val = (
                        self._shape_value(LogToken.LEVEL, levelname, r)
                        if r
                        else levelname
                    )
                elif it is LogToken.IDENT:
                    r = rules.get(LogToken.IDENT)
                    val = (
                        self._shape_value(LogToken.IDENT, identifier, r)
                        if r
                        else identifier
                    )
                elif it is LogToken.FILENAME:
                    r = rules.get(LogToken.FILENAME)
                    val = (
                        self._shape_value(LogToken.FILENAME, filename, r)
                        if r
                        else filename
                    )
                elif it is LogToken.LINENO:
                    r = rules.get(LogToken.LINENO)
                    s = str(lineno)
                    val = self._shape_value(LogToken.LINENO, s, r) if r else s
                elif it is LogToken.FUNCNAME:
                    r = rules.get(LogToken.FUNCNAME)
                    val = self._shape_value(LogToken.FUNCNAME, func, r) if r else func
                elif it is LogToken.MODULE:
                    r = rules.get(LogToken.MODULE)
                    val = self._shape_value(LogToken.MODULE, module, r) if r else module
                elif it is LogToken.THREAD:
                    val = str(thread)
                elif it is LogToken.PROCESS:
                    val = str(process)
                else:  # MSG
                    r = rules.get(LogToken.MSG)
                    val = self._shape_value(LogToken.MSG, msg, r) if r else msg

                # 2. Apply token-specific ANSI colors
                ansi = scheme.token_color_for_level(it, levelno)

                if ansi:
                    parts.append(ansi)
                    parts.append(val)
                    parts.append(reset)
                    if sep:
                        parts.append(sep)
                else:
                    parts.append(val)

            out = "".join(parts)
            if scheme and sep:
                out = out + reset
            return out

        # Whole-line coloring path (no token color, only level tint)
        rules = self.rules
        for it in self._ir:
            if isinstance(it, str):
                parts.append(it)
                continue
            if it is LogToken.DATE:
                parts.append(self._time.format(created))
            elif it is LogToken.LEVEL:
                r = rules.get(LogToken.LEVEL)
                parts.append(
                    self._shape_value(LogToken.LEVEL, levelname, r) if r else levelname
                )
            elif it is LogToken.IDENT:
                r = rules.get(LogToken.IDENT)
                parts.append(
                    self._shape_value(LogToken.IDENT, identifier, r)
                    if r
                    else identifier
                )
            elif it is LogToken.FILENAME:
                r = rules.get(LogToken.FILENAME)
                parts.append(
                    self._shape_value(LogToken.FILENAME, filename, r)
                    if r
                    else filename
                )
            elif it is LogToken.LINENO:
                r = rules.get(LogToken.LINENO)
                s = str(lineno)
                parts.append(self._shape_value(LogToken.LINENO, s, r) if r else s)
            elif it is LogToken.FUNCNAME:
                r = rules.get(LogToken.FUNCNAME)
                parts.append(
                    self._shape_value(LogToken.FUNCNAME, func, r) if r else func
                )
            elif it is LogToken.MODULE:
                r = rules.get(LogToken.MODULE)
                parts.append(
                    self._shape_value(LogToken.MODULE, module, r) if r else module
                )
            elif it is LogToken.THREAD:
                parts.append(str(thread))
            elif it is LogToken.PROCESS:
                parts.append(str(process))
            elif it is LogToken.MSG:
                r = rules.get(LogToken.MSG)
                parts.append(self._shape_value(LogToken.MSG, msg, r) if r else msg)

        out = "".join(parts)

        if scheme and sep:
            out = sep + out + reset
        if scheme and enable_level_color and not enable_token_color:
            lvl = scheme.level_color(levelno)
            if lvl:
                out = f"{lvl}{out}{reset}"
        return out
