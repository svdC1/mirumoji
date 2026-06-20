"""
Centralised logging configuration shared by the server, launcher CLI, GUI, and
Modal jobs

info: One Setup
    - `setup_logging` configures the `mirumoji` logger with a rotating file
      handler and / or a `Rich` console handler

    - The file format is clean and structured for later reading, while the
      console renders through `Rich`

    - The console handler coordinates with `tqdm` so the live progress bars
      rendered by file transfers / transcription are never broken by a log line
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme
from tqdm.auto import tqdm

from .paths import HOST_LOG_PATH

_LOGGER_NAME = "mirumoji"
"""
The root logger name every `mirumoji.*` module logs under
"""

_MANAGED_FLAG = "_mirumoji_managed"
"""
Attribute stamped on handlers this module attaches, so repeated `setup_logging`
calls only ever clear their own handlers and never third-party ones
"""

_FILE_FORMAT = "{asctime} | {levelname:<8} | {name}:{funcName} | {message}"
_FILE_DATEFMT = "%Y-%m-%d %H:%M:%S%z"
_CONSOLE_FORMAT = "{subsys}  {message}"

_MAX_BYTES = 5_000_000
_BACKUP_COUNT = 3


class MirumojiHighlighter(RegexHighlighter):
    """
    Custom `Rich` highlighter for mirumoji's console logging messages
    """

    base_style = "highlighter."

    # Patterns Apply In Order + Later Matches Win On Overlap, So Broad Groups
    # (keywords, numbers) Come First + Structural Tokens (module, uuid, path,
    # url) Come Last - This Stops A Number From Bleeding Its Colour Into The
    # Digits Of A Path, URL, Or UUID That Contains It
    highlights = [  # noqa: RUF012
        # Lifecycle | Success Keywords (case-insensitive)
        r"\b(?P<ok>(?i:succeeded|success|started|ready|complete[d]?|saved))\b",
        # Failure | Cancellation Keywords
        r"\b(?P<bad>(?i:failed|failure|error|aborted|cancell?ed))\b",
        # Degraded | Retry Keywords
        r"\b(?P<warn>(?i:retry|retrying|fallback|skipped|missing))\b",
        # Numbers + Optional Size | Time | Rate Unit
        (
            r"(?P<number>(?<![\w.])-?\d+(?:\.\d+)?"
            r"(?:\s?(?:[KMGT]i?B|ms|s|m|h|fps|%|x))?\b)"
        ),
        # Dotted Sub-Package Names (`mirumoji.server.jobs`, `server.jobs`, ...)
        r"(?P<module>(?:mirumoji|server|launcher|cli|gui)(?:\.[a-z_]+)+)",
        # Profile | Job | File UUIDs
        (
            r"(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
        ),
        # Windows + POSIX Filesystem Paths
        r"(?P<path>(?:[A-Za-z]:\\|\\\\|/)[^\s'\"`|]+)",
        # URLs + Connection URIs (http, https, ws, sqlite+aiosqlite, ...)
        r"(?P<url>[a-zA-Z][\w+.-]*://[^\s'\"`]+)",
    ]


MIRUMOJI_LOGGING_THEME = Theme(
    {
        "accent": "#E2533B",
        "accent.soft": "#F08A6E",
        "info": "#5E83A4",
        "success": "#8AA06A",
        "danger": "bold #C8503D",
        "warning": "#D9A441",
        "muted": "#7E7567",
        "heading": "bold #F4EEE3",
        "ink": "#F4EEE3",
        # Highlighter Group Mappings
        # Semantic Keywords - Mirror The Level Palette
        "highlighter.ok": "#8AA06A",  # success green
        "highlighter.bad": "bold #C8503D",  # danger red
        "highlighter.warn": "#D9A441",  # warning amber
        # Data Tokens - Distinct From The Level Palette
        "highlighter.number": "#C99A57",  # soft gold
        "highlighter.uuid": "#F08A6E",  # accent.soft coral
        "highlighter.path": "#5E83A4",  # info blue
        "highlighter.url": "underline #5E83A4",  # info blue, underlined
        "highlighter.module": "#7E7567",  # muted - subsystem context
    }
)
"""
Defines the `Rich` theme for mirumoji's console logging messages mimicking the
frontend's `Sumi & Shu` design
"""


class _TqdmRichHandler(RichHandler):
    """
    `RichHandler` that clears any active `tqdm` progress bars while it writes

    info: Additional Information
        - Wraps each emit in `tqdm.external_write_mode` so that a log line
          removes the live bars, prints, then lets `tqdm` redraw them

        - This way, the byte-progress bars rendered by file saves, Modal
          transfers, or the third-party model-downloads are never broken by
          logging output

        - With no bar active it is a cheap no-op
    """

    def emit(self, record: logging.LogRecord) -> None:
        with tqdm.external_write_mode():
            super().emit(record)

    def get_level_text(self, record: logging.LogRecord) -> Text:
        """
        Override `Rich` log level output to match the mirumoji's theme colors
        """

        level_name = record.levelname

        if level_name == "INFO":
            return Text().from_markup(f"[info]{level_name}[/]:    ")
        elif level_name == "WARNING":
            return Text.from_markup(f"[warning]{level_name}[/]:    ")
        elif level_name in ("ERROR", "CRITICAL"):
            return Text.from_markup(f"[danger]{level_name}[/]:    ")
        elif level_name == "DEBUG":
            return Text.from_markup(f"[muted]{level_name}[/]:    ")

        # Fallback For Custom Levels
        return Text.from_markup(f"[ink]{level_name}[/]:")


class _SubsysFilter(logging.Filter):
    """
    Adds a `subsys` attribute to each record for the console format

    The `mirumoji.` prefix is dropped so that the console shows a compact
    subsystem tag (`server.jobs`, `launcher.cli.main`, ...) for the `module`
    highlighter group to colour. The file keeps the full logger
    name
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.subsys = record.name.removeprefix("mirumoji.")
        return True


