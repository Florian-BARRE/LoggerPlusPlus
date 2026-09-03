"""Quickstart: configure a sink and log with a self-aligning identifier column."""

from __future__ import annotations

import sys

from loggerplusplus import add, logger, remove


def main() -> None:
    remove()  # drop loguru's default handler first
    add(
        sink=sys.stderr,
        level="DEBUG",
        format="<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | "
        "[<blue>{identifier:<auto}</blue>] | "
        "<level>{message}</level>",
    )
    logger.bind(identifier="MAIN").info("hello")
    logger.bind(identifier="LONG-WORKER").warning(
        "the identifier column grows and stays aligned"
    )
    logger.bind(identifier="DB").debug("shorter ids are padded to the widest seen")


if __name__ == "__main__":
    main()
