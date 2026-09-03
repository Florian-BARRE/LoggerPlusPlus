"""One-call setup(), plus bridging the standard library logging into loguru."""

from __future__ import annotations

import logging

from loggerplusplus import setup


def main() -> None:
    # One call: console sink with a named format + route stdlib logging through loguru.
    setup(level="DEBUG", format="OpsFormat", intercept=True)

    # A third-party library that uses the standard `logging` now lands in our format.
    logging.getLogger("third_party.lib").warning("stdlib record routed through loguru")


if __name__ == "__main__":
    main()
