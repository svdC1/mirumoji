"""
Defines the Dashboard Panel

Exposes buttons to run the Docker Compose lifecycle actions (up, down, pull,
build, status) and a terminal-like surface to display their live streamed
output
"""

import os
from collections.abc import Generator
from typing import TypeAlias, cast

import flet as ft

from ...core import compose as compose_core
from ...core import envfile, lifecycle, repo
from ...core.compose import RESOLVED_COMPOSE_PATH
from ...core.constants import (
    CONFIG_ENV_VARS,
    HOST_LAN_IP_VAR,
    TRANSCRIBE_BACKEND_VAR,
    backend_vars,
)
from ...core.host import get_host_lan_ip
from ...core.models import ImageSource, ServiceStatus
from ...core.status import parse_status
from .. import theme
from ..runner import run_blocking, run_stream
from ..state import AppState

# --- Types ---

_CUSTOM_BUTTON: TypeAlias = (
    theme.PrimaryActionButton | theme.SecondaryActionButton
)

# --- Constants ---

_CONFIG_NAMES = [v.name for v in CONFIG_ENV_VARS]
"""
List containing the names of all environment variables managed by the launcher
"""

# --- Helpers ---


def _status_lines(services: list[ServiceStatus]) -> list[str]:
    """
    Renders parsed service statuses as aligned monospace table rows

    Args:
        services (list[ServiceStatus]): The parsed compose service statuses

    Returns:
        A header row followed by one row per service, padded into columns for
        the terminal surface
    """
    headers = ("SERVICE", "STATE", "STATUS", "PORTS")
    rows = [(s.service, s.state, s.status, s.ports or "-") for s in services]
    widths = [
        max(len(headers[col]), *(len(row[col]) for row in rows))
        for col in range(len(headers))
    ]

    def render(cells: tuple[str, ...]) -> str:
        padded = (cell.ljust(widths[col]) for col, cell in enumerate(cells))
        return "  ".join(padded).rstrip()

    return [render(headers), *(render(row) for row in rows)]


def _missing_required(state: AppState) -> list[str]:
    """
    Returns the names of required variables missing for the current backend

    The variable values follow the same order of precedence as defined in the
    CLI's `up` command. The managed config is the source of truth, with the
    process' environment as a fallback (Compose applies the same precedence),
    so that a shell-provided value is not reported as missing

    Args:
        state (AppState): The shared GUI state (backend + config path)

    Returns:
        The missing required variable names, empty when all are configured
    """
    values = envfile.overlay_environ(
        envfile.read(state.env_path), _CONFIG_NAMES
    )
    missing = envfile.missing_required(backend_vars(state.backend), values)
    return [var.name for var in missing]


def _up_flow(state: AppState) -> Generator[str, None, str]:
    """
    Composite flow mirroring `mirumoji up`

    Args:
        state (AppState): The chosen backend / source / env file

    Yields:
        Output lines from each underlying step

    Returns:
        The resolved host LAN IP (for the success message)
    """
    ip = get_host_lan_ip()
    os.environ[HOST_LAN_IP_VAR] = ip
    os.environ[TRANSCRIBE_BACKEND_VAR] = state.backend.value
    if state.source is ImageSource.BUILD:
        repo_path = yield from repo.ensure_repo()
        yield from lifecycle.build_images(repo_path, state.backend)
    compose_file = compose_core.write_compose(state.backend, state.source)
    if state.source is ImageSource.PULL:
        yield from lifecycle.pull(compose_file, env_file=state.env_path)
    yield from lifecycle.up(compose_file, env_file=state.env_path)
    return ip


def _build_flow(state: AppState) -> Generator[str, None, None]:
    """
    Composite flow mirroring `mirumoji build`

    Args:
        state (AppState): The chosen backend

    Yields:
        Output lines from the checkout + image builds
    """
    repo_path = yield from repo.ensure_repo()
    yield from lifecycle.build_images(repo_path, state.backend)


def _pull_flow(state: AppState) -> Generator[str, None, int]:
    """
    Composite flow mirroring `mirumoji pull`

    Args:
        state (AppState): The chosen backend

    Yields:
        Output lines from the pull

    Returns:
        The compose exit code
    """
    compose_file = compose_core.write_compose(state.backend, ImageSource.PULL)
    return (yield from lifecycle.pull(compose_file, env_file=state.env_path))


