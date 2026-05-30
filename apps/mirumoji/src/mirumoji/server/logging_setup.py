"""
This module defines helpers for configuring the backend's logging
"""

import logging
import sys

from tqdm.auto import tqdm

from .constants import HOST_LOG_PATH, LOGGING_LEVEL


class TqdmStreamHandler(logging.StreamHandler):
    """
    Handler for displaying `tqdm` progress bars with python logging
    """

    def __init__(self) -> None:
        super().__init__(sys.stdout)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg, file=self.stream)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """
    Configures the `mirumoji` logger to include custom formatters and handlers.
    In addition, creates the logging directory if it doesn't exist
    """
    level = getattr(logging, LOGGING_LEVEL, logging.INFO)

    # Get the logger and set its level
    logger = logging.getLogger("mirumoji")
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        "{asctime} -- {levelname} -- ({name}:{funcName}) || {message}",
        style="{",
        datefmt="%H:%M:%S[%z]",
    )

    # Create DIR and add handlers
    HOST_LOG_PATH.mkdir(parents=True, exist_ok=True)
    log_file = str((HOST_LOG_PATH / "backend.log").resolve())
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = TqdmStreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
