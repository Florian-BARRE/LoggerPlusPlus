"""Structured NDJSON output for log pipelines (ELK / Loki / Datadog)."""

from __future__ import annotations

import sys

from loggerplusplus import add_json, logger, remove


def main() -> None:
    remove()
    add_json(sink=sys.stdout, level="DEBUG")
    logger.bind(identifier="API", user="bob").info("one JSON object per line")
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("errors carry a structured traceback")


if __name__ == "__main__":
    main()
