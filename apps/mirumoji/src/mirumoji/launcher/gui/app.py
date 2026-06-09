"""
Defines the Flet desktop shell for the Mirumoji GUI

A branded icon sidebar (`NavigationRail`) switches between the launcher's
panels, all driving the same `mirumoji.launcher.core` the CLI uses, themed to
match the frontend's "Sumi & Shu" design
"""

import logging

import flet as ft

from ... import __version__
from ...paths import HOST_LOG_PATH, _package_path
from ..core import envfile
from . import theme
from .panels import dashboard, environment, logs, settings
from .state import AppState

LOGGER = logging.getLogger(__name__)

_ASSETS = _package_path("launcher", "gui", "assets")

# Sidebar destinations -> panel index
_DESTINATIONS = [
    (ft.Icons.DASHBOARD_OUTLINED, "Dashboard"),
    (ft.Icons.FACT_CHECK_OUTLINED, "Environment"),
    (ft.Icons.SETTINGS_OUTLINED, "Settings"),
    (ft.Icons.ARTICLE_OUTLINED, "Logs"),
]


def _brand() -> ft.Container:
    """
    Builds the sidebar brand mark

    Returns:
        The configured `Container` control
    """
    seal = ft.Container(
        width=42,
        height=42,
        bgcolor=theme.SHU,
        border_radius=11,
        alignment=ft.Alignment.CENTER,
        content=ft.Text(
            "見",
            size=22,
            color=theme.INK,
            font_family=theme.DISPLAY,
            weight=ft.FontWeight.BOLD,
        ),
    )
    return ft.Container(
        content=seal,
        padding=ft.Padding.only(top=20, bottom=12),
    )


def _page_main(page: ft.Page) -> None:
    """
    Builds the application window and wires sidebar navigation

    Args:
        page (ft.Page): The Flet page provided by the runtime
    """
    page.title = "Mirumoji"
    page.bgcolor = theme.BG
    page.padding = 0
    page.fonts = theme.FONT_FILES
    page.theme = theme.MirumojiTheme()
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1120
    page.window.height = 740
    page.window.min_width = 940
    page.window.min_height = 620

    def notify_callback(message: str, kind: str = "info") -> None:
        page.show_dialog(theme.NotificationBar(message, kind))

    def set_busy_callback(busy: bool) -> None:
        # Lock navigation while an action runs so that the user can't,
        # for example, switch the backend in Settings part-way through a
        # build
        state.busy = busy
        rail.disabled = busy
        page.update()

    state = AppState(notify=notify_callback, set_busy=set_busy_callback)
    # Adopt the persisted backend / image-source choice from the managed config
    state.load_deployment(envfile.read(state.env_path))

    panels: dict[int, ft.Control] = {}

    body = ft.Container(expand=True, padding=32, bgcolor=theme.BG)

    def show(index: int) -> None:
        # Build each panel once, then cache it
        if index not in panels:
            if index == 0:
                panels[0] = dashboard.build(page, state)
            elif index == 1:
                panels[1] = environment.build(page, state)
            elif index == 2:
                panels[2] = settings.build(page, state)
            else:
                panels[3] = logs.build(page, state)
        # The Dashboard pills reflect the persisted deployment choice, which
        # Settings can change. Re-read it from the config each time it's shown
        if index == 0 and state.sync_dashboard is not None:
            state.sync_dashboard()
        body.content = panels[index]
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=theme.SURFACE,
        indicator_color=ft.Colors.with_opacity(0.2, theme.SHU),
        min_width=104,
        group_alignment=-0.85,
        leading=_brand(),
        trailing=ft.Container(
            expand=True,
            alignment=ft.Alignment.BOTTOM_CENTER,
            padding=ft.Padding.only(bottom=16),
            content=ft.Text(f"v{__version__}", size=11, color=theme.INK_FAINT),
        ),
        destinations=[
            ft.NavigationRailDestination(
                icon=icon,
                label=label,
                selected_icon=icon,
            )
            for icon, label in _DESTINATIONS
        ],
        on_change=lambda e: show(e.control.selected_index),
    )

    page.add(
        ft.Row(
            expand=True,
            spacing=0,
            controls=[
                rail,
                ft.VerticalDivider(width=1, color=theme.BORDER),
                body,
            ],
        )
    )

    # Default landing panel
    show(0)
    # Keep a reference so the state survives for later panels
    page.data = state


def _configure_logging() -> None:
    """
    Routes launcher logs to a UTF-8 `launcher.log` file

    The bundled GUI has no console, so `sys.stderr` is unavailable. With no
    handler configured, a `WARNING`+ record falls back to logging's stderr
    last-resort handler, which then raises while writing (no stderr, or a
    non-UTF-8 console choking on glyphs like `↦` in error messages). That
    exception kills the worker thread before its `on_error` callback runs,
    leaving the UI stuck. Attaching a real UTF-8 file handler removes the
    last-resort path entirely and keeps a log for debugging bundled runs
    """
    try:
        HOST_LOG_PATH.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = logging.FileHandler(
            HOST_LOG_PATH / "launcher.log", encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
            )
        )
    except OSError:
        # If the log dir isn't writable, still attach a no-op handler so
        # logging never reaches the broken stderr last-resort
        handler = logging.NullHandler()

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def main() -> None:
    """
    Entry point for the `mirumoji gui` command — launches the desktop window
    """
    _configure_logging()
    LOGGER.info(f"Starting Mirumoji GUI {__version__}")
    ft.run(_page_main, assets_dir=str(_ASSETS))
