"""
This module defines a helper function for configuring the backend's logging.
"""

import logging
import sys
import os
from pathlib import Path
from tqdm.auto import tqdm


class TqdmStreamHandler(logging.StreamHandler):
    """
    Handler for displaying `tqdm` progress bars with python logging
    """
    def __init__(self) -> None:
        super().__init__(sys.stdout)

    def emit(self, record) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg, file=self.stream)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """
    Configure the root logger to include custom formatting and handlers
    """
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
    level = getattr(logging, LOGGING_LEVEL, logging.INFO)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "{asctime} -- {levelname} -- ({name}:{funcName}) || {message}",
        style="{",
        datefmt="%H:%M:%S[%z]"
    )

    # Create and add handlers
    log_dir = Path.home() / ".mirumoji_logs"
    log_dir.mkdir(exist_ok=True)
    log_file = str((log_dir / "backend.log").resolve())
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = TqdmStreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
