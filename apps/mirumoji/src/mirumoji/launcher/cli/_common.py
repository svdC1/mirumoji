"""
Defines shared helpers for the CLI's `Typer` command implementations

info: Scope
    - Centralises command output display using `Rich`

    - Centralises error message display using `Rich`

    - Maps the `shared` core's typed exceptions to `Rich` messages +
      `Typer.Exit` non-zero exits
"""

import subprocess
import sys
import threading
from collections import OrderedDict, deque
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, TypeVar, cast, overload

import typer
from rich.console import Group, RenderableType
from rich.live import Live
from rich.table import Table
from rich.text import Text

from ..core import checks, envfile, process
from ..core.constants import CONFIG_ENV_VARS, backend_vars
from ..core.docker_progress import classify
from ..core.errors import LauncherError
from ..core.log_render import tokenize
from ..core.models import Backend, CheckStatus, ImageSource
from .theme import console, err_console

_T = TypeVar("_T")

_ALL_ENV_VARS = [v.name for v in CONFIG_ENV_VARS]
"""
Every environment variable name that the launcher recognises in the user's
configuration `.env` file
"""


# --- Stream Rendering ---

# Maps a Docker progress `kind` (see `core.docker_progress`) to a `Rich` style
_KIND_STYLE = {"done": "success", "active": "info", "idle": "muted"}

# Maps a log-segment `kind` (see `core.log_render`) to a `Rich` style for the
# `logs` console view. The `level` kind is styled by its word via
# `_LOG_LEVEL_STYLE`
_LOG_STYLE = {
    "service": "#E2533B",
    "uuid": "#F08A6E",
    "url": "underline #5E83A4",
    "path": "#5E83A4",
    "number": "#C99A57",
    "ok": "#8AA06A",
    "bad": "bold #C8503D",
    "warn": "#D9A441",
}

_LOG_LEVEL_STYLE = {
    "DEBUG": "#7E7567",
    "INFO": "#5E83A4",
    "WARNING": "#D9A441",
    "ERROR": "bold #C8503D",
    "CRITICAL": "bold #C8503D",
}


class StreamRender:
    """
    Bounded, Docker-aware live renderer for streamed subprocess output

    question: Why
        Docker emits plain progress lines (one line per update) when its
        output is piped, producing a huge amount of output which grows
        a `Rich` table out of bounds

    info: How It Works
        - Per-layer progress lines are collapsed by layer id into a single
          in-place row, mirroring Docker's native console display, bounding
          the layer section to the image's layer count

        - Every other line (build output, `logs -f`, git) goes to a bounded
          tail showing only the most recent lines

    Args:
        title (str): Heading shown above the rendered output
        max_layers (int): Most layer rows to show at once
        max_tail (int): Most non-layer lines to keep
    """

    def __init__(
        self,
        title: str,
        *,
        max_layers: int = 10,
        max_tail: int = 8,
    ) -> None:
        self.title = title
        self.max_layers = max_layers
        self._layers: OrderedDict[str, str] = OrderedDict()
        self._tail: deque[str] = deque(maxlen=max_tail)

    def add(self, line: str) -> None:
        """
        Routes a single output line into the layer map or the bounded tail

        Args:
            line (str): The raw output line to render
        """
        _, layer_id = classify(line)
        if layer_id is None:
            self._tail.append(line)
            return
        # Collapse by layer id, keeping the most-recently-updated layers when
        # the view is capped
        self._layers[layer_id] = line
        self._layers.move_to_end(layer_id)

    @staticmethod
    def _style_for(line: str) -> str:
        """
        Picks a theme style for a layer line from its Docker status

        Args:
            line (str): A matched Docker progress line

        Returns:
            The `rich` style name to render the line with
        """
        kind, _ = classify(line)
        return _KIND_STYLE.get(kind, "muted")

    def __rich__(self) -> Group:
        """
        Renders the current state as a `rich` group

        Returns:
            A `Group` of the title, the collapsed layer rows, and the tail
        """
        # A leading blank line lifts the block off the command prompt, and a
        # blank line after the title separates it from the output rows
        rows: list[RenderableType] = [Text("")]
        if self.title:
            rows.append(Text(self.title, style="heading"))
            rows.append(Text(""))

        layers = list(self._layers.values())
        hidden = len(layers) - self.max_layers
        if hidden > 0:
            layers = layers[-self.max_layers :]
            rows.append(Text(f"... {hidden} More Layer(s)", style="muted"))
        rows.extend(Text(line, style=self._style_for(line)) for line in layers)

        rows.extend(Text(f"↪ {line}", style="muted") for line in self._tail)

        return Group(*rows)


