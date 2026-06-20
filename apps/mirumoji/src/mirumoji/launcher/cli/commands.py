"""
Typer command implementations for the `Mirumoji` CLI

Each CLI command uses `Typer` and `Rich` to expose the `shared` core's
functionality in a user-friendly way
"""

import logging
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.padding import Padding
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ...paths import HOST_CONFIG_FILE
from ..core import checks, envfile, host, lifecycle, process, repo
from ..core.compose import RESOLVED_COMPOSE_PATH, write_compose
from ..core.constants import (
    CONFIG_KEYS,
    HOST_LAN_IP_VAR,
    LLM_VARS,
    MODAL_VARS,
    TRANSCRIBE_BACKEND_VAR,
    deployment_choices,
    is_config_key,
)
from ..core.errors import EnvConfigError, LauncherError
from ..core.models import Backend, CheckResult, CheckStatus, ImageSource
from ..core.status import parse_status
from ._common import (
    _validate_dependencies,
    fail,
    require_env,
    resolve_backend,
    resolve_source,
    stream_command,
    stream_logs,
)
from .theme import console

LOGGER = logging.getLogger(__name__)

# Maps Environment Dependency Status To Console Symbols
_SYMBOLS = {
    CheckStatus.OK: ("✓", "success"),
    CheckStatus.MISSING: ("✗", "danger"),
    CheckStatus.SKIPPED: ("-", "muted"),
}


def build(
    transcribe: Annotated[
        Backend | None,
        typer.Option(
            "--transcribe",
            "-t",
            help="Transcription Backend (Defaults To The Saved Config)",
        ),
    ] = None,
) -> None:
    """
    Builds the `Mirumoji` images locally from source

    Clones/Updates the managed `mirumoji` repo checkout and builds the
    frontend + backend images locally for the chosen backend

    info: Backend Resolution
        The backend value is resolved in the following order

        - Value Passed To --transcribe, If Present

        - Value Stored in Config, If Present

        - Default Value (`MODAL`)

    """
    backend = resolve_backend(transcribe, HOST_CONFIG_FILE)

    repo_path = stream_command(
        gen=repo.ensure_repo(),
        identifier="Git",
        title="Preparing `mirumoji` Repo Checkout",
    )

    console.print("✓ Checkout Ensured", style="success")

    stream_command(
        gen=lifecycle.build_images(repo_path, backend),
        identifier="Docker",
        title="Building Images",
    )

    console.print("✓ Images Built", style="success")


