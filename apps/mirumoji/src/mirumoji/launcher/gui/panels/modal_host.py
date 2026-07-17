"""
Defines the Modal Host panel

Deploys, inspects, tears down, and backs up the full Mirumoji app hosted on the
user's own Modal account, mirroring the `mirumoji modal` CLI command group. The
offload worker is not managed here since the server owns its lifecycle
"""

import secrets
from pathlib import Path
from typing import TypeAlias, cast

import flet as ft

from .... import modal as modal_lifecycle
from ....exceptions import ModalError
from ...core import checks, envfile
from ...core.constants import (
    CONFIG_ENV_VARS,
    MODAL_HOST_VARS,
    TRANSCRIBE_BACKEND_VAR,
    backend_vars,
)
from ...core.models import Backend
from ...modal.constants import (
    DATA_VOLUME_NAME,
    HOST_APP_NAME,
    HOST_CPU_VAR,
    HOST_MAX_CONCURRENT_REQUESTS_VAR,
    HOST_MEMORY_VAR,
    WEB_FUNCTION_NAME,
    WEB_PASSWORD_ENV,
    WEB_USERNAME,
)
from .. import theme
from ..runner import run_blocking
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


def _resolve_env(state: AppState) -> dict[str, str]:
    """
    Resolves the managed config overlaid with the process environment

    Keeps only the non-empty managed config keys, matching the `modal` CLI
    commands so the GUI injects the same configuration into the deploy

    Args:
        state (AppState): The shared GUI state (holds the config path)

    Returns:
        The resolved non-empty managed configuration values
    """
    merged = envfile.overlay_environ(
        envfile.read(state.env_path), _CONFIG_NAMES
    )
    return {name: merged[name] for name in _CONFIG_NAMES if merged.get(name)}


def _host_config(env: dict[str, str]) -> dict[str, str]:
    """
    Resolves the host reservations (CPU, memory, concurrency) with their
    managed-config defaults, matching the `mirumoji modal deploy` command

    Args:
        env (dict[str, str]): The resolved managed configuration values

    Returns:
        Every defaulted host variable, so each sizing key is present
    """
    return {
        var.name: env.get(var.name) or var.default
        for var in MODAL_HOST_VARS
        if var.default
    }


def _missing_tokens(env: dict[str, str]) -> list[str]:
    """
    Returns the required Modal credentials that are not configured

    Args:
        env (dict[str, str]): The resolved managed configuration values

    Returns:
        The missing required Modal variable names, empty when all are set
    """
    missing = envfile.missing_required(backend_vars(Backend.MODAL), env)
    return [var.name for var in missing]


