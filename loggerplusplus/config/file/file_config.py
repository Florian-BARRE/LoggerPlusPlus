# ====== Code Summary ======
# This module defines a configuration dataclass for file naming and routing in a logging subsystem.
# It encapsulates how log filenames are constructed (timestamp/daily/custom/none) and where they are routed
# (shared vs dedicated outputs), and provides a method to compute target file paths based on the config.

from __future__ import annotations

# ====== Standard Library Imports ======
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ====== Local Project Imports ======
from .file_enums import FileRouting, FileNaming


@dataclass(slots=True)
class FileConfig:
    """
    Configuration for file naming and routing behavior used by the logging system.

    Attributes:
        log_dir (Path): Directory where logs are stored.
        routing (FileRouting): Routing strategy (shared, dedicated, or both).
        naming (FileNaming): File naming strategy (timestamp, daily, custom, or none).
        max_bytes (int | None): Max file size before rotation (None disables size-based rotation).
        backup_count (int): Number of backup files to retain on rotation.
        encoding (str): Encoding used for log files.
        timestamp_format (str): `strftime` format used for time-based naming.
        shared_pattern (str): Format pattern for shared log filename.
        dedicated_pattern (str): Format pattern for dedicated log filename.
        sep (str): Separator placed between components (e.g., identifier and timestamp).
    """

    # NOTE: Defaults match common, sensible logging conventions.
    log_dir: Path = Path("logs")
    routing: FileRouting = FileRouting.SHARED_ONLY
    naming: FileNaming = FileNaming.TIMESTAMP
    max_bytes: int | None = None
    backup_count: int = 5
    encoding: str = "utf-8"
    timestamp_format: str = "%Y%m%d-%H%M%S"
    shared_pattern: str = "{identifier}{sep}{time}.log"
    dedicated_pattern: str = "{logger}{sep}{time}.log"
    sep: str = "-"

    # -------------------- Private Methods -------------------- #
    def _build_time(self) -> str:
        """
        Build the time component string according to the configured naming strategy.

        Returns:
            str: The formatted timestamp (may be an empty string when naming is NONE).

        Notes:
            - If `naming` is DAILY, use a day-granular format. If the default timestamp
              format is in use, collapse to YYYYMMDD for clearer daily grouping.
        """
        # 1. Short-circuit when naming is disabled
        if self.naming == FileNaming.NONE:
            return ""

        # 2. Select the appropriate strftime format based on naming mode
        if self.naming == FileNaming.DAILY:
            # Retain custom user format if provided; otherwise collapse to YYYYMMDD for daily granularity
            fmt = (
                "%Y%m%d"
                if self.timestamp_format == "%Y%m%d-%H%M%S"
                else self.timestamp_format
            )
        else:
            fmt = self.timestamp_format

        # 3. Render the current time using the selected format
        return datetime.now().strftime(fmt)

    def _render(self, pattern: str, identifier: str, logger: str, t: str) -> str:
        """
        Render a filename from the given pattern and inputs.

        Args:
            pattern (str): Filename pattern including format fields.
            identifier (str): High-level identifier (e.g., application or tenant).
            logger (str): Logger name or context.
            t (str): Pre-built time string (may be empty).

        Returns:
            str: The formatted filename (without directory).
        """
        # 1. Determine whether to apply the separator based on presence of time
        sep = self.sep if t else ""

        # 2. Format the pattern with the provided fields
        return pattern.format(
            identifier=identifier,
            logger=logger,
            time=t,
            sep=sep,
        )

    # --------------------- Public Methods -------------------- #
    def get_file_targets(self, identifier: str, logger_name: str) -> list[Path]:
        """
        Compute the target log file paths based on routing and naming configuration.

        Args:
            identifier (str): High-level identifier for shared logs (e.g., service name).
            logger_name (str): Specific logger name for dedicated logs.

        Returns:
            list[Path]: One or two absolute/relative Paths (depending on routing).

        Behavior:
            - Ensures `log_dir` exists.
            - When naming is NONE, filenames are `{identifier}.log` or `{logger_name}.log`.
            - Otherwise, filenames are rendered using the configured patterns and timestamp.
        """
        # 1. Ensure the log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 2. Build the time token according to naming rules
        t: str = self._build_time()

        # 3. Compute the shared and dedicated filenames based on naming strategy
        if self.naming != FileNaming.NONE:
            shared_name: str = self._render(
                self.shared_pattern, identifier, logger_name, t
            )
            dedicated_name: str = self._render(
                self.dedicated_pattern, identifier, logger_name, t
            )
        else:
            # No time in filenames when naming is disabled
            shared_name = f"{identifier}.log"
            dedicated_name = f"{logger_name}.log"

        # 4. Route to shared/dedicated targets according to the routing configuration
        targets: list[Path] = []
        if self.routing in (FileRouting.SHARED_ONLY, FileRouting.BOTH):
            targets.append(self.log_dir / shared_name)
        if self.routing in (FileRouting.DEDICATED_ONLY, FileRouting.BOTH):
            targets.append(self.log_dir / dedicated_name)

        # 5. Return the list of target paths
        return targets