# --- Display Helpers ---


def subprocess_error_table(
    error: subprocess.CalledProcessError, name: str | None, **table_kwargs: Any
) -> Table:
    """
    Console helper that formats the information of a subprocess
    command failure as a table using `rich`

    Args:
        error (subprocess.CalledProcessError): The subprocess exception raised
            by the command
        name (str | None): Optional name to include in the table, formatted as
            `✗ {name} Command Failure`
        **table_kwargs (Any): Arguments overrides for `rich.table.Table`

    Returns:
        A `rich.table.Table` object with subprocess failure information

    """

    cmd_str = " ".join(error.cmd) if isinstance(error.cmd, list) else error.cmd
    stderr = error.stderr.strip() if error.stderr else "None"
    stdout = error.stdout.strip() if error.stdout else "None"
    name = name or "External"
    table_args: dict[str, Any] = {
        "title": f"✗ {name} Command Failure",
        "border_style": "danger",
    }

    if table_kwargs:
        table_args.update(table_kwargs)

    error_table = Table(**table_args)

    error_table.add_column("Attribute", style="danger")
    error_table.add_column("Detail", style="danger")

    error_table.add_row("Command", cmd_str, style="info")
    error_table.add_row("Exit Code", str(error.returncode), style="info")
    error_table.add_row("Output", stdout, style="info")
    error_table.add_row("Error Output", stderr, style="info")

    return error_table


# --- Error Handling ---


def fail(
    message: str = "Operation Aborted",
    code: int = 1,
) -> typer.Exit:
    """
    Console helper that prints errors with  `rich` and returns a `typer.Exit`
    object for the launcher command to raise

    Args:
        messsage (str): Error message to display, formatted as `✗ {message}`
        code (int): The non-zero status to raise
    Returns:
        A `typer.Exit` object carrying a non-zero status
    """

    err_console.print(f"✗ {message}", style="danger")
    return typer.Exit(code=code)


@overload
def _consume_stream(
    gen: Generator[str, None, _T],
    render: StreamRender,
    identifier: str,
    handle: None = None,
) -> _T: ...


@overload
def _consume_stream(
    gen: Generator[str, None, _T],
    render: StreamRender,
    identifier: str,
    handle: process.StreamHandle,
) -> _T | None: ...


def _consume_stream(
    gen: Generator[str, None, _T],
    render: StreamRender,
    identifier: str,
    handle: process.StreamHandle | None = None,
) -> _T | None:
    """
    Consumes a `core.process.stream` generator, rendering each line through a
    bounded `StreamRender`. In addition, maps launcher / subprocess errors to
    clean `Typer` command exits

    Args:
        gen (Generator[str, None, T]): A generator yielding output lines
        render (StreamRender): The bounded renderer to route each line through
        identifier (str): An identifier for the command (e.g `Docker`), used in
            error messages
        handle (process.StreamHandle | None): When given, consumption stops as
            soon as the handle is cancelled, so a `CTRL+C` tears the display
            down promptly instead of draining the backlog

    Returns:
        The generator's return value or None when the operation was cancelled
    """
    # The `Live` is transient so that the render clears when the block exits
    # (success or error). Exceptions are handled OUTSIDE the block so that the
    # mapped error message prints cleanly instead of being swallowed by it
    try:
        with Live(
            render,
            refresh_per_second=10,
            console=console,
            transient=True,
        ):
            while True:
                # On cancel (CTRL+C) the process is killed, but lines it
                # already wrote stay buffered in the pipe and `readline` keeps
                # returning them. Stop consuming at once instead of appending
                # each into the renderer, so the `Live` tears down before
                # the interpreter shuts down on a daemon thread still writing
                # to stdout
                if handle is not None and handle.cancelled:
                    return None
                try:
                    line = next(gen)
                except StopIteration as stop:
                    return cast(_T, stop.value)
                render.add(line)

    # Catch Launcher Exceptions
    except LauncherError as exc:
        raise fail(str(exc)) from exc

    # Catch Subprocess Exceptions
    except subprocess.CalledProcessError as exc:
        err_console.print(subprocess_error_table(exc, name=identifier))
        raise fail(f"{identifier} Command Failed") from exc

    # Catch Executable Not Found Exceptions
    except FileNotFoundError as exc:
        raise fail(f"Command `{exc.filename}` Couldn't Be Found") from exc


