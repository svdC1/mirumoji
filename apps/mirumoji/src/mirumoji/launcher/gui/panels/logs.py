"""
Defines the Logs panel

Streams Docker Compose container logs for the whole stack or a single service
"""

import flet as ft

from ...core import lifecycle
from ...core.compose import RESOLVED_COMPOSE_PATH
from ...core.constants import BACKEND_SERVICE, FRONTEND_SERVICE
from .. import theme
from ..runner import run_stream
from ..state import AppState

_ALL = "all"


def build(page: ft.Page, state: AppState) -> ft.Control:
    """
    Builds the Logs panel

    Args:
        page (ft.Page): The owning page
        state (AppState): The shared GUI state (used for toast notifications)

    Returns:
        The panel's root control
    """
    terminal = theme.TerminalSurface()

    service_dd = theme.SettingsDropdown(
        "Service",
        _ALL,
        [_ALL, FRONTEND_SERVICE, BACKEND_SERVICE],
        width=220,
    )
    tail_input = theme.SettingsInput("Tail Lines", "200")
    tail_input.width = 160
    follow_cb = ft.Checkbox(label="Follow", value=False)

    def resolve_tail() -> tuple[int | None, bool]:
        """
        Parses the Tail-Lines field, flagging non-integer input inline

        Returns:
            The tail count (`None` when blank) and whether the input is valid
        """
        raw = (tail_input.field.value or "").strip()
        if not raw:
            tail_input.field.error = None
            return None, True
        try:
            tail = int(raw)
        except ValueError:
            tail_input.field.error = "Must Be A Number"
            return None, False
        tail_input.field.error = None
        return tail, True

    def stream(_: ft.Event[ft.Button]) -> None:
        tail, valid = resolve_tail()
        if not valid:
            page.update()
            return

        terminal.clear()
        terminal.set_status("Streaming", "info")
        stream_btn.set_loading(True)
        page.update()

        compose_file = (
            RESOLVED_COMPOSE_PATH if RESOLVED_COMPOSE_PATH.is_file() else None
        )
        service = (
            None
            if service_dd.dropdown.value == _ALL
            else service_dd.dropdown.value
        )

        def done(_: object) -> None:
            terminal.set_status("Done", "success")
            stream_btn.set_loading(False)
            page.update()

        def fail(message: str) -> None:
            terminal.set_status("Failed", "danger")
            stream_btn.set_loading(False)
            state.notify(message, "danger")
            page.update()

        run_stream(
            page,
            lifecycle.logs(
                service,
                follow=bool(follow_cb.value),
                tail=tail,
                compose_file=compose_file,
            ),
            terminal,
            on_done=done,
            on_error=fail,
        )

    stream_btn = theme.PrimaryActionButton(
        "Stream Logs", on_click=stream, icon=ft.Icons.PLAY_ARROW
    )

    return ft.Column(
        expand=True,
        spacing=theme.GAP,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text("Logs", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
            ft.Text(
                "Container Logs From The Running Docker Compose Application",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            ),
            theme.Section(
                "Controls",
                ft.Row(
                    spacing=16,
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[service_dd, tail_input, follow_cb, stream_btn],
                ),
            ),
            terminal,
        ],
    )
