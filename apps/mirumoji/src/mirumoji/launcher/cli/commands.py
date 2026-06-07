"""
Typer command implementations for the `Mirumoji` CLI

Each CLI command uses `Typer` and `Rich` to expose the `shared` core's
functionality in a user-friendly way
"""

import os
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ...paths import DEFAULT_ENV_PATH
from ..core import checks, host, lifecycle, repo
from ..core.compose import RESOLVED_COMPOSE_PATH, write_compose
from ..core.constants import (
    HOST_LAN_IP_VAR,
    TRANSCRIBE_BACKEND_VAR,
)
from ..core.errors import LauncherError
from ..core.models import Backend, CheckResult, CheckStatus, ImageSource
from ._common import (
    _collect_env,
    _format_compose_ports,
    _parse_compose_ps,
    _validate_dependencies,
    fail,
    stream_command,
)
from .theme import console

# Maps Environment Dependency Status To Console Symbols
_SYMBOLS = {
    CheckStatus.OK: ("✓", "success"),
    CheckStatus.MISSING: ("✗", "danger"),
    CheckStatus.SKIPPED: ("-", "muted"),
}


def build(
    transcribe: Annotated[
        Backend,
        typer.Option(
            "--transcribe",
            "-t",
            prompt="Choose a Transcription Backend",
            help="Which Transcription Backend To Use",
        ),
    ] = Backend.MODAL,
) -> None:
    """
    Builds the `Mirumoji` images locally from source

    Clones/Updates the managed `mirumoji` repo checkout and builds the
    frontend + backend images locally for the chosen backend
    """

    repo_path = stream_command(
        gen=repo.ensure_repo(),
        identifier="Git",
        title="Preparing `mirumoji` Repo Checkout",
    )

    console.print("✓ Checkout Ensured", style="success")

    stream_command(
        gen=lifecycle.build_images(repo_path, transcribe),
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

    console.print(table)


def server(
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


def status() -> None:
    """
    Displays the status of the `Mirumoji` Docker Compose application's services

    Shows the running compose application's services and their health as a
    table
    """
    try:
        entries = _parse_compose_ps(lifecycle.ps())
    except LauncherError as exc:
        raise fail(str(exc)) from exc

    if not entries:
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

    for entry in entries:
        state = entry.get("State", "")
        style = "success" if state == "running" else "warning"
        table.add_row(
            entry.get("Service", entry.get("Name", "")),
            f"[{style}]{state}[/{style}]",
            entry.get("Status", ""),
            _format_compose_ports(entry),
        )

    console.print(table)


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
    stream_command(
        gen=lifecycle.logs(
            service,
            follow=follow,
            tail=tail,
            compose_file=compose_file,
        ),
        identifier="Docker",
        title="Mirumoji Docker Compose Logs",
    )


def pull(
    transcribe: Annotated[
        Backend,
        typer.Option(
            "--transcribe",
            "-t",
            prompt="Choose a Transcription Backend",
            help="Which Transcription Backend To Use",
        ),
    ] = Backend.MODAL,
) -> None:
    """
    Pulls the Mirumoji images from Docker Hub

    Pulls the pre-built `Mirumoji` Docker Images from Docker Hub for the
    chosen backend
    """
    compose_file = write_compose(transcribe, ImageSource.PULL)
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
            "Flet Is Not Installed - Run `pip install mirumoji[gui]` Or Use "
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
            help="Build Images Locally (--build) Or Pull From Docker Hub",
        ),
    ] = False,
    detach: Annotated[
        bool,
        typer.Option(
            "--detach/--foreground",
            "-d",
            help="Run Detached (--detach) Or In The Foreground",
        ),
    ] = True,
    env_file: Annotated[
        Path,
        typer.Option("--env-file", help="The .env File To Read And Update"),
    ] = DEFAULT_ENV_PATH,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Use Existing Configuration And Skip Prompts",
        ),
    ] = False,
) -> None:
    """
    Launches the Mirumoji Docker Compose Application

    info: Steps
        - Collects all variables from a `.env` file or the proccess'
          environment and validates them against the required variables

        - Prompts for required variables that are missing

        - Acquires the host's LAN IPv4 to build the frontend's self-signed
          certificate

        - Builds the correct compose file according to backend / image source
          options

        - Builds the application's Docker Images locally, or pulls the
          pre-built ones from Docker Hub

        - Rund Docker Compose Up on the generated compose file to start the
          application
    """

    source = ImageSource.BUILD if build else ImageSource.PULL

    _validate_dependencies(transcribe, source)
    _collect_env(transcribe, env_file, interactive=not yes)

    ip = host.get_host_lan_ip()
    os.environ[HOST_LAN_IP_VAR] = ip
    os.environ[TRANSCRIBE_BACKEND_VAR] = transcribe.value

    if source is ImageSource.BUILD:
        repo_path = stream_command(
            gen=repo.ensure_repo(),
            identifier="Git",
            title="Preparing `mirumoji` Repo Checkout",
        )
        console.print("✓ Checkout Ensured", style="success")

        stream_command(
            gen=lifecycle.build_images(repo_path, transcribe),
            identifier="Docker",
            title="Building Images",
        )

        console.print("✓ Images Built", style="success")

    compose_file = write_compose(transcribe, source)

    if source is ImageSource.PULL:
        stream_command(
            gen=lifecycle.pull(compose_file),
            identifier="Docker",
            title="Pulling Images",
        )
        console.print("✓ Images Pulled", style="success")

    stream_command(
        gen=lifecycle.up(compose_file, env_file=env_file, detach=detach),
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
    console.print(success_table)
    console.print(stop_panel)
