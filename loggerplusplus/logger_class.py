# ====== Imports ======
# Internal project imports
from loggerplusplus.logger import Logger


# ====== LoggerClass ======
class LoggerClass:
    """
    A class that manages a Logger instance for logging purposes.

    If no logger is provided during initialization, a default Logger is created
    using the class name as its identifier.

    Attributes:
        logger (Logger): The logger instance used for logging operations.
    """

    def __init__(self, logger: Logger | None = None):
        """
        Initializes the LoggerClass with a Logger instance.

        Args:
            logger (Logger | None): An optional Logger instance. If None, a new
                Logger is created with the class name as its identifier.
        """
        # Initialize the logger. If none provided, create a default Logger
        # with the class name as the identifier and enable manager rules.
        self.logger: Logger = logger or Logger(
            identifier=self.__class__.__name__,
            follow_logger_manager_rules=True
        )