def doctor() -> None:
    """
    Reports the status of every external dependency

    Runs every environment check and renders a report informing which
    pre-requisites are present and which are missing
    """
    results: list[CheckResult] = [
        checks.docker(),
        checks.docker_compose(),
        checks.git(),
        checks.nvidia_gpu(),
        checks.nvidia_toolkit(),
        checks.flet(),
        checks.flutter(),
    ]

    table = Table(title="Mirumoji Environment", title_style="heading")
    table.add_column("Dependency", style="ink", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Detail", style="muted")

    for result in results:
        symbol, style = _SYMBOLS[result.status]
        table.add_row(
            result.name,
            f"[{style}]{symbol} {result.status.value.title()}[/{style}]",
            result.detail,
        )

    console.print(Padding(table, (1, 0, 0, 0)))


def status() -> None:
    """
    Displays the status of the `Mirumoji` Docker Compose application's services

    Shows the running compose application's services and their health as a
    table
    """
    try:
        services = parse_status(lifecycle.ps())
    except LauncherError as exc:
        raise fail(str(exc)) from exc

    if not services:
        console.print("No Running Services Found", style="muted")
        return

    table = Table(
        title="Mirumoji Docker Compose Application",
        title_style="heading",
    )
    table.add_column("Service", style="ink", no_wrap=True)
    table.add_column("State", no_wrap=True)
    table.add_column("Status", style="muted")
    table.add_column("Ports", style="muted")

    for service in services:
        style = "success" if service.running else "warning"
        table.add_row(
            service.service,
            f"[{style}]{service.state}[/{style}]",
            service.status,
            service.ports,
        )

    console.print(Padding(table, (1, 0, 0, 0)))


def logs(
    service: Annotated[
        str | None,
        typer.Argument(help="Service To Scope To (frontend / backend)"),
    ] = None,
    follow: Annotated[
        bool,
        typer.Option("--follow", "-f", help="Follow New Output"),
    ] = False,
    tail: Annotated[
        int | None,
        typer.Option("--tail", help="Show Only The Last N Lines"),
    ] = None,
) -> None:
    """
    Streams logs from the Mirumoji Docker Compose application

    Streams Docker Container logs for the whole compose application or a
    single service
    """
    compose_file = (
        RESOLVED_COMPOSE_PATH if RESOLVED_COMPOSE_PATH.is_file() else None
    )
    # A handle lets CTRL+C stop a followed tail (otherwise the read blocks
    # forever waiting for the next line)
    handle = process.StreamHandle()
    stream_logs(
        gen=lifecycle.logs(
            service,
            follow=follow,
            tail=tail,
            compose_file=compose_file,
            handle=handle,
        ),
        identifier="Docker",
        handle=handle,
        with_service=service is None,
    )


def pull(
    transcribe: Annotated[
        Backend | None,
        typer.Option(
            "--transcribe",
            "-t",
            help="Transcription Backend (Defaults To The Saved Config)",
        ),
    ] = None,
) -> None:
    """
    Pulls the Mirumoji images from Docker Hub

    Pulls the pre-built `Mirumoji` Docker Images from Docker Hub for the chosen
    backend

    info: Backend Resolution
        The backend value is resolved in the following order

        - Value Passed To --transcribe, If Present

        - Value Stored in Config, If Present

        - Default Value (`MODAL`)
    """
    backend = resolve_backend(transcribe, HOST_CONFIG_FILE)
    compose_file = write_compose(backend, ImageSource.PULL)
    stream_command(
        gen=lifecycle.pull(compose_file),
        identifier="Docker",
        title="Pulling Images",
    )

    console.print("✓ Images Pulled", style="success")


def gui() -> None:
    """
    Launches the Mirumoji desktop GUI

    Launches the Flet desktop GUI. Requires the `gui` extra (Flet). The
    shipped standalone executables are built separately
    """
    if not checks.flet().ok:
        raise fail(
            "Flet Is Not Installed. Run `pip install mirumoji[gui]` Or Use "
            "The Standalone Executable",
        )
    from ..gui.app import main

    main()


def render(
    transcribe: Annotated[
        Backend,
        typer.Option(
            "--transcribe",
            "-t",
            prompt="Choose a Transcription Backend",
            help="Which Transcription Backend To Use",
        ),
    ] = Backend.MODAL,
    build: Annotated[
        bool,
        typer.Option(
            "--build/--pull",
            help="Reference Local Build Tags (--build) Or Docker Hub (--pull)",
        ),
    ] = False,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Where To Write The Compose File",
        ),
    ] = Path("docker-compose.yaml"),
) -> None:
    """
    Renders a resolved docker compose file from the packaged template

    Writes a resolved compose file from the packaged template for a chosen
    backend + image source. Used to produce the static files referenced by the
    manual-install documentation
    """
    source = ImageSource.BUILD if build else ImageSource.PULL
    try:
        written = write_compose(transcribe, source, out_path=output)
    except FileNotFoundError as exc:
        raise fail(f"Compose Template Not Found  ↦  {exc}") from exc
    console.print(
        f"✓ Wrote Resolved Docker Compose File to {written}",
        style="success",
    )