def build(page: ft.Page, state: AppState) -> ft.Control:
    """
    Builds the Modal Host panel

    Args:
        page (ft.Page): The owning page
        state (AppState): The shared GUI state

    Returns:
        The panel's root control
    """
    terminal = theme.TerminalSurface()
    generate_cb = ft.Checkbox(
        label="Generate A Password If One Is Not Set", value=False
    )
    volume_cb = ft.Checkbox(label="Also Delete The Data Volume", value=False)

    # The reservations a deploy would use, resolved with their managed-config
    # defaults and refreshed on every action so they never go stale
    cpu_pill = theme.StatusPill("", "info")
    memory_pill = theme.StatusPill("", "info")
    concurrency_pill = theme.StatusPill("", "info")

    def _config_row(label: str, pill: ft.Container) -> ft.Row:
        """
        Builds a labelled reservation pill row

        Args:
            label (str): The reservation's label
            pill (ft.Container): The `StatusPill` holding the reservation value

        Returns:
            The label + pill row
        """
        return ft.Row(
            [
                ft.Text(label, theme_style=ft.TextThemeStyle.LABEL_SMALL),
                pill,
            ],
            spacing=10,
        )

    def _refresh_config() -> None:
        """
        Re-reads the resolved host reservations into the config pills
        """
        host_config = _host_config(_resolve_env(state))
        cast(ft.Text, cpu_pill.content).value = host_config[HOST_CPU_VAR]
        cast(ft.Text, memory_pill.content).value = host_config[HOST_MEMORY_VAR]
        cast(ft.Text, concurrency_pill.content).value = host_config[
            HOST_MAX_CONCURRENT_REQUESTS_VAR
        ]

    _refresh_config()

    def _ready() -> dict[str, str] | None:
        """
        Resolves the config and verifies the Modal credentials are present

        Returns:
            The resolved env when ready, or `None` after notifying the user
        """
        env = _resolve_env(state)
        missing = _missing_tokens(env)
        if missing:
            state.notify(
                f"Set {', '.join(missing)} In Settings First", "danger"
            )
            return None
        return env

    def on_deploy(_: ft.Event[ft.Button]) -> None:
        env = _ready()
        if env is None:
            return
        password = env.get(WEB_PASSWORD_ENV)
        if not password:
            if not generate_cb.value:
                state.notify(
                    "No Web Password  ↦  Set MIRUMOJI_WEB_PASSWORD In "
                    "Settings Or Enable Password Generation",
                    "danger",
                )
                return
            password = secrets.token_urlsafe(12)
            envfile.set_value(state.env_path, WEB_PASSWORD_ENV, password)
        env[WEB_PASSWORD_ENV] = password
        # The host offloads transcription to the GPU worker instead of needing
        # a GPU on the always-warm web tier
        env[TRANSCRIBE_BACKEND_VAR] = Backend.MODAL.value
        host_config = _host_config(env)
        begin("Deploying The Host App", deploy_btn)

        def do() -> dict[str, str | None]:
            # Imported here, not at module top, so importing the `modal` SDK
            # (which flips the Windows asyncio policy to a selector loop that
            # cannot spawn subprocesses) is deferred past the GUI's proactor
            # loop startup. The `modal_lifecycle` helpers import it lazily too
            from ...modal import host as host_deploy

            version = envfile.resolve_version(state.env_path)
            checks.require_published_version(version)
            with modal_lifecycle.modal_credentials(env):
                host_deploy.ensure_host_deployed(
                    env, host_config, version=version
                )
                return {
                    "url": modal_lifecycle.web_url(
                        HOST_APP_NAME, WEB_FUNCTION_NAME
                    ),
                    "dashboard": modal_lifecycle.dashboard_url(HOST_APP_NAME),
                    "password": password,
                }

        def deployed(result: dict[str, str | None]) -> None:
            url = result["url"]
            if url:
                terminal.append_link("URL", url)
            else:
                terminal.append_log("URL  ↦  Run Status")
            terminal.append_log(f"Username  ↦  {WEB_USERNAME}")
            terminal.append_log(f"Password  ↦  {result['password']}")
            dashboard = result["dashboard"]
            if dashboard:
                terminal.append_link("Dashboard", dashboard)
            done("Mirumoji Is Hosted")

        run_blocking(page, do, deployed, on_error=lambda e: fail(str(e)))

    def on_status(_: ft.Event[ft.Button]) -> None:
        env = _ready()
        if env is None:
            return
        begin("Querying Status", status_btn)

        def do() -> dict[str, object]:
            with modal_lifecycle.modal_credentials(env):
                tags = modal_lifecycle.deployed_tags(HOST_APP_NAME)
                return {
                    "deployed": tags is not None,
                    "version": (tags or {}).get(
                        modal_lifecycle.VERSION_KEY, "Unknown"
                    ),
                    "volume": modal_lifecycle.volume_exists(DATA_VOLUME_NAME),
                    "url": modal_lifecycle.web_url(
                        HOST_APP_NAME, WEB_FUNCTION_NAME
                    ),
                    "dashboard": modal_lifecycle.dashboard_url(HOST_APP_NAME),
                }

        def render(s: dict[str, object]) -> None:
            host_state = (
                f"Deployed (v{s['version']})"
                if s["deployed"]
                else "Not Deployed"
            )
            volume_state = "Present" if s["volume"] else "Absent"
            terminal.append_log(f"Host App  ↦  {host_state}")
            terminal.append_log(f"Data Volume  ↦  {volume_state}")
            url = s["url"]
            if isinstance(url, str):
                terminal.append_link("URL", url)
            dashboard = s["dashboard"]
            if isinstance(dashboard, str):
                terminal.append_link("Dashboard", dashboard)
            done("Status Updated")

        run_blocking(page, do, render, on_error=lambda e: fail(str(e)))

    def _run_down(env: dict[str, str], delete_volume: bool) -> None:
        begin("Stopping The Host App", down_btn)

        def do() -> bool:
            with modal_lifecycle.modal_credentials(env):
                error = modal_lifecycle.stop(HOST_APP_NAME)
                # A failed stop is only fatal on its own. When deleting the
                # volume too, the app is often already stopped, so proceed
                if error and not delete_volume:
                    raise ModalError(error)
                if delete_volume:
                    modal_lifecycle.delete_volume(DATA_VOLUME_NAME)
                return bool(error)

        def stopped(stop_failed: bool) -> None:
            if stop_failed:
                terminal.append_log(
                    "Could Not Stop The Host App (It May Not Be Running)"
                )
            else:
                terminal.append_log("Stopped The Host App")
            if delete_volume:
                terminal.append_log("Deleted The Data Volume")
            done("Stopped")

        run_blocking(page, do, stopped, on_error=lambda e: fail(str(e)))

    def on_down(_: ft.Event[ft.Button]) -> None:
        env = _ready()
        if env is None:
            return
        if not volume_cb.value:
            _run_down(env, False)
            return

        # Deleting the volume is destructive, so confirm first
        def confirm() -> None:
            page.pop_dialog()
            _run_down(env, True)

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Delete The Data Volume"),
                content=ft.Text(
                    "This Permanently Erases The Hosted Profiles, Media, And "
                    "Database. Continue?",
                    color=theme.INK_MUTED,
                ),
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=lambda _: page.pop_dialog()
                    ),
                    ft.TextButton(
                        "Delete Everything", on_click=lambda _: confirm()
                    ),
                ],
            )
        )

    async def on_download(_: ft.Event[ft.Button]) -> None:
        env = _ready()
        if env is None:
            return
        picked = await ft.FilePicker().get_directory_path(
            dialog_title="Choose A Folder To Download The Data Into",
        )
        if not picked:
            return
        destination = Path(picked)
        begin("Downloading The Data Volume", download_btn)

        def do() -> Path:
            with modal_lifecycle.modal_credentials(env):
                modal_lifecycle.download_volume(DATA_VOLUME_NAME, destination)
            return destination

        run_blocking(
            page,
            do,
            lambda dest: done(f"Downloaded To {dest}"),
            on_error=lambda e: fail(str(e)),
        )

    deploy_btn = theme.PrimaryActionButton(
        "Deploy",
        on_click=lambda e: on_deploy(e),
        icon=ft.Icons.CLOUD_UPLOAD_OUTLINED,
    )
    status_btn = theme.SecondaryActionButton(
        "Status",
        on_click=lambda e: on_status(e),
        icon=ft.Icons.INFO_OUTLINE,
    )
    down_btn = theme.SecondaryActionButton(
        "Down",
        on_click=lambda e: on_down(e),
        icon=ft.Icons.STOP,
    )
    download_btn = theme.SecondaryActionButton(
        "Download Data",
        on_click=on_download,
        icon=ft.Icons.DOWNLOAD,
    )

    actions: list[_CUSTOM_BUTTON] = [
        deploy_btn,
        status_btn,
        down_btn,
        download_btn,
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
        _refresh_config()
        lock_buttons(active_button)
        state.set_busy(True)

    def done(message: str) -> None:
        """
        Marks the current action as succeeded, unlocks the UI, and toasts

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

        Args:
            message (str): The error message shown as a toast
        """
        terminal.set_status("Failed", "danger")
        unlock_buttons()
        state.set_busy(False)
        state.notify(message, "danger")

    return ft.Column(
        expand=True,
        spacing=theme.GAP,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text(
                "Modal Host", theme_style=ft.TextThemeStyle.HEADLINE_LARGE
            ),
            ft.Text(
                "Deploy And Manage The Full App On Your Modal Account",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            ),
            theme.Section(
                "Active Configuration",
                ft.Row(
                    spacing=36,
                    wrap=False,
                    controls=[
                        _config_row("CPU Cores", cpu_pill),
                        _config_row("Memory (MiB)", memory_pill),
                        _config_row("Max Requests", concurrency_pill),
                    ],
                ),
            ),
            ft.Row([*actions], spacing=10, wrap=True),
            ft.Row([generate_cb, volume_cb], spacing=24, wrap=False),
            terminal,
        ],
    )
