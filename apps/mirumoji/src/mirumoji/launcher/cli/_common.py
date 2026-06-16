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
from collections.abc import Generator
from pathlib import Path
from typing import Any, TypeVar, cast, overload

import typer
from rich.live import Live
from rich.table import Table

from ..core import checks, envfile, process
from ..core.constants import CONFIG_ENV_VARS, backend_vars
from ..core.errors import LauncherError
from ..core.models import Backend, CheckStatus, ImageSource
from .theme import console, err_console

_T = TypeVar("_T")

_ALL_ENV_VARS = [v.name for v in CONFIG_ENV_VARS]
"""
Every environment variable name that the launcher recognises in the user's
configuration `.env` file
"""


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
    table: Table,
    identifier: str,
    handle: None = None,
) -> _T: ...


@overload
def _consume_stream(
    gen: Generator[str, None, _T],
    table: Table,
    identifier: str,
    handle: process.StreamHandle,
) -> _T | None: ...


def _consume_stream(
    gen: Generator[str, None, _T],
    table: Table,
    identifier: str,
    handle: process.StreamHandle | None = None,
) -> _T | None:
    """
    Consumes a `core.process.stream` generator, pretty-printing each line to a
    live `rich` table. In addition, maps launcher / subprocess errors to clean
    `Typer` command exits

    Args:
        gen (Generator[str, None, T]): A generator yielding output lines
        table (Table): The `rich` table to append each output line to
        identifier (str): An identifier for the command (e.g `Docker`), used in
            error messages
        handle (process.StreamHandle | None): When given, consumption stops as
            soon as the handle is cancelled, so a `CTRL+C` tears the display
            down promptly instead of draining the backlog

    Returns:
        The generator's return value or None when the operation was cancelled
    """
    # The `Live` is transient so that the progress table clears when the block
    # exits (success or error). Exceptions are handled OUTSIDE the block so
    # that the mapped error message prints cleanly instead of being swallowed
    # by it
    try:
        with Live(
            table,
            refresh_per_second=10,
            console=console,
            transient=True,
        ):
            while True:
                # On cancel (CTRL+C) the process is killed, but lines it
                # already wrote stay buffered in the pipe and `readline` keeps
                # returning them. Stop consuming at once instead of rendering
                # each into the growing table, so the `Live` tears down before
                # the interpreter shuts down on a daemon thread still writing
                # to stdout
                if handle is not None and handle.cancelled:
                    return None
                try:
                    line = next(gen)
                except StopIteration as stop:
                    return cast(_T, stop.value)
                table.add_row(f"↪ {line}", style="muted")

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
    pretty-printing each line inside a `rich` table and returning the process'
    return value. Maps launcher errors to clean `Typer` command exits

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
        title (str): The title of the `rich` table in which command output
            will be displayed
        handle (process.StreamHandle | None): The cancellation token bound to
            `gen`, enabling `CTRL+C` to stop a followed stream

    Returns:
        The generator's return value
    """
    table = Table(
        title=title,
        title_style="heading",
        border_style="info",
        show_header=False,
    )
    table.add_column()

    # Without a handle there is nothing to cancel, so consume in place
    if handle is None:
        return _consume_stream(gen, table, identifier)

    # With a handle, consume on a worker thread and keep the main thread free
    # to catch CTRL+C. A blocked `readline` (a CREATE_NO_WINDOW child gets no
    # console signal on Windows) would otherwise defer the interrupt
    # indefinitely. The short poll keeps the main thread responsive to it
    outcome: dict[str, Any] = {}

    def _worker() -> None:
        try:
            outcome["value"] = _consume_stream(gen, table, identifier, handle)
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