def build(page: ft.Page, state: AppState) -> ft.Control:
    """
    Builds the Dashboard panel

    Args:
        page (ft.Page): The owning page
        state (AppState): The shared GUI state

    Returns:
        The panel's root control
    """

    terminal = theme.TerminalSurface()
    volumes_cb = ft.Checkbox(label="Also Delete Data Volumes", value=False)

    def on_up(_: ft.Event[ft.Button]) -> None:
        missing = _missing_required(state)
        if missing:
            state.notify(
                f"Set {', '.join(missing)} In Settings Before Starting",
                "danger",
            )
            return
        begin("Starting Mirumoji", up_btn)

        def up_done(ip: str) -> None:
            terminal.append_link("Local", "https://localhost")
            terminal.append_link("LAN", f"https://{ip}")
            terminal.append_log(
                f"Trust Other Devices ↦ Install "
                f"http://{ip}/mirumoji-ca.crt Once Per Device "
                f"(Enables The Installable PWA)"
            )
            done("Mirumoji Is Running")

        run_stream(
            page,
            _up_flow(state),
            terminal,
            on_done=up_done,
            on_error=fail,
        )

    def on_pull(_: ft.Event[ft.Button]) -> None:
        begin("Pulling Images", pull_btn)
        run_stream(
            page,
            _pull_flow(state),
            terminal,
            on_done=lambda _: done("Images Pulled"),
            on_error=fail,
        )

    def on_build(_: ft.Event[ft.Button]) -> None:
        begin("Building Images", build_btn)
        run_stream(
            page,
            _build_flow(state),
            terminal,
            on_done=lambda _: done("Images Built"),
            on_error=fail,
        )

    def on_down(_: ft.Event[ft.Button]) -> None:
        begin("Stopping", down_btn)
        compose_file = (
            RESOLVED_COMPOSE_PATH if RESOLVED_COMPOSE_PATH.is_file() else None
        )
        run_stream(
            page,
            lifecycle.down(
                volumes=bool(volumes_cb.value), compose_file=compose_file
            ),
            terminal,
            on_done=lambda _: done("Stopped"),
            on_error=fail,
        )

    def on_status(_: ft.Event[ft.Button]) -> None:
        begin("Querying Status", status_btn)

        def render(out: str) -> None:
            services = parse_status(out)
            if not services:
                done("No Running Services")
                return
            for line in _status_lines(services):
                terminal.append_log(line)
            done("Status Updated")

        run_blocking(
            page,
            lifecycle.ps,
            render,
            on_error=lambda e: fail(str(e)),
        )

    up_btn = theme.PrimaryActionButton(
        "Up",
        on_click=lambda e: on_up(e),
        icon=ft.Icons.PLAY_ARROW,
    )

    down_btn = theme.SecondaryActionButton(
        "Down",
        on_click=lambda e: on_down(e),
        icon=ft.Icons.STOP,
    )

    pull_btn = theme.SecondaryActionButton(
        "Pull",
        on_click=lambda e: on_pull(e),
        icon=ft.Icons.DOWNLOAD,
    )

    build_btn = theme.SecondaryActionButton(
        "Build",
        on_click=lambda e: on_build(e),
        icon=ft.Icons.BUILD,
    )
    status_btn = theme.SecondaryActionButton(
        "Status",
        on_click=lambda e: on_status(e),
        icon=ft.Icons.INFO_OUTLINE,
    )

    actions: list[_CUSTOM_BUTTON] = [
        up_btn,
        down_btn,
        pull_btn,
        build_btn,
        status_btn,
    ]

    def lock_buttons(active_button: _CUSTOM_BUTTON) -> None:
        """
        Disables every action button, showing a spinner on the active one

        Args:
            active_button (_CUSTOM_BUTTON): The button that ran the action
        """
        for btn in actions:
            if btn is active_button:
                btn.set_loading(True)
            else:
                btn.disabled = True
        page.update()

    def unlock_buttons() -> None:
        """
        Restores every action button to its idle state
        """
        for btn in actions:
            btn.set_loading(False)
        page.update()

    def begin(label: str, active_button: _CUSTOM_BUTTON) -> None:
        """
        Starts an action: clears the terminal, shows progress, locks the UI

        Args:
            label (str): The in-progress status label
            active_button (_CUSTOM_BUTTON): The button that ran the action
        """
        terminal.clear()
        terminal.set_status(label, "info")
        lock_buttons(active_button)
        state.set_busy(True)

    def done(message: str) -> None:
        """
        Marks the current action as succeeded, unlocks the UI, and toasts

        The outcome persists in the terminal header (like the Logs panel) while
        the toast is the momentary announcement

        Args:
            message (str): The success message shown in the header + as a toast
        """
        terminal.set_status(message, "success")
        unlock_buttons()
        state.set_busy(False)
        state.notify(message, "success")

    def fail(message: str) -> None:
        """
        Marks the action failed, unlocks the UI, and toasts the error

        The header persists a "Failed" status while the toast carries the full
        error message

        Args:
            message (str): The error message shown as a toast
        """
        terminal.set_status("Failed", "danger")
        unlock_buttons()
        state.set_busy(False)
        state.notify(message, "danger")

    # The pills mirror the persisted deployment choice. The panel is cached, so
    # the page re-syncs them from the config whenever the Dashboard is shown
    backend_pill = theme.StatusPill(state.backend.value, "info")
    source_pill = theme.StatusPill(state.source.value, "info")

    def sync_dashboard() -> None:
        """
        Re-reads the persisted deployment choice and updates the config pills
        """
        state.load_deployment(envfile.read(state.env_path))
        cast(ft.Text, backend_pill.content).value = state.backend.value
        cast(ft.Text, source_pill.content).value = state.source.value

    state.sync_dashboard = sync_dashboard

    return ft.Column(
        expand=True,
        spacing=theme.GAP,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text("Dashboard", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
            ft.Text(
                "Build, Run, And Inspect The Mirumoji Docker Application",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            ),
            theme.Section(
                "Active Configuration",
                ft.Row(
                    spacing=36,
                    controls=[
                        ft.Row(
                            [
                                ft.Text(
                                    "Backend",
                                    theme_style=ft.TextThemeStyle.LABEL_SMALL,
                                ),
                                backend_pill,
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    "Source",
                                    theme_style=ft.TextThemeStyle.LABEL_SMALL,
                                ),
                                source_pill,
                            ],
                            spacing=10,
                        ),
                    ],
                ),
            ),
            ft.Row([*actions], spacing=10, wrap=True),
            ft.Row([volumes_cb], spacing=16),
            terminal,
        ],
    )