def stream_command(
    gen: Generator[str, None, _T],
    identifier: str,
    title: str,
    *,
    handle: process.StreamHandle | None = None,
) -> _T:
    """
    Consumes the streaming generator returned by `core.process.stream`,
    rendering each line through a bounded `StreamRender` and returning the
    process' return value. Maps launcher errors to clean `Typer` command exits

    info: Cancellation
        - When a `StreamHandle` is given (the same one passed to the streaming
          generator), output is consumed on a worker thread so that `CTRL+C`
          on the main thread can stop a stream that's blocked waiting for its
          next line (e.g. `docker compose logs -f`)

        - The interrupt cancels the handle, killing the followed process, and
          exits cleanly

        - Without a handle the generator is consumed in the same thread that's
          running this function

    Args:
        gen (Generator[str, None, T]): A generator yielding output lines
        identifier (str): An identifier for the command being executed
            (e.g `Docker`)
        title (str): The heading shown above the streamed output
        handle (process.StreamHandle | None): The cancellation token bound to
            `gen`, enabling `CTRL+C` to stop a followed stream

    Returns:
        The generator's return value
    """
    render = StreamRender(title)

    # Without a handle there is nothing to cancel, so consume in place
    if handle is None:
        return _consume_stream(gen, render, identifier)

    return _drive(
        lambda: _consume_stream(gen, render, identifier, handle), handle
    )


def _drive(
    consume: Callable[[], _T | None], handle: process.StreamHandle
) -> _T:
    """
    Runs `consume` on a worker thread so `CTRL+C` can stop a blocked read

    A followed stream (`docker compose logs -f`) blocks inside `readline`
    waiting for the next line, so consumption runs on a daemon worker while the
    main thread stays free to catch the interrupt, cancel the handle (killing
    the followed process), and exit cleanly

    Args:
        consume (Callable[[], T | None]): The consumer to run, returning the
            stream's value or `None` when cancelled
        handle (process.StreamHandle): The cancellation token bound to the
            stream

    Returns:
        The consumer's return value
    """
    # A blocked `readline` (a CREATE_NO_WINDOW child gets no console signal on
    # Windows) would otherwise defer the interrupt indefinitely. The short poll
    # keeps the main thread responsive to it
    outcome: dict[str, Any] = {}

    def _worker() -> None:
        try:
            outcome["value"] = consume()
        except BaseException as exc:
            # Re-raised on the main thread so Typer handles the exit / error
            outcome["error"] = exc

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()
    try:
        while worker.is_alive():
            worker.join(timeout=0.2)
    except KeyboardInterrupt:
        # Marks the handle on CTRL + C (the consumer stops on its next check)
        # and kills the followed process so a blocked `readline` returns.
        # Bound the join so a stuck worker can't hang the exit, then flush
        # stdout so the interpreter never shuts down mid-write on the daemon
        # worker thread
        handle.cancel()
        worker.join(timeout=2.0)
        sys.stdout.flush()
        console.print("Stopped", style="muted")
        raise typer.Exit(code=130) from None

    error = outcome.get("error")
    if error is not None:
        raise error
    return cast(_T, outcome.get("value"))


def _log_line(line: str, *, with_service: bool) -> Text:
    """
    Builds a themed `Rich` line for the `logs` console view

    Args:
        line (str): A raw container log line
        with_service (bool): Whether to highlight the docker service prefix

    Returns:
        A `Text` with each tokenized segment styled like the server console
    """
    text = Text()
    for segment, kind in tokenize(line, with_service=with_service):
        if kind == "level":
            style = _LOG_LEVEL_STYLE.get(segment, "")
        else:
            style = _LOG_STYLE.get(kind, "")
        text.append(segment, style=style)
    return text


