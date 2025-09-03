# ====== Code Summary ======
# This module defines `SafeRotatingFileHandler`, a safer subclass of
# `RotatingFileHandler` designed to handle file rollover reliably on Windows.
# It uses `os.replace` for atomic moves, and falls back to copy+truncate if the
# file is locked by antivirus or indexers, avoiding stalls or crashes.

# ====== Standard Library Imports ======
import os
from logging.handlers import RotatingFileHandler


class SafeRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler with Windows-friendly rotation strategy.

    Strategy:
        1. Close stream (handled by base in doRollover).
        2. Try fast path: `os.replace(source, dest)` for atomic replacement.
        3. On PermissionError: copy source -> dest, then truncate source to zero.
           (No sleeps, avoids long stalls with antivirus/indexer.)
    """

    def rotate(self, source: str, dest: str) -> None:  # type: ignore[override]
        """
        Perform file rotation, with fallback for locked files on Windows.

        Args:
            source (str): Path of the current log file.
            dest (str): Path of the rotated backup file.
        """
        # 1. Remove destination if present (best-effort)
        try:
            if os.path.exists(dest):
                os.remove(dest)
        except Exception:
            pass

        # 2. Fast path: atomic replace
        try:
            os.replace(source, dest)
            return
        except PermissionError:
            pass

        # 3. Fallback: copy + truncate (no waiting)
        try:
            # Copy bytes in chunks
            with open(source, "rb") as sf, open(dest, "wb") as df:
                while True:
                    chunk = sf.read(1024 * 1024)
                    if not chunk:
                        break
                    df.write(chunk)

            # Truncate source by recreating an empty file
            with open(
                    source,
                    "w",
                    encoding=getattr(self, "encoding", "utf-8"),
                    errors=getattr(self, "errors", "replace"),
            ) as sfw:
                sfw.truncate(0)
        except Exception:
            # Give up silently to avoid crashing; next rollover may succeed
            return

    def doRollover(self) -> None:
        """
        Ensure stream is closed before rotating, then defer to base implementation.
        """
        if self.stream:
            try:
                self.stream.close()
            finally:
                self.stream = None
        super().doRollover()
