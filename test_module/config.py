import sys
from loggerplusplus import loggerplusplus
from loggerplusplus.formats import ClassicFormat

def configure_logging():
    """Configure global logger sinks (console + file)."""
    loggerplusplus.remove()  # avoid double logging

    loggerplusplus.add(
        sink=sys.stderr,
        level="DEBUG",
        format=ClassicFormat()
    )

    # add(
    #     sink="test_module.log",
    #     level="DEBUG",
    #     colorize=False,
    #     format=(
    #         "{time:YYYY-MM-DD HH:mm:ss} | {level.name:<8} | "
    #         "[{identifier:<auto[18~middle]}] | {name}:{line} | {message}"
    #     ),
    # )