def down(
    volumes: Annotated[
        bool,
        typer.Option(
            "--volumes/--keep-volumes",
            "-v",
            help="Also Delete Data Volumes (Profiles, Media, Database)",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip Confirmation Prompts"),
    ] = False,
) -> None:
    """
    Stops the Mirumoji Docker Compose Application
    """
    if volumes and not yes:
        confirmed = typer.confirm(
            "This Will Permanently Delete All Profiles, Media, And The "
            "Database. Continue?",
            default=False,
        )
        if not confirmed:
            console.print("Aborted", style="muted")
            raise typer.Exit(code=0)

    compose_file = (
        RESOLVED_COMPOSE_PATH if RESOLVED_COMPOSE_PATH.is_file() else None
    )

    stream_command(
        gen=lifecycle.down(volumes=volumes, compose_file=compose_file),
        title="Stopping The Mirumoji Docker Compose Application",
        identifier="Docker",
    )

    console.print("✓ Stopped", style="success")


def up(
    transcribe: Annotated[
        Backend | None,
        typer.Option(
            "--transcribe",
            "-t",
            help="Transcription Backend (Defaults To The Saved Config)",
        ),
    ] = None,
    build: Annotated[
        bool | None,
        typer.Option(
            "--build/--pull",
            help="Build Images Locally Or Pull From Docker Hub "
            "(Defaults To The Saved Config)",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option(
            "--detach/--foreground",
            "-d",
            help="Run Detached (--detach) Or In The Foreground",
        ),
    ] = True,
) -> None:
    """
    Launches the Mirumoji Docker Compose Application

    info: Backend Resolution
        The backend value is resolved in the following order

        - Value Passed To --transcribe, If Present

        - Value Stored in Config, If Present

        - Shell's MIRUMOJI_TRANSCRIBE_BACKEND environment variable, If Present

        - Default Value (`MODAL`)

    info: Image Source Resolution
        The image source value is resolved in the following order

        - --pull / --build flags, If Present

        - Value Stored in Config, If Present

        - Shell's MIRUMOJI_IMAGE_SOURCE environment variable, If Present

        - Default Value (`PULL`)

    info: Steps
        - Resolves the backend / image source according to the order of
          precedence listed above

        - Validates that every required variable is configured (the managed
          config file is never altered in a run)

        - Acquires the host's LAN IPv4 to build the frontend's self-signed
          certificate

        - Builds the correct compose file based on the backend / image source
          choice

        - Builds images locally for a build source. For a pull source it does
          not pull explicitly, letting `docker compose up` fetch only the
          missing images (use `mirumoji pull` to refresh on demand)

        - Runs Docker Compose Up using the managed config as the `--env-file`
    """

    backend = resolve_backend(transcribe, HOST_CONFIG_FILE)
    source = resolve_source(build, HOST_CONFIG_FILE)

    _validate_dependencies(backend, source)
    require_env(backend, HOST_CONFIG_FILE)

    ip = host.get_host_lan_ip()
    os.environ[HOST_LAN_IP_VAR] = ip
    os.environ[TRANSCRIBE_BACKEND_VAR] = backend.value
    LOGGER.info(
        f"Starting Mirumoji (Backend '{backend.value}', "
        f"Source '{source.value}', LAN IP '{ip}')"
    )

    if source is ImageSource.BUILD:
        repo_path = stream_command(
            gen=repo.ensure_repo(),
            identifier="Git",
            title="Preparing `mirumoji` Repo Checkout",
        )
        console.print("✓ Checkout Ensured", style="success")

        stream_command(
            gen=lifecycle.build_images(repo_path, backend),
            identifier="Docker",
            title="Building Images",
        )

        console.print("✓ Images Built", style="success")

    compose_file = write_compose(backend, source)

    # No explicit pull here. `docker compose up` already pulls any missing
    # image and reuses cached ones, so a normal `up` doesn't need to hit
    # Docker Hub. Run `mirumoji pull` to refresh images on demand
    stream_command(
        gen=lifecycle.up(
            compose_file, env_file=HOST_CONFIG_FILE, detach=detach
        ),
        title="Starting Mirumoji",
        identifier="Docker",
    )

    success_table = Table(
        title="✓ Mirumoji Is Running",
        border_style="success",
        title_style="heading",
    )
    success_table.add_column("Local", style="ink")
    success_table.add_column("LAN", style="ink")
    success_table.add_row("https://localhost", f"https://{ip}", style="info")
    stop_panel = Panel(
        Syntax("mirumoji down", "bash"),
        title="Stop The Application",
        border_style="accent",
    )
    console.print(Padding(success_table, (1, 0, 0, 0)))
    console.print(stop_panel)


# --- Config Sub-App ---

# Variables That Have Their Values Masked When Displaying Config
_SECRET_NAMES = frozenset(
    var.name for var in (*LLM_VARS, *MODAL_VARS) if var.secret
)


def config_import(
    path: Annotated[
        Path,
        typer.Argument(help="Path To The .env File To Import"),
    ],
) -> None:
    """
    Imports A Custom `.env` File Into The Launcher's Managed Configuration

    Merges the file's variables into the managed config, overriding existing
    values and keeping any the file omits
    """
    try:
        merged = envfile.import_file(path, HOST_CONFIG_FILE)
    except EnvConfigError as exc:
        raise fail(str(exc)) from exc
    console.print(
        f"✓ Imported {path}  ↦  {HOST_CONFIG_FILE} ({len(merged)} Variables)",
        style="success",
    )


def config_show() -> None:
    """
    Shows The Launcher's Managed Configuration, Masking Secret Values
    """
    values = envfile.read(HOST_CONFIG_FILE)
    if not values:
        console.print(
            f"No Configuration Set Yet  ↦  {HOST_CONFIG_FILE}", style="muted"
        )
        return
    table = Table(
        title="Mirumoji Configuration",
        title_style="heading",
        border_style="info",
    )
    table.add_column("Variable", style="info")
    table.add_column("Value", style="ink")
    for key, value in values.items():
        shown = f"{value[0:3]}•••" if key in _SECRET_NAMES and value else value
        table.add_row(key, shown)
    console.print(Padding(table, (1, 0, 0, 0)))
    console.print(
        f"Configuration Being Stored At  ↦  {HOST_CONFIG_FILE}", style="muted"
    )


def config_path() -> None:
    """
    Prints The Path To The Launcher's Managed Configuration File
    """
    console.print(
        f"Configuration Being Stored At  ↦  {HOST_CONFIG_FILE}",
        style="info",
    )


def config_set(
    key: Annotated[str, typer.Argument(help="The Config Key To Set")],
    value: Annotated[str, typer.Argument(help="The Value To Assign")],
) -> None:
    """
    Sets (Upserts) A Single Key In The Launcher's Managed Configuration

    Rejects unknown keys, and validates the value for the deployment keys
    (`MIRUMOJI_TRANSCRIBE_BACKEND` / `MIRUMOJI_IMAGE_SOURCE`)
    """
    if not is_config_key(key):
        raise fail(
            f"Unknown Config Key '{key}'. "
            f"Valid Keys  ↦  {', '.join(sorted(CONFIG_KEYS))}"
        )
    choices = deployment_choices(key)
    if choices is not None and value not in choices:
        raise fail(
            f"Invalid Value For {key}  ↦  Choose From {', '.join(choices)}"
        )
    envfile.set_value(HOST_CONFIG_FILE, key, value)
    console.print(f"✓ Set {key}", style="success")


def config_delete(
    key: Annotated[str, typer.Argument(help="The Config Key To Delete")],
) -> None:
    """
    Removes A Single Key From The Launcher's Managed Configuration
    """
    if not is_config_key(key):
        raise fail(
            f"Unknown Config Key '{key}'. "
            f"Valid Keys  ↦  {', '.join(sorted(CONFIG_KEYS))}"
        )
    if envfile.delete_value(HOST_CONFIG_FILE, key):
        console.print(f"✓ Deleted {key}", style="success")
    else:
        console.print(f"{key} Was Not Set", style="muted")


def config_clear() -> None:
    """
    Removes All Keys from The Launcher's Managed Configuration
    """

    results = [
        envfile.delete_value(HOST_CONFIG_FILE, key) for key in CONFIG_KEYS
    ]

    deleted_keys = [k for k in results if k]

    console.print(f"✓ Deleted {len(deleted_keys)} Keys", style="success")


# --- Dev Sub-App ---


def dev_up(
    transcribe: Annotated[
        Backend | None,
        typer.Option(
            "--transcribe",
            "-t",
            help="Transcription Backend (Defaults To The Saved Config)",
        ),
    ] = None,
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help=(
                "Path To The Local Mirumoji Repo Checkout (Defaults to "
                "`Path.cwd()` When Left Empty)"
            ),
            show_default=False,
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option(
            "--detach/--foreground",
            "-d",
            help="Run Detached (--detach) Or In The Foreground",
        ),
    ] = True,
) -> None:
    """
    Launches the Mirumoji Docker Compose Application For Development Using
    Images Built With `dev build`

    Builds the `Mirumoji` images locally from a mirumoji repo clone at an
    arbitrary path without updating it

    Intended for development only. Accepts a path to a `mirumoji` repo
    checkout and builds the frontend + backend images locally for the chosen
    backend

    info: Backend Resolution
        The backend value is resolved in the following order

        - Value Passed To --transcribe, If Present

        - Value Stored in Config, If Present

        - Shell's MIRUMOJI_TRANSCRIBE_BACKEND environment variable, If Present

        - Default Value (`MODAL`)

    info: Steps
        - Resolves the backend according to the order of
          precedence listed above

        - Validates that every required variable is configured (the managed
          config file is never altered in a run)

        - Acquires the host's LAN IPv4 to build the frontend's self-signed
          certificate

        - Builds the correct compose file based on the backend choice

        - Builds images locally

        - Runs Docker Compose Up using the managed config as the `--env-file`
    """

    backend = resolve_backend(transcribe, HOST_CONFIG_FILE)
    source = ImageSource.BUILD
    if path is None:
        path = Path.cwd()

    _validate_dependencies(backend, source)
    require_env(backend, HOST_CONFIG_FILE)

    ip = host.get_host_lan_ip()
    os.environ[HOST_LAN_IP_VAR] = ip
    os.environ[TRANSCRIBE_BACKEND_VAR] = backend.value
    LOGGER.info(
        f"Starting Mirumoji (Backend '{backend.value}', "
        f"Source '{source.value}', LAN IP '{ip}')"
    )

    stream_command(
        gen=lifecycle.build_images(path, backend),
        identifier="Docker",
        title="Building Images",
    )

    console.print("✓ Images Built", style="success")

    compose_file = write_compose(backend, source)

    stream_command(
        gen=lifecycle.up(
            compose_file,
            env_file=HOST_CONFIG_FILE,
            detach=detach,
        ),
        title="Starting Mirumoji",
        identifier="Docker",
    )

    success_table = Table(
        title="✓ Mirumoji Is Running",
        border_style="success",
        title_style="heading",
    )
    success_table.add_column("Local", style="ink")
    success_table.add_column("LAN", style="ink")
    success_table.add_row("https://localhost", f"https://{ip}", style="info")
    stop_panel = Panel(
        Syntax("mirumoji down", "bash"),
        title="Stop The Application",
        border_style="accent",
    )
    console.print(Padding(success_table, (1, 0, 0, 0)))
    console.print(stop_panel)


def dev_server(
    host: Annotated[
        str,
        typer.Option(help="Interface To Bind"),
    ] = "0.0.0.0",
    port: Annotated[
        int,
        typer.Option(help="Port To Listen On"),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option(help="Reload On Code Changes (Development)"),
    ] = False,
) -> None:
    """
    Runs the Mirumoji server with uvicorn

    Launches the FastAPI server directly with uvicorn (no Docker), using the
    app factory. Intended for local development and Python-only iteration
    """
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise fail(
            "The Server Extra Is Not Installed — Run `pip install "
            "mirumoji[server]`",
        ) from exc

    uvicorn.run(
        "mirumoji.server.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )
