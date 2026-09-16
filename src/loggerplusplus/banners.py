# ====== Code Summary ======
# The `Banner` toolkit: factories that each return a `str -> str` transform, so a banner is just
# a transform you hand to any level method (`logger.info(text, transform=Banner.box())`). Three
# renderers ship: `figlet` (big ASCII art, via the OPTIONAL `pyfiglet` extra), `box` (zero-dep
# Unicode box — rehomes the ConfigPlusPlus header style natively) and `rule` (zero-dep separator
# line). `preset` bundles good defaults by name. pyfiglet is imported lazily and only when a
# figlet transform is actually CALLED, so importing this module never requires the extra.

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

__all__: list[str] = ["Banner"]


def _require_figlet() -> Any:
    """
    Import pyfiglet lazily, raising an actionable error when the extra is missing.

    Returns:
        Any: The `pyfiglet.Figlet` class.

    Raises:
        ImportError: When pyfiglet is not installed, with the exact install command.
    """
    try:
        from pyfiglet import Figlet  # optional extra, never a hard dependency
    except ImportError as exc:
        raise ImportError(
            "Banner.figlet requires pyfiglet. Install it with: pip install 'loggerplusplus[banners]'"
        ) from exc
    return Figlet


class Banner:
    """
    Factories that build banner transforms (each a `Callable[[str], str]`).

    Every method returns a transform suitable for the `transform=` keyword of any level method,
    or for direct use as a plain string function. Nothing here emits or prints — rendering and
    emission stay separate, so the same banner works through every sink.
    """

    @staticmethod
    def figlet(font: str = "standard") -> Callable[[str], str]:
        """
        Build a transform that renders text as big ASCII art via pyfiglet.

        Args:
            font (str): A pyfiglet font name (e.g. "standard", "slant", "big", "small").

        Returns:
            Callable[[str], str]: A transform; calling it requires the `banners` extra.
        """

        def _render(text: str) -> str:
            # Trailing newlines are re-added at emission time (raw mode); strip them here.
            figlet_cls = _require_figlet()
            return figlet_cls(font=font).renderText(text).rstrip("\n")

        return _render

    @staticmethod
    def box(
        *,
        align: str = "center",
        width: Optional[int] = None,
        double: bool = False,
    ) -> Callable[[str], str]:
        """
        Build a transform that frames text in a Unicode box.

        Args:
            align (str): "center", "left" or "right" alignment of each line.
            width (int | None): Inner width; defaults to the widest input line.
            double (bool): Use a double-line frame (╔═╗) instead of a single one (┌─┐).

        Returns:
            Callable[[str], str]: A zero-dependency transform.
        """

        def _render(text: str) -> str:
            # 1. Normalize to lines and resolve the inner width.
            lines: List[str] = text.splitlines() or [""]
            inner: int = (
                width if width is not None else max(len(line) for line in lines)
            )

            # 2. Pick the frame glyphs.
            if double:
                horizontal, top_l, top_r, bot_l, bot_r, vertical = (
                    "═",
                    "╔",
                    "╗",
                    "╚",
                    "╝",
                    "║",
                )
            else:
                horizontal, top_l, top_r, bot_l, bot_r, vertical = (
                    "─",
                    "┌",
                    "┐",
                    "└",
                    "┘",
                    "│",
                )

            # 3. Assemble the framed block.
            top: str = f"{top_l}{horizontal * (inner + 2)}{top_r}"
            bottom: str = f"{bot_l}{horizontal * (inner + 2)}{bot_r}"
            body: List[str] = []
            for line in lines:
                if align == "center":
                    content = line.center(inner)
                elif align == "right":
                    content = line.rjust(inner)
                else:
                    content = line.ljust(inner)
                body.append(f"{vertical} {content} {vertical}")
            return "\n".join([top, *body, bottom])

        return _render

    @staticmethod
    def rule(
        char: str = "─", width: int = 60, label: Optional[str] = None
    ) -> Callable[[str], str]:
        """
        Build a transform that renders a horizontal rule, centering the text as its label.

        Args:
            char (str): The fill character.
            width (int): Total line width.
            label (str | None): Fixed label; when None the message itself is used as the label.

        Returns:
            Callable[[str], str]: A zero-dependency transform.
        """

        def _render(text: str) -> str:
            # 1. A blank label yields a plain rule.
            base: str = label if label is not None else text
            if not base:
                return char * width

            # 2. Center the padded label within the rule, degrading gracefully when too wide.
            padded: str = f" {base} "
            if len(padded) >= width:
                return padded.strip()
            left: int = (width - len(padded)) // 2
            right: int = width - len(padded) - left
            return f"{char * left}{padded}{char * right}"

        return _render

    @staticmethod
    def preset(name: str) -> Callable[[str], str]:
        """
        Return a named, ready-made banner transform.

        Args:
            name (str): One of "title", "big", "small" (figlet fonts), "box", "double"
                (Unicode boxes) or "line" (a rule).

        Returns:
            Callable[[str], str]: The matching transform.

        Raises:
            ValueError: When the preset name is unknown.
        """
        presets: Dict[str, Callable[[str], str]] = {
            "title": Banner.figlet("standard"),
            "big": Banner.figlet("big"),
            "small": Banner.figlet("small"),
            "box": Banner.box(),
            "double": Banner.box(double=True),
            "line": Banner.rule(),
        }
        try:
            return presets[name]
        except KeyError:
            raise ValueError(
                f"unknown banner preset {name!r}; available: {sorted(presets)}"
            ) from None
