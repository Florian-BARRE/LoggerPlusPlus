# ====== Code Summary ======
# This module defines `SafeStreamHandler`, a custom logging stream handler
# that gracefully handles `UnicodeEncodeError` by re-encoding messages with
# replacement characters, ensuring log output remains stable.

# ====== Standard Library Imports ======
import logging


class SafeStreamHandler(logging.StreamHandler):
    """
    Stream handler resilient to UnicodeEncodeError by replacing invalid characters.

    Falls back to re-encoding messages using the stream's encoding with errors="replace".
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a logging record, handling UnicodeEncodeError gracefully.

        Args:
            record (logging.LogRecord): The log record to emit.
        """
        try:
            # 1. Attempt normal emission
            super().emit(record)
        except UnicodeEncodeError:
            msg = self.format(record)
            stream = self.stream

            if hasattr(stream, "buffer"):
                # 2. Re-encode using stream's encoding, replacing invalid chars
                data = (msg + self.terminator).encode(
                    getattr(stream, "encoding", "utf-8"), errors="replace"
                )
                try:
                    stream.buffer.write(data)
                except Exception:
                    pass
                try:
                    stream.flush()
                except Exception:
                    pass
            else:
                # 3. Fallback: write text directly with replacement
                try:
                    stream.write(msg + self.terminator)
                    stream.flush()
                except Exception:
                    pass
