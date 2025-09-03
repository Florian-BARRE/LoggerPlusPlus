# ====== Code Summary ======
# A custom logging.Formatter that assembles colored, token-aware log lines using a pluggable
# layout and color scheme. It supports per-token/static/dynamic coloring, optional separators,
# and integrates with a broader formatting configuration object.

from __future__ import annotations

# ====== Standard Library Imports ======
import logging

# ====== Local Project Imports ======
from .layout.base import BaseLayout
from .color.base import BaseColorScheme
from .layout.log_token import LogToken
from ..config.format import FormatConfig, SeparatorMode


class LoggerPlusPlusFormatter(logging.Formatter):
    """
    Token-aware, color-capable log formatter.

    This formatter delegates token ordering/formatting to a `BaseLayout` implementation,
    and uses a `BaseColorScheme` (if provided) to colorize either specific tokens or the
    entire line by log level. Behavior is further customized by a `FormatConfig`.

    Args:
        layout (BaseLayout): Concrete layout that provides placeholders and compiled format.
        scheme (BaseColorScheme | None): Optional color scheme for tokens and levels.
        enable_level_color (bool): Apply level color to the entire message when token color is disabled.
        enable_token_color (bool): Apply per-token colorization when available.
        cfg (FormatConfig | None): Optional configuration that controls rules, overrides,
            separators, and performance toggles.

    Notes:
        - The `FormatConfig.separators` controls whether a separator ANSI code is prefixed/suffixed.
        - When both token and level colors are enabled, token colors take precedence for individual tokens.
    """

    # ------------------------ Initialization ------------------------ #
    def __init__(
            self,
            layout: BaseLayout,
            scheme: BaseColorScheme | None = None,
            enable_level_color: bool = True,
            enable_token_color: bool = True,
            cfg: FormatConfig | None = None,
    ) -> None:
        # 1. Initialize base formatter with a simple message template (layout drives content)
        super().__init__(fmt="%(message)s")

        # 2. Store core collaborators and configuration
        self._layout: BaseLayout = layout
        self._scheme: BaseColorScheme | None = scheme
        self._enable_level_color: bool = enable_level_color
        self._enable_token_color: bool = enable_token_color
        self._cfg: FormatConfig | None = cfg

        # 3. Derive fast-assembly flag and ANSI reset from scheme
        self._fast: bool = bool(getattr(cfg, "enable_fast_assembly", False)) if cfg else False
        self._reset: str = self._scheme.reset() if self._scheme else ""

        # 4. Determine separator ANSI sequence according to configuration and theme
        self._sep: str = ""
        if self._scheme and self._enable_token_color and self._cfg:
            if self._cfg.separators.mode == SeparatorMode.STATIC and self._cfg.separators.ansi:
                self._sep = self._cfg.separators.ansi
            elif self._cfg.separators.mode == SeparatorMode.THEME:
                self._sep = self._scheme.separator_default()

        # 5. Cache the compiled format string from the layout for fast formatting
        self._compiled_fmt: str = self._layout.compiled_fmt

    # ---------------------- Private Helpers ---------------------- #
    def _static_color(self, tok: LogToken) -> str:
        """
        Compute a static color ANSI sequence for a token (level-agnostic).

        Args:
            tok (LogToken): The token whose color is requested.

        Returns:
            str: ANSI sequence to start color for the token, or empty string if none.

        Steps:
            1. Validate configuration and token-color enablement.
            2. Respect token disablement and per-token rule disabling.
            3. Check overrides and rule-provided color.
            4. Fallback to scheme-provided token color.
        """
        # 1. Validate configuration and token-color enablement
        if not (self._cfg and self._enable_token_color):
            return ""

        # 2. Respect token disablement and per-token rule disabling
        if tok in self._cfg.token_color_disabled:
            return ""
        rule = self._cfg.rules.get(tok) if self._cfg.rules else None
        if rule and getattr(rule, "disable_color", False):
            return ""

        # 3. Check overrides and rule-provided color
        if tok in self._cfg.token_color_overrides:
            return self._cfg.token_color_overrides[tok]
        if rule and hasattr(rule, "color_ansi"):
            color_ansi = getattr(rule, "color_ansi")
            if isinstance(color_ansi, str):
                return color_ansi

        # 4. Fallback to scheme-provided token color
        if self._scheme:
            return self._scheme.token_color(tok)
        return ""

    def _dynamic_color(self, tok: LogToken, levelno: int) -> str:
        """
        Compute a dynamic color ANSI sequence for a token (level-aware).

        Args:
            tok (LogToken): The token whose color is requested.
            levelno (int): The numeric log level associated with the record.

        Returns:
            str: ANSI sequence to start color for the token, or empty string if none.

        Steps:
            1. Validate configuration and token-color enablement.
            2. Respect token disablement and per-token rule disabling.
            3. Check overrides and rule-provided color.
            4. Fallback to scheme-provided token color for the specific level.
        """
        # 1. Validate configuration and token-color enablement
        if not (self._cfg and self._enable_token_color):
            return ""

        # 2. Respect token disablement and per-token rule disabling
        if tok in self._cfg.token_color_disabled:
            return ""
        rule = self._cfg.rules.get(tok) if self._cfg.rules else None
        if rule and getattr(rule, "disable_color", False):
            return ""

        # 3. Check overrides and rule-provided color
        if tok in self._cfg.token_color_overrides:
            return self._cfg.token_color_overrides[tok]
        if rule and hasattr(rule, "color_ansi"):
            color_ansi = getattr(rule, "color_ansi")
            if isinstance(color_ansi, str):
                return color_ansi

        # 4. Fallback to scheme-provided token color for this level
        if self._scheme:
            return self._scheme.token_color_for_level(tok, levelno)
        return ""

    # ----------------------- Public Methods ----------------------- #
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record into a string using the configured layout and color scheme.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The fully formatted, optionally colorized log line.

        Steps:
            1. Ask the layout to produce the printf-style template and value mapping.
            2. Optionally wrap the entire format with a separator and reset.
            3. For a fixed token order, inject token-specific ANSI sequences into the template.
            4. Render the message using printf-style substitution.
            5. If token color is disabled but level color is enabled, colorize the whole line.
        """
        # 1. Ask the layout to produce the printf-style template and value mapping.
        fmt, mapping = self._layout.format_fields(
            created=record.created,
            levelname=record.levelname,
            identifier=getattr(record, "identifier", record.name),
            filename=record.filename,
            lineno=record.lineno,
            func=record.funcName,
            module=record.module,
            thread=record.thread,
            process=record.process,
            msg=record.getMessage(),
        )

        # 2. Optionally wrap the entire format with a separator and reset.
        out_fmt: str = self._compiled_fmt
        if self._sep:
            out_fmt = f"{self._sep}{out_fmt}{self._reset}"

        # 3. Inject token-specific ANSI sequences into the template in a stable order.
        order: tuple[LogToken, ...] = (
            LogToken.DATE,
            LogToken.LEVEL,
            LogToken.IDENT,
            LogToken.FILENAME,
            LogToken.LINENO,
            LogToken.FUNCNAME,
            LogToken.MODULE,
            LogToken.THREAD,
            LogToken.PROCESS,
            LogToken.MSG,
        )
        for tok in order:
            ph = self._layout.placeholder_map.get(tok)  # expects dict[LogToken, str]
            if not ph or ph not in out_fmt:
                continue
            ansi = (
                self._dynamic_color(tok, record.levelno)
                if tok in (LogToken.LEVEL, LogToken.MSG)
                else self._static_color(tok)
            )
            if ansi:
                # When separators are active, place reset then the separator before continuing the format.
                tail = f"{self._reset}{self._sep}" if self._sep else self._reset
                out_fmt = out_fmt.replace(ph, f"{ansi}{ph}{tail}")

        # 4. Render the message using printf-style substitution.
        out: str = out_fmt % mapping  # mapping is expected to be dict[str, object]

        # 5. If token color is disabled but level color is enabled, colorize the whole line.
        if self._scheme and self._enable_level_color and not self._enable_token_color:
            lvl = self._scheme.level_color(record.levelno)
            if lvl:
                out = f"{lvl}{out}{self._reset}"

        return out
