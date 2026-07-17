"""
Typer command implementations for the `Mirumoji` CLI

Each CLI command uses `Typer` and `Rich` to expose the `shared` core's
functionality in a user-friendly way
"""

import json
import logging
import os
import secrets
from pathlib import Path
from typing import Annotated

import typer
from rich.padding import Padding
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ... import __version__
from ... import modal as modal_lifecycle
from ...exceptions import ModalError
from ...paths import HOST_CONFIG_FILE
from ..core import checks, envfile, host, lifecycle, process, repo, storage
from ..core.compose import RESOLVED_COMPOSE_PATH, write_compose
from ..core.constants import (
    CONFIG_ENV_VARS,
    CONFIG_KEYS,
    HOST_LAN_IP_VAR,
    TRANSCRIBE_BACKEND_VAR,
    deployment_choices,
    is_config_key,
)
from ..core.errors import EnvConfigError, LauncherError
from ..core.models import Backend, CheckResult, CheckStatus, ImageSource
from ..core.status import parse_status
from ..modal.constants import (
    DATA_VOLUME_NAME,
    HOST_APP_NAME,
    WEB_FUNCTION_NAME,
    WEB_PASSWORD_ENV,
    WEB_USERNAME,
)
from ._common import (
    _validate_dependencies,
    fail,
    require_env,
    require_published_version,
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
    version: Annotated[
        str | None,
        typer.Option(
            "--image-version",
            help="Build This Version's Tagged Source (Defaults To The "
            "Installed One)",
        ),
    ] = None,
) -> None:
    """
    Builds the `Mirumoji` images locally from source

    Clones/Updates the managed `mirumoji` repo checkout at the resolved
    version's release tag and builds the frontend + backend images locally for
    the chosen backend

    info: Backend Resolution
        The backend value is resolved in the following order

        - Value Passed To --transcribe, If Present

        - Value Stored in Config, If Present

        - Default Value (`MODAL`)

    info: Version Resolution Order
        The release tag whose source is built is resolved in the following
        order

        - Value Passed To --image-version, If Present

        - MIRUMOJI_IMAGE_VERSION Stored In Config, If Present

        - Shell's MIRUMOJI_IMAGE_VERSION Environment Variable, If Present

        - Default Value (The Installed Package Version)

    The locally built images always carry the local build tags, so the version
    only selects which release's source (its `v<version>` git tag) is built
    """
    backend = envfile.resolve_backend(transcribe, HOST_CONFIG_FILE)
    version = envfile.resolve_image_version(HOST_CONFIG_FILE, version)

    repo_path = stream_command(
        gen=repo.ensure_repo(ref=f"v{version}"),
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
        typer.Option(
            "--follow",
            "-f",
            help="Follow New Output",
        ),
    ] = False,
    tail: Annotated[
        int | None,
        typer.Option(
            "--tail",
            "-t",
            help="Show Only The Last N Lines",
        ),
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
    version: Annotated[
        str | None,
        typer.Option(
            "--image-version",
            help="Use This Published Version (Defaults To The Installed One)",
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

    info: Version Resolution Order
        The version value is resolved in the following order

        - Value Passed To --image-version, If Present

        - MIRUMOJI_IMAGE_VERSION Stored In Config, If Present

        - Shell's MIRUMOJI_IMAGE_VERSION Environment Variable, If Present

        - Default Value (The Installed Package Version)
    """
    backend = envfile.resolve_backend(transcribe, HOST_CONFIG_FILE)
    version = envfile.resolve_image_version(HOST_CONFIG_FILE, version)
    require_published_version(version)
    compose_file = write_compose(backend, ImageSource.PULL, version=version)
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
    version: Annotated[
        str | None,
        typer.Option(
            "--image-version",
            help="Pin The Image Version (Defaults To The Installed One)",
        ),
    ] = None,
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

    info: Version Resolution Order
        The version value is resolved in the following order

        - Value Passed To --image-version, If Present

        - MIRUMOJI_IMAGE_VERSION Stored In Config, If Present

        - Shell's MIRUMOJI_IMAGE_VERSION Environment Variable, If Present

        - Default Value (The Installed Package Version)
    """
    source = ImageSource.BUILD if build else ImageSource.PULL
    version = envfile.resolve_image_version(HOST_CONFIG_FILE, version)
    try:
        written = write_compose(
            transcribe, source, version=version, out_path=output
        )
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
        typer.Option(
            "--yes",
            "-y",
            help="Skip Confirmation Prompts",
        ),
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


def reset(
    keep_config: Annotated[
        bool,
        typer.Option(
            "--keep-config",
            "-kc",
            help="Preserve The Config File (Your LLM / Modal Keys)",
        ),
    ] = False,
    keep_logs: Annotated[
        bool,
        typer.Option(
            "--keep-logs",
            "-kl",
            help="Preserve The Log Files",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip Confirmation Prompts",
        ),
    ] = False,
) -> None:
    """
    Deletes Mirumoji's Local Data Folder From This Machine

    Removes media, the database, cached builds, and (unless kept) the config
    and logs. Docker data volumes are not touched, use `down --volumes` for
    those
    """
    if not yes:
        kept = [
            name
            for name, keep in (("Config", keep_config), ("Logs", keep_logs))
            if keep
        ]
        note = f" (Keeping {', '.join(kept)})" if kept else ""
        confirmed = typer.confirm(
            "This Will Permanently Delete Mirumoji's Local Data Folder"
            f"{note}. Continue?",
            default=False,
        )
        if not confirmed:
            console.print("Aborted", style="muted")
            raise typer.Exit(code=0)

    steps = storage.reset_storage(
        keep_config=keep_config,
        keep_logs=keep_logs,
    )

    failures = 0
    for step in steps:
        if step.status == "removed":
            console.print(f"✓ Removed {step.label}", style="success")
        elif step.status == "absent":
            console.print(f"- {step.label} (Nothing To Remove)", style="muted")
        else:
            failures += 1
            console.print(
                f"✗ {step.label} In Use ({step.detail})",
                style="warning",
            )

    if failures:
        console.print(
            f"⚠ {failures} Item(s) Left In Place. Stop The App Or Server "
            "And Retry",
            style="warning",
        )
    else:
        console.print("✓ Fresh Start Complete", style="success")


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
    version: Annotated[
        str | None,
        typer.Option(
            "--image-version",
            help="Use This Published Version (Defaults To The Installed One)",
        ),
    ] = None,
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

    info: Version Resolution Order
        The version value is resolved in the following order

        - Value Passed To --image-version, If Present

        - MIRUMOJI_IMAGE_VERSION Stored In Config, If Present

        - Shell's MIRUMOJI_IMAGE_VERSION Environment Variable, If Present

        - Default Value (The Installed Package Version)

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

    backend = envfile.resolve_backend(transcribe, HOST_CONFIG_FILE)
    source = envfile.resolve_source(build, HOST_CONFIG_FILE)
    version = envfile.resolve_image_version(HOST_CONFIG_FILE, version)

    _validate_dependencies(backend, source)
    require_env(backend, HOST_CONFIG_FILE)
    if source is ImageSource.PULL:
        require_published_version(version)

    ip = host.get_host_lan_ip()
    os.environ[HOST_LAN_IP_VAR] = ip
    os.environ[TRANSCRIBE_BACKEND_VAR] = backend.value
    LOGGER.info(
        f"Starting Mirumoji (Backend '{backend.value}', "
        f"Source '{source.value}', LAN IP '{ip}')"
    )

    if source is ImageSource.BUILD:
        repo_path = stream_command(
            gen=repo.ensure_repo(ref=f"v{version}"),
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

    compose_file = write_compose(backend, source, version=version)

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
        caption=(
            f"Trust Other Devices: Install http://{ip}/mirumoji-ca.crt "
            f"Once Per Device For A Trusted HTTPS Origin (Enables The "
            f"Installable PWA)"
        ),
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
_SECRET_NAMES = frozenset(var.name for var in CONFIG_ENV_VARS if var.secret)


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


def config_show(
    raw: Annotated[
        bool,
        typer.Option(
            "--raw",
            help="Show Secret Values Unmasked (Tokens, Passwords)",
        ),
    ] = False,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print Output As A JSON String (Always Shows Secret Values "
                "Unmasked)"
            ),
        ),
    ] = False,
) -> None:
    """
    Shows The Launcher's Managed Configuration, Masking Secret Values

    Pass `--raw` to reveal the secret values in full, for copying a generated
    password or auditing a key
    """
    values = envfile.read(HOST_CONFIG_FILE)
    if not values:
        console.print(
            f"No Configuration Set Yet  ↦  {HOST_CONFIG_FILE}", style="muted"
        )
        return

    if output_json:
        console.print(json.dumps(values))
        return

    caption = (
        Text(
            "Secret Values Are Shown, Keep This Output Private",
            style="warning",
        )
        if raw
        else None
    )

    table = Table(
        title="Mirumoji Configuration",
        title_style="heading",
        border_style="info",
        caption=caption,
        show_lines=True,
    )
    table.add_column("Variable", style="info")
    table.add_column(
        "Value",
        style="ink",
        overflow="fold",
        max_width=60,
    )
    for key, value in values.items():
        masked = key in _SECRET_NAMES and value and not raw
        shown = f"{value[0:3]}•••" if masked else value
        table.add_row(key, shown)
    console.print(Padding(table, (1, 0, 0, 0)))


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
    Launches the Mirumoji Docker Compose Application For Development

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

    backend = envfile.resolve_backend(transcribe, HOST_CONFIG_FILE)
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

    # BUILD uses the fixed local image tags, so the version is irrelevant here
    compose_file = write_compose(backend, source, version=__version__)

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
        caption=(
            f"Trust Other Devices  ↦  Install http://{ip}/mirumoji-ca.crt "
            f"Once Per Device For A Trusted HTTPS Origin (Enables The "
            f"Installable PWA)"
        ),
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


# --- Modal Host Sub-App ---


def modal_deploy(
    gen_password: Annotated[
        bool,
        typer.Option(
            "--generate-password",
            "-gp",
            help=(
                "Generate A Secure Password For The Deployed App And Save It "
                "To The Managed Config When MIRUMOJI_WEB_PASSWORD Is Not Set"
            ),
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Redeploy Even If The Same Version Is Already Live",
        ),
    ] = False,
    version: Annotated[
        str | None,
        typer.Option(
            "--image-version",
            help="Use This Published Version (Defaults To The Installed One)",
        ),
    ] = None,
) -> None:
    """
    Deploys A Fully Functional Mirumoji App To Your Modal Account

    Deploys a `Modal` web function running a FastAPI app serving both the
    `modal` transcribe backend and the built frontend

    The app is accessible at the printed URL and gated by `HTTP Basic Auth`
    with `mirumoji` as the username and the `MIRUMOJI_WEB_PASSWORD` managed
    config variable as the password

    info: `--generate-password` (`-gp`)
        - When this flag is passed, a unique password is generated and stored
          in the managed config under `MIRUMOJI_WEB_PASSWORD`

        - When this flag is passed and `MIRUMOJI_WEB_PASSWORD` already exists
          as a variable in the managed config (`mirumoji config show`), or as
          an environment variable in the current shell, the already-existent
          value is used and no new password is created

        - When this flag is not passed and the `MIRUMOJI_WEB_PASSWORD` variable
          doesn't exist in either the managed config or the current shell, this
          command displays an error message

        - The `MIRUMOJI_WEB_PASSWORD` set in the managed config has preference
          over the one set in the current shell and is the one that will be
          used when both are set

    info: Idempotent Deployment
        - Re-running this command rolls the app forward only on version bumps
          without ever creating duplicates

        - Pass `--force` (`-f`) to always redeploy the app

    info: Version Resolution Order
        The version value is resolved in the following order

        - Value Passed To --image-version, If Present

        - MIRUMOJI_IMAGE_VERSION Stored In Config, If Present

        - Shell's MIRUMOJI_IMAGE_VERSION Environment Variable, If Present

        - Default Value (The Installed Package Version)

    info: Distinction From The Mirumoji `modal-offload` App
        - When running mirumoji locally with the `modal` transcribe backend
          set up, the server automatically creates and manages a different
          `Modal` app called `mirumoji-offload`

        - `mirumoji-offload` is configured using your mirumoji-managed
          configuration variables (`MIRUMOJI_MODAL_SCALEDOWN_WINDOW`,
          `MIRUMOJI_MODAL_GPU`, `MODAL_FORCE_BUILD`, `MODAL_TOKEN_ID`,
          `MODAL_TOKEN_SECRET`, `MIRUMOJI_MODAL_IMAGE`), is always GPU-enabled,
          and always scales down to 0 when there's no GPU-task running

        - The `Modal` app that this command deploys (`mirumoji-host`)
          runs the server with the `modal` transcribe backend and serves
          the frontend in a single `Modal` `CPU-Only` container that only
          scales down when the app is stopped (`mirumoji modal down`)

        - The server running in the `mirumoji-host` app will automatically
          create a `mirumoji-offload` app (or use an already live one) with
          your mirumoji-managed configuration whenever you request a task
          that needs a GPU, which means that both apps will exist
          simultaneously

        - This separation exists because letting a GPU-enabled container sit
          idly can incur expensive idle-GPU charges. Separating the cheap
          CPU-only operations (running in `mirumoji-host`) from the expensive
          operations that require a GPU (`mirumoji-offload`) avoids these
          extra unnecessary charges because `mirumoji-offload` always scales
          to 0 (meaning it is never running unless an active GPU task needs
          it), while `mirumoji-host` keeps running at all times to make the
          app accessible (for watching videos, Japanese-tokenization,
          dictionary-lookups, etc...)

    info: App Configuration
        All of your mirumoji-managed configuration (`mirumoji config`),
        such as LLM keys and `modal-offload` configuration (scaledown window,
        which GPU is used), is passed to the container running `mirumoji-host`
        as a `Modal Secret`, so this is like running the local `modal`
        transcribe backend, with the only difference being that everything
        (including what would normally run locally) will be running in Modal

    info: App Data
         - Unlike the local `mirumoji up`, which keeps your data as local
           Docker volumes, the data you upload or generate while using the
           hosted app (your media files and the mirumoji database) is kept
           inside an automatically created, or reused, `Modal` volume

        - You can download this data at any time with `mirumoji modal
          download-data`

        - You can also delete the entire volume at any time with
          `mirumoji modal down -v`
    """
    from ..modal import host as modal_host

    # Get All Variables From The Managed Config File, Falling Back To The
    # Process' Environment For Missing Values
    env = envfile.resolve_managed_config(HOST_CONFIG_FILE)

    # Define The Password That Will Be Used To Gate The App
    password = env.get(WEB_PASSWORD_ENV)

    if password is None:
        if not gen_password:
            raise fail(
                "No Password  ↦  Set A Password To Gate The App With "
                "`mirumoji config set MIRUMOJI_WEB_PASSWORD ***` Or Pass "
                "`--generate-password` To Create A New One Automatically"
            )
        else:
            password = secrets.token_urlsafe(12)
            envfile.set_value(HOST_CONFIG_FILE, WEB_PASSWORD_ENV, password)
            console.print("✓ Generated A Login Password", style="success")
            env[WEB_PASSWORD_ENV] = password

    # Make Sure MODAL_TOKEN_ID + MODAL_TOKEN_SECRET Are Set
    require_env(Backend.MODAL, HOST_CONFIG_FILE)

    # The Host Runs As A Modal-Backend Server So That Transcription Offloads
    # To The GPU Worker Rather Than Needing A GPU On At All Times
    env[TRANSCRIBE_BACKEND_VAR] = Backend.MODAL.value

    # The Host Reservations (CPU, Memory, Concurrency) Size The Modal Function
    # Itself, So They Are Resolved Separately From The Container Config
    host_config = envfile.host_config(env)

    version = envfile.resolve_image_version(HOST_CONFIG_FILE, version)
    require_published_version(version)

    # The Modal Credentials Are Exported Only For The Deploy Calls, Then The
    # Process Environment Is Restored
    with modal_lifecycle.modal_credentials(env):
        try:
            with console.status(
                "[muted]Deploying The Host App[/]",
                spinner="dots",
                spinner_style="accent",
            ):
                modal_host.ensure_host_deployed(
                    env, host_config, version=version, force=force
                )
        except ModalError as exc:
            raise fail(f"Failed To Deploy The App  ↦  {exc}") from exc

        # Get The Live App URL + Modal Dashboard URL
        url = modal_lifecycle.web_url(HOST_APP_NAME, WEB_FUNCTION_NAME)
        dashboard = modal_lifecycle.dashboard_url(HOST_APP_NAME)

    table = Table(
        title="✓ Mirumoji Is Hosted",
        border_style="success",
        title_style="heading",
    )
    table.add_column("Field", style="ink", no_wrap=True)
    table.add_column("Value", style="info")
    table.add_row("URL", url or "Run `mirumoji modal status`")
    table.add_row("Username", WEB_USERNAME)
    table.add_row("Password", password)
    if dashboard:
        table.add_row("Dashboard", dashboard)
    console.print(Padding(table, (1, 0, 0, 0)))
    console.print(
        Panel(
            Syntax("mirumoji modal down", "bash"),
            title="Stop The Hosted App",
            border_style="accent",
        )
    )


def modal_status() -> None:
    """
    Shows The Status Of The Modal-Hosted App + Its Data Volume

    info: `mirumoji-offload`
        The GPU-offload worker `Modal` app is owned by the server (deployed on
        the first GPU call and torn down in its lifespan), so it is not shown
        or managed here
    """
    # Get All Variables From The Managed Config File, Falling Back To The
    # Process' Environment For Missing Values
    env = envfile.resolve_managed_config(HOST_CONFIG_FILE)

    # Make Sure MODAL_TOKEN_ID + MODAL_TOKEN_SECRET Are Set
    require_env(Backend.MODAL, HOST_CONFIG_FILE)

    # The Modal Credentials Are Exported Only For The Status Calls, Then The
    # Process Environment Is Restored
    try:
        with modal_lifecycle.modal_credentials(env):
            # Verify App Is Deployed
            is_deployed = False
            deployed_version = "Unknown"
            tags = modal_lifecycle.deployed_tags(HOST_APP_NAME)
            if tags is not None:
                is_deployed = True
                deployed_version = tags.get(
                    modal_lifecycle.VERSION_KEY, "Unknown"
                )

            # Verify Volume Exists
            volume_exists = modal_lifecycle.volume_exists(DATA_VOLUME_NAME)

            # Get Live App URL + Dashboard URL If App Is Deployed
            live_url = None
            dashboard_url = None
            if is_deployed:
                live_url = modal_lifecycle.web_url(
                    HOST_APP_NAME, WEB_FUNCTION_NAME
                )
                dashboard_url = modal_lifecycle.dashboard_url(HOST_APP_NAME)
    except ModalError as exc:
        raise fail(f"Could Not Query The Deployment  ↦  {exc}") from exc

    # Print Result
    table = Table(
        title="Mirumoji Modal Deployment",
        title_style="heading",
        border_style="info",
    )
    table.add_column("Resource", style="ink", no_wrap=True)
    table.add_column("State", no_wrap=True)
    table.add_column("Detail", style="muted")
    if not is_deployed:
        table.add_row("Host App", "[muted]Not Deployed[/]", HOST_APP_NAME)
    else:
        table.add_row(
            "Host App",
            "[success]Deployed[/]",
            f"{HOST_APP_NAME} (v{deployed_version})",
        )
    table.add_row(
        "Data Volume",
        "[success]Present[/]" if volume_exists else "[muted]Absent[/]",
        DATA_VOLUME_NAME,
    )

    if live_url is not None:
        table.add_row("URL", f"[info]{live_url}[/]", "")
    if dashboard_url is not None:
        table.add_row("Dashboard", f"[info]{dashboard_url}[/]", "")

    console.print(Padding(table, (1, 0, 0, 0)))


def modal_down(
    volume: Annotated[
        bool,
        typer.Option(
            "--volume/--keep-volume",
            "-v",
            help="Also Delete The Data Volume (Profiles, Media, Database)",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip Confirmation Prompts",
        ),
    ] = False,
) -> None:
    """
    Stops the Modal-Hosted App And Optionally Deletes Its Data Volume

    info: Offload Worker
        The GPU-offload worker is owned by the server and stopped by it
        during shutdown

    info: Volume Deletion
        - The data volume is only deleted when `--volume` is passed. Modal
          refuses to delete a volume mounted on a running app, so the app is
          stopped first

        - When `--volume` is passed, a failed stop (the app is already stopped
          or was never deployed) is only a warning, so the volume can still be
          deleted

        - Deleting it permanently erases the hosted profiles, media, and
          database
    """
    # Get All Variables From The Managed Config File, Falling Back To The
    # Process' Environment For Missing Values
    env = envfile.resolve_managed_config(HOST_CONFIG_FILE)

    # Make Sure MODAL_TOKEN_ID + MODAL_TOKEN_SECRET Are Set
    require_env(Backend.MODAL, HOST_CONFIG_FILE)

    if volume and not yes:
        confirmed = typer.confirm(
            "This Will Permanently Delete The Hosted Profiles, Media, And "
            "Database. Continue?",
            default=False,
        )
        if not confirmed:
            console.print("Aborted", style="muted")
            raise typer.Exit(code=0)

    # The Modal Credentials Are Exported Only For The Teardown Calls, Then The
    # Process Environment Is Restored
    with modal_lifecycle.modal_credentials(env):
        with console.status(
            "[muted]Stopping The Host App[/]",
            spinner="dots",
            spinner_style="accent",
        ):
            stop_error = modal_lifecycle.stop(HOST_APP_NAME)
        if stop_error:
            # A failed stop is only fatal on its own. When also deleting the
            # volume, the app is often already stopped or was never deployed,
            # so warn and carry on so the volume can still be removed
            if not volume:
                raise fail(f"Failed To Stop The Host App  ↦  {stop_error}")
            console.print(
                f"⚠ Could Not Stop The Host App  ↦  {stop_error}",
                style="warning",
            )
        else:
            console.print("✓ Stopped The Host App", style="success")

        if volume:
            try:
                with console.status(
                    "[muted]Deleting The Data Volume[/]",
                    spinner="dots",
                    spinner_style="accent",
                ):
                    modal_lifecycle.delete_volume(DATA_VOLUME_NAME)
                    console.print("✓ Deleted The Data Volume", style="success")

            except ModalError as exc:
                raise fail(f"Failed To Delete Volume  ↦  {exc}") from exc


def modal_download_data(
    destination: Annotated[
        Path,
        typer.Argument(
            help="Local Directory To Download The Hosted Data Into",
        ),
    ] = Path("mirumoji-data"),
) -> None:
    """
    Downloads The Modal-Hosted App's Data Volume To A Local Directory

    Downloads everything in the `mirumoji-data` volume (the media you uploaded
    and the mirumoji database) so it can be backed up or inspected locally.
    Re-downloading into the same directory overwrites the existing copies
    """
    # Get All Variables From The Managed Config File, Falling Back To The
    # Process' Environment For Missing Values
    env = envfile.resolve_managed_config(HOST_CONFIG_FILE)

    # Make Sure MODAL_TOKEN_ID + MODAL_TOKEN_SECRET Are Set
    require_env(Backend.MODAL, HOST_CONFIG_FILE)

    # The Modal Credentials Are Exported Only For The Download Call, Then The
    # Process Environment Is Restored
    with modal_lifecycle.modal_credentials(env):
        try:
            with console.status(
                "[muted]Downloading The Data Volume[/]",
                spinner="dots",
                spinner_style="accent",
            ):
                modal_lifecycle.download_volume(DATA_VOLUME_NAME, destination)
        except ModalError as exc:
            raise fail(f"Failed To Download The Data  ↦  {exc}") from exc

    console.print(
        f"✓ Downloaded The Data Volume To '{destination}'",
        style="success",
    )