def _resolve_level(level: str | int | None) -> int:
    """
    Resolves a logging level from an explicit value or the environment

    Args:
        level (str | int | None): An explicit level name / number, or `None` to
            read `MIRUMOJI_LOGGING_LEVEL`, defaulting to `INFO`

    Returns:
        The numeric logging level
    """
    if isinstance(level, int):
        return level
    name = (
        level
        if isinstance(level, str)
        else os.environ.get("MIRUMOJI_LOGGING_LEVEL", "INFO")
    )
    return getattr(logging, name.upper(), logging.INFO)


def _build_file_handler(log_file: str) -> RotatingFileHandler:
    """
    Builds the rotating file handler under `HOST_LOG_PATH`

    Args:
        log_file (str): The log file name to create under `HOST_LOG_PATH`

    Returns:
        A configured `RotatingFileHandler` stamped as managed
    """
    HOST_LOG_PATH.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        str((HOST_LOG_PATH / log_file).resolve()),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(_FILE_FORMAT, style="{", datefmt=_FILE_DATEFMT)
    )
    setattr(handler, _MANAGED_FLAG, True)
    return handler


def _build_console_handler() -> _TqdmRichHandler:
    """
    Builds the `tqdm`-aware `Rich` console handler

    Returns:
        A configured `_TqdmRichHandler` stamped as managed
    """
    handler = _TqdmRichHandler(
        console=Console(theme=MIRUMOJI_LOGGING_THEME),
        show_time=False,
        show_level=True,
        show_path=False,
        markup=False,
        rich_tracebacks=True,
        highlighter=MirumojiHighlighter(),
    )
    handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT, style="{"))
    handler.addFilter(_SubsysFilter())
    setattr(handler, _MANAGED_FLAG, True)
    return handler


def _clear_managed(logger: logging.Logger) -> None:
    """
    Removes and closes every handler that this module previously attached to
    `logger`

    Args:
        logger (logging.Logger): The logger to clear managed handlers from
    """
    for handler in logger.handlers[:]:
        if getattr(handler, _MANAGED_FLAG, False):
            logger.removeHandler(handler)
            handler.close()


def setup_logging(
    *,
    log_file: str | None = "backend.log",
    console: bool = True,
    level: str | int | None = None,
    capture_root: bool = False,
) -> None:
    """
    Configures the `mirumoji` logger with shared handlers and formatters

    info: Handlers
        - A `RotatingFileHandler` (5 MB x 3 backups) under `HOST_LOG_PATH`,
          using a clean structured format, when `log_file` is given

        - A `tqdm`-aware `Rich` console handler when `console` is `True`

    info: Idempotent
        On each call, only the handlers attached by this module are cleared so
        that repeated calls never stack handlers or disturb third-party ones

    Args:
        log_file (str | None): Log file name under `HOST_LOG_PATH`, or `None`
            for no file handler (Modal containers only emit to stdout)
        console (bool): Whether to attach the `Rich` console handler
        level (str | int | None): Explicit level, or `None` to read
            `MIRUMOJI_LOGGING_LEVEL` (default `INFO`)
        capture_root (bool): When `True`, also attach the same file handler to
            the root logger so third-party records get a UTF-8 sink instead of
            logging's last-resort stderr handler. Requires `log_file`

    Raises:
        ValueError: If `capture_root` is set without a `log_file`
    """
    if capture_root and log_file is None:
        raise ValueError("capture_root=True requires a log_file")

    resolved = _resolve_level(level)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(resolved)
    logger.propagate = False

    root = logging.getLogger()
    _clear_managed(logger)
    _clear_managed(root)

    file_handler: RotatingFileHandler | None = None
    if log_file is not None:
        file_handler = _build_file_handler(log_file)
        logger.addHandler(file_handler)

    if console:
        logger.addHandler(_build_console_handler())

    # Share the single file-handler instance so that the file is never rotated
    # by two separate handlers writing to it at once
    if capture_root and file_handler is not None:
        root.setLevel(resolved)
        root.addHandler(file_handler)
