"""
Defines the Flet desktop shell for the Mirumoji GUI

A branded icon sidebar (`NavigationRail`) switches between the launcher's
panels, all driving the same `mirumoji.launcher.core` the CLI uses, themed to
match the frontend's "Sumi & Shu" design
"""

import logging

import flet as ft

from ... import __version__
from ...log import setup_logging
from ...paths import _package_path
from ..core import envfile
from . import theme
from .panels import dashboard, environment, logs, modal_host, settings
from .state import AppState

LOGGER = logging.getLogger(__name__)

_ASSETS = _package_path("launcher", "gui", "assets")

# Sidebar destinations -> panel index
_DESTINATIONS = [
    (ft.Icons.DASHBOARD_OUTLINED, "Dashboard"),
    (ft.Icons.FACT_CHECK_OUTLINED, "Environment"),
    (ft.Icons.SETTINGS_OUTLINED, "Settings"),
    (ft.Icons.ARTICLE_OUTLINED, "Logs"),
    (ft.Icons.CLOUD_OUTLINED, "Modal Host"),
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
            elif index == 3:
                panels[3] = logs.build(page, state)
            else:
                panels[4] = modal_host.build(page, state)
        # A panel is built once and cached, so anything it renders from the
        # managed config (the Dashboard's deployment pills, the Modal Host's
        # mode pills) goes stale as soon as Settings changes it. Re-read it
        # each time the panel is shown
        state.sync_panel(index)
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


def main() -> None:
    """
    Entry point for the `mirumoji gui` command, launches the desktop window
    """
    # The bundled GUI has no console, so a record reaching logging's stderr
    # last-resort handler would raise mid-write (no stderr, or a non-UTF-8
    # console choking on glyphs like `↦`) and stall the UI. `capture_root`
    # attaches a UTF-8 file sink to the root logger, removing that path
    setup_logging(log_file="launcher.log", console=False, capture_root=True)
    LOGGER.info(f"Starting Mirumoji GUI {__version__}")
    ft.run(_page_main, assets_dir=str(_ASSETS))