def stream_logs(
    gen: Generator[str, None, _T],
    identifier: str,
    *,
    handle: process.StreamHandle | None = None,
    with_service: bool = True,
) -> _T:
    """
    Streams container logs straight to the console as a scrolling, themed view

    info: Additional Information
        - Unlike `stream_command`, this prints each line directly and lets the
          terminal's own scrollback hold the history

        - Each line is coloured like the server console

        - Also maps launcher errors to clean `Typer` exits

    Args:
        gen (Generator[str, None, T]): A generator yielding log lines
        identifier (str): An identifier for the command (e.g `Docker`)
        handle (process.StreamHandle | None): The cancellation token enabling
            `CTRL+C` to stop a followed (`-f`) stream
        with_service (bool): Whether to highlight the docker service prefix
            (pass `False` when logs are filtered to a single service)

    Returns:
        The generator's return value
    """

    def consume() -> _T | None:
        try:
            while True:
                if handle is not None and handle.cancelled:
                    return None
                try:
                    line = next(gen)
                except StopIteration as stop:
                    return cast(_T, stop.value)
                console.print(_log_line(line, with_service=with_service))
        except LauncherError as exc:
            raise fail(str(exc)) from exc
        except subprocess.CalledProcessError as exc:
            err_console.print(subprocess_error_table(exc, name=identifier))
            raise fail(f"{identifier} Command Failed") from exc
        except FileNotFoundError as exc:
            raise fail(f"Command `{exc.filename}` Couldn't Be Found") from exc

    if handle is None:
        return cast(_T, consume())
    return _drive(consume, handle)


# -- Up Validation ---


def _validate_dependencies(backend: Backend, source: ImageSource) -> None:
    """
    Runs environment checks for all Mirumoji Docker Compose application
    dependencies and aborts if any of them is missing

    Args:
        backend (Backend): The chosen transcription backend
        source (ImageSource): Pull vs local build

    Raises:
        typer.Exit: If a required dependency to run the Mirumoji Docker
            Compose application is missing
    """
    missing = [
        result
        for result in checks.validate_deploy(backend, source)
        if result.status is CheckStatus.MISSING
    ]
    if missing:
        for result in missing:
            err_console.print(
                f"✗ {result.name}  ↦  {result.detail}",
                style="danger",
            )
        raise fail("Environment Checks Failed  ↦  Run `mirumoji doctor`")


def resolve_backend(flag: Backend | None, env_path: Path) -> Backend:
    """
    Resolves which transcription backend should be used when running
    a CLI command

    info: Order of Precedence
        The values are considered in the following order

        - Direct Flag Passed To Command (--transcribe)

        - Value Stored In The Managed Config File

        - Default (`MODAL`)

    Args:
        flag (Backend | None): The `--transcribe` value, if provided
        env_path (Path): The managed config file to fall back to

    Returns:
        The backend to use for this run
    """
    if flag is not None:
        return flag
    backend, _ = envfile.read_deployment(envfile.read(env_path))
    return backend or Backend.MODAL


def resolve_source(flag: bool | None, env_path: Path) -> ImageSource:
    """
    Resolves which image source should be used when running a CLI command

    info: Order of Precedence
        The values are considered in the following order

        - Direct Flag Passed To Command (--build/--pull)

        - Value Stored In The Managed Config File

        - Default (`PULL`)

    Args:
        flag (bool | None): `True` for `--build`, `False` for `--pull`, `None`
            when neither was passed
        env_path (Path): The managed config file to fall back to

    Returns:
        The image source to use for this run
    """
    if flag is not None:
        return ImageSource.BUILD if flag else ImageSource.PULL
    _, source = envfile.read_deployment(envfile.read(env_path))
    return source or ImageSource.PULL


def require_env(backend: Backend, env_path: Path) -> None:
    """
    Validates that every environment variable required by the chosen backend
    is configured

    info: Read-Only
        - The managed config is the source of truth

        - The process' environment is used as a fallback (Compose applies the
          same precedence at runtime) so that a value supplied purely via the
          shell does not trigger a false "missing"

    Args:
        backend (Backend): The chosen transcription backend
        env_path (Path): The managed config file to read

    Raises:
        typer.Exit: If a required variable is set neither in the config nor in
            the process' environment
    """
    values = envfile.overlay_environ(envfile.read(env_path), _ALL_ENV_VARS)
    missing = envfile.missing_required(backend_vars(backend), values)
    if missing:
        names = ", ".join(var.name for var in missing)
        raise fail(
            f"Missing Required Variables  ↦  [{names}]. "
            "Set Them With `mirumoji config set <KEY> <VALUE>`"
        )
