"""The ready-made formats, selected by name (as a service would from configuration)."""

from __future__ import annotations

import sys

from loggerplusplus import formats, loggerplusplus


def main() -> None:
    for name in (
        "ShortFormat",
        "OpsFormat",
        "ClassicFormat",
        "MinimalFormat",
        "PlainFormat",
    ):
        loggerplusplus.remove()
        loggerplusplus.add(
            sink=sys.stderr, level="DEBUG", format=getattr(formats, name)()
        )
        loggerplusplus.bind(identifier=name).info("rendered with this format")


if __name__ == "__main__":
    main()
