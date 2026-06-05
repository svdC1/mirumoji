"""
Defines shared helpers for the CLI's `Typer` command implementations

info: Scope
    - Centralises command output display using `Rich`

    - Centralises error message display using `Rich`

    - Maps the `shared` core's typed exceptions to `Rich` messages +
      `Typer.Exit` non-zero exits
"""

import json
import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import Any, TypeVar, cast

import typer
from rich.live import Live
from rich.table import Table

from .shared import checks, envfile
from .shared.constants import (
    LLM_VARS,
    MODAL_VARS,
    PASSTHROUGH_VARS,
    prompted_vars,
)
from .shared.errors import LauncherError
from .shared.models import Backend, CheckStatus, EnvVar, ImageSource
from .theme import console, err_console

_T = TypeVar("_T")

_ALL_ENV_VARS = [
    *(v.name for v in (*LLM_VARS, *MODAL_VARS)),
    *PASSTHROUGH_VARS,
]
"""
Every environment variable name that the launcher may carry from the
environment into the `.env` file
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
    *,
    print_calls: tuple[dict[str, Any]] | None = None,
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


def stream_command(
    gen: Generator[str, None, _T],
    identifier: str,
    title: str,
) -> _T:
    """
    Consumes the streaming generator returned by `shared.process.stream`,
    pretty-printing each line (external command output) inside a `rich` table
    , and returning the process' return code at the end. In addition, maps
    launcher errors to clean `Typer` command exits

    Args:
        gen (Generator[str, None, T]): A generator yielding output lines
        identifier (str): An identifier for the command being executed
            (e.g `Docker`)
        title (str): The title of the `rich` table in which command output
            will be displayed

    Returns:
        The generator's return value
    """
    # Create Dynamic Table
    table = Table(
        title=title,
        title_style="heading",
        border_style="info",
        show_header=False,
    )
    table.add_column()

    # The `Live` is transient so the progress table clears when the block
    # exits (success or error). Exceptions are handled OUTSIDE the block so the
    # mapped error message prints cleanly instead of being swallowed by it
    try:
        with Live(
            table, refresh_per_second=10, console=console, transient=True
        ):
            while True:
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


# --- Docker Helpers ---


def _parse_compose_ps(output: str) -> list[dict[str, Any]]:
    """
    Parses `docker compose ps` JSON, tolerating array or NDJSON forms

    Args:
        output (str): The raw compose `ps --format json` output

    Returns:
        The parsed service entries
    """
    text = output.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        entries = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        return entries


def _format_compose_ports(entry: dict[str, Any]) -> str:
    """
    Formats a `docker compose ps` service entry's published ports as
    `host->container`

    Args:
        entry (dict): A compose `ps` service entry

    Returns:
        A comma-separated published-ports summary
    """
    pubs = entry.get("Publishers") or []
    parts = [
        f"{p.get('PublishedPort')}->{p.get('TargetPort')}"
        for p in pubs
        if p.get("PublishedPort")
    ]
    return ", ".join(parts)


# -- Up Validation ---


def _validate_dependencies(backend: Backend, source: ImageSource) -> None:
    """
    Runs environment checks for all Mirumoji Docker Compose apploication
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
        for result in checks.validate(backend, source)
        if result.status is CheckStatus.MISSING
    ]
    if missing:
        for result in missing:
            err_console.print(
                f"✗ {result.name}  ↦  {result.detail}",
                style="danger",
            )
        raise fail("Environment Checks Failed  ↦  Run `mirumoji doctor`")


def _prompt_env_var(var: EnvVar, current: str) -> str:
    """
    Prompts for a single environment variable, looping until a required one is
    given

    Args:
        var (EnvVar): The variable to prompt for
        current (str): The currently resolved value, if any

    Returns:
        The entered (or retained) value
    """
    default = current or var.default
    label = var.description or var.name
    while True:
        entered: str = typer.prompt(
            label,
            default=default,
            hide_input=var.secret,
            show_default=not var.secret,
        ).strip()
        if entered or not var.required:
            return entered
        console.print(f"{var.name} Is Required", style="warning")


def _collect_env(
    backend: Backend,
    env_path: Path,
    *,
    interactive: bool,
) -> dict[str, str]:
    """
    Resolves the environment, prompting for missing values when `interactive`
    is `True`

    info: Steps
        - Reads the existing `.env` file at `env_path`

        - Appends the process' environment variables (see
          `shared.envfile.overlay_environ`)

        - If `interactive=False` validates that all required variables are set

        - If `interactive=True` prompts for missing values

        - Writes all collected variables to the `.env` file at `env_path`

    Args:
        backend (Backend): The chosen transcription backend
        env_path (Path): The `.env` file to read and update
        interactive (bool): Whether to prompt for values

    Returns:
        The resolved environment values

    Raises:
        typer.Exit: If a required var is missing and prompting is disabled
    """
    values = envfile.overlay_environ(
        envfile.read(env_path),
        _ALL_ENV_VARS,
    )

    vars = prompted_vars(backend)

    if not interactive:
        missing = envfile.missing_required(vars, values)
        if missing:
            names = ", ".join(var.name for var in missing)
            raise fail(f"Missing Required Variables  ↦  [{names}]")
        return values

    for var in vars:
        entered = _prompt_env_var(var, values.get(var.name, ""))
        if entered:
            values[var.name] = entered

    envfile.write(env_path, values)
    console.print(f"Saved Configuration To {env_path}", style="muted")
    return values
