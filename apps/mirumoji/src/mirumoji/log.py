"""
Centralised logging configuration shared by the server, CLI, GUI, and
Modal jobs

info: One Setup
    - `setup_logging` configures the `mirumoji` logger with a rotating file
      handler and / or a `Rich` console handler

    - The file format is clean and structured for later reading, while the
      console renders through `Rich`

    - A request-scoped context (`REQUEST_CONTEXT`) lets the server tag every
      log line emitted while handling a request with its correlation id, so a
      single request's logs can be followed across the file
"""

import contextlib
import logging
import os
from contextvars import ContextVar
from functools import lru_cache
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme

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

_FILE_FORMAT = (
    "{asctime} | {levelname:<8} | {correlation_id} | "
    "{name}:{funcName} | {message}"
)
_FILE_DATEFMT = "%Y-%m-%d %H:%M:%S%z"
_CONSOLE_FORMAT = "({correlation_id}) {subsys} {message}"

_MAX_BYTES = 5_000_000
_BACKUP_COUNT = 3


REQUEST_CONTEXT: ContextVar[dict[str, str]] = ContextVar(
    "mirumoji_request_context",
)
"""
Process-scoped, request-local context populated by the server's
`LoggingMiddleware`

Holds the current request's `correlation_id`, `method`, `path`, `client_ip`,
and `query`. Empty outside of a request (launcher or
startup logs)

Context variables are process-wide and must be declared at module level (the
stdlib forbids creating them in a closure), so a module singleton is not used
"""


def get_request_context() -> dict[str, str]:
    """
    Returns the current request-scoped logging context

    Returns:
        The context dict, or an empty dict outside of a request
    """
    return REQUEST_CONTEXT.get({})


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
        # HTTP Methods (the request-summary lines from `LoggingMiddleware`)
        r"\b(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b",
        # Numbers + Optional Size | Time | Rate Unit
        (
            r"(?P<number>(?<![\w.])-?\d+(?:\.\d+)?"
            r"(?:\s?(?:[KMGT]i?B|ms|s|m|h|fps|%|x))?\b)"
        ),
        # HTTP Status Codes On A Request-Summary Line, Coloured By Class.
        # Anchored To The ` In` That Follows The Status In
        # `LoggingMiddleware`'s Format, So Only A Request Status Is Coloured,
        # Never Some Other 3-Digit Number. After `number` So The Class Wins
        r"(?P<status_ok>[123]\d\d)(?= In\b)",
        r"(?P<status_warn>4\d\d)(?= In\b)",
        r"(?P<status_bad>5\d\d)(?= In\b)",
        # Dotted Sub-Package Names (`mirumoji.server.jobs`, `server.jobs`, ...)
        r"(?P<module>(?:mirumoji|server|launcher|cli|gui)(?:\.[a-z_]+)+)",
        # Request Correlation Id - The Un-Dashed 32-Hex Tag In `(...)` That
        # `LoggingMiddleware` Prefixes To Every Request-Scoped Line. Comes
        # After `number` So It Wins The Digit Runs Inside The Hex
        r"\((?P<correlation>[0-9a-f]{32})\)",
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
        "highlighter.correlation": "#F08A6E",  # request tag
        "highlighter.method": "bold #F4EEE3",  # the request verb
        # Request Status Codes, Coloured By Class
        "highlighter.status_ok": "#8AA06A",  # 1xx/2xx/3xx - success green
        "highlighter.status_warn": "#D9A441",  # 4xx - amber, client error
        "highlighter.status_bad": "bold #C8503D",  # 5xx - danger, server error
        "highlighter.path": "#5E83A4",  # info blue
        "highlighter.url": "underline #5E83A4",  # info blue, underlined
        "highlighter.module": "#7E7567",  # muted - subsystem context
    }
)
"""
Defines the `Rich` theme for mirumoji's console logging messages mimicking the
frontend's `Sumi & Shu` design
"""


@lru_cache(maxsize=1)
def get_console() -> Console:
    """
    Returns the shared server-side `Rich` console

    Built once on first use (not at import) and reused so the console log
    handler and the themed transfer progress bars (`server.progress`) share a
    single output stream instead of fighting over stdout

    Returns:
        The shared themed `Console`
    """
    return Console(theme=MIRUMOJI_LOGGING_THEME)


class _ThemedRichHandler(RichHandler):
    """
    `RichHandler` that renders log levels in mirumoji's `Sumi & Shu` palette
    """

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


class _RequestContextFilter(logging.Filter):
    """
    Injects the request-scoped context onto every record for the file format

    Reads `REQUEST_CONTEXT` and stamps `correlation_id`, `req_method`,
    `req_path`, `client_ip` for downstream formatters that want them. Outside
    of a request the correlation id is `-`, so launcher and startup logs stay
    readable
    """

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = REQUEST_CONTEXT.get({})
        record.correlation_id = ctx.get("correlation_id") or "-"
        record.req_method = ctx.get("method", "")
        record.req_path = ctx.get("path", "")
        record.client_ip = ctx.get("client_ip", "")
        return True


