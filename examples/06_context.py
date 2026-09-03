"""Correlation context: tag every record in a request with a shared id."""

from __future__ import annotations

import sys

from loggerplusplus import add, bind_context, logger, new_id, remove


def main() -> None:
    remove()
    add(
        sink=sys.stderr,
        level="DEBUG",
        format="[{extra[request_id]}] [{identifier:<auto}] {message}",
        filter=lambda record: "request_id" in record["extra"],
    )
    with bind_context(request_id=new_id(prefix="req-")):
        logger.bind(identifier="HANDLER").info("received")
        logger.bind(identifier="DB").debug("query executed")  # same request_id


if __name__ == "__main__":
    main()