class _ThirdPartyNoiseFilter(logging.Filter):
    """
    Quiets non-mirumoji INFO chatter once logging is taken over

    With every logger routed to the root logger, an ASGI server's own INFO
    lines (its access log and startup banners) would render alongside
    mirumoji's own. This passes every `mirumoji.*` record at any level, but
    drops records from other loggers below `WARNING`, so a framework's warnings
    and errors still surface themed while its INFO noise stays quiet. The rule
    is by logger name, so it names no specific server
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == _LOGGER_NAME or record.name.startswith(
            f"{_LOGGER_NAME}."
        ):
            return True
        return record.levelno >= logging.WARNING


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
    # The format references `{correlation_id}`, so the request-context filter
    # must run on the handler for every record it emits (including third-party
    # records routed here via `capture_root`)
    handler.addFilter(_RequestContextFilter())
    setattr(handler, _MANAGED_FLAG, True)
    return handler


def _build_console_handler() -> _ThemedRichHandler:
    """
    Builds the themed `Rich` console handler on the shared console

    Disables RichHandler's built-in keyword list (it highlights the HTTP
    methods as bold yellow, which would override the themed `method` group)

    Returns:
        A configured `_ThemedRichHandler` stamped as managed
    """
    handler = _ThemedRichHandler(
        console=get_console(),
        show_time=False,
        show_level=True,
        show_path=False,
        markup=False,
        rich_tracebacks=True,
        highlighter=MirumojiHighlighter(),
        keywords=[],
    )
    handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT, style="{"))
    handler.addFilter(_SubsysFilter())
    handler.addFilter(_RequestContextFilter())
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

        - A themed `Rich` console handler when `console` is `True`

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
        raise ValueError("`capture_root=True` Requires A `log_file`")

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


def takeover_logging(
    *,
    log_file: str | None = "backend.log",
    console: bool = True,
    level: str | int | None = None,
) -> None:
    """
    Makes mirumoji's logging authoritative for the whole process

    info: Framework Agnostic
        - Rather than reconfiguring a specific server (uvicorn, hypercorn,
          ...), this strips the handlers from every existing logger and turns
          their propagation back on, so every record funnels to the root
          logger,
          which carries mirumoji's themed handlers

        - A `_ThirdPartyNoiseFilter` then drops non-mirumoji records below
          `WARNING`, so a server's INFO chatter (access log, startup banners)
          stays quiet while its warnings and errors surface themed

    info: Handlers
        - A `RotatingFileHandler` (5 MB x 3 backups) under `HOST_LOG_PATH`,
          using a clean structured format, when `log_file` is given

        - A themed `Rich` console handler when `console` is `True`

    warning: Call Order
        Call from `create_app`, the app factory. It runs after an ASGI server
        has created its own loggers but before the server emits any line, so
        even the first startup banner is captured and quieted

    Args:
        log_file (str | None): Log file name under `HOST_LOG_PATH`, or `None`
            for no file handler
        console (bool): Whether to attach the `Rich` console handler
        level (str | int | None): Explicit level, or `None` to read
            `MIRUMOJI_LOGGING_LEVEL` (default `INFO`)
    """
    resolved = _resolve_level(level)

    # Route every existing logger to root by dropping its own handlers and
    # re-enabling propagation, so no logger keeps its framework-specific
    # format. The stripped handlers are closed, not just detached, so a file
    # handler (e.g. the launcher's own log when it runs the dev server)
    # releases its file rather than leaking the open handle
    for name in list(logging.root.manager.loggerDict):
        existing = logging.getLogger(name)
        for handler in existing.handlers:
            with contextlib.suppress(Exception):
                handler.close()
        existing.handlers.clear()
        existing.propagate = True
        existing.setLevel(logging.NOTSET)
        existing.disabled = False

    root = logging.getLogger()
    _clear_managed(root)
    root.setLevel(resolved)

    # One filter instance shared by both handlers (filters are stateless)
    noise_filter = _ThirdPartyNoiseFilter()

    if log_file is not None:
        file_handler = _build_file_handler(log_file)
        file_handler.addFilter(noise_filter)
        root.addHandler(file_handler)

    if console:
        console_handler = _build_console_handler()
        console_handler.addFilter(noise_filter)
        root.addHandler(console_handler)


def teardown_logging() -> None:
    """
    Closes and removes every handler this module attached, releasing the log
    file

    warning: Why It Matters
        - On Windows, an open file handle blocks deleting the folder it lives
          in, and `platformdirs` nests the log directory inside the data
          directory (`.../mirumoji/{version}/Logs`)

        - So the rotating log handler holds the whole data directory open. Call
          this at server shutdown, and before wiping the storage directory,
          so the directory can actually be removed

    info: Coverage
        Clears the managed handlers from the root logger (where `takeover`
        attaches them) and from every named logger (where `setup_logging`
        attaches them for the launcher), closing each so its file is released
    """
    _clear_managed(logging.getLogger())
    for name in list(logging.root.manager.loggerDict):
        _clear_managed(logging.getLogger(name))
