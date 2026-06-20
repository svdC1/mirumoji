"""
Defines the Logs panel

Streams Docker Compose container logs for the whole stack or a single service
"""

import flet as ft

from ...core import lifecycle
from ...core.compose import RESOLVED_COMPOSE_PATH
from ...core.constants import BACKEND_SERVICE, FRONTEND_SERVICE
from ...core.process import StreamHandle
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
    terminal = theme.TerminalSurface(log_view=True)

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

    # Holds the active stream's cancellation token so the Stop button (a
    # separate click event) can terminate the followed `docker compose logs`
    active: dict[str, StreamHandle | None] = {"handle": None}

    def stream(_: ft.Event[ft.Button]) -> None:
        tail, valid = resolve_tail()
        if not valid:
            page.update()
            return

        terminal.clear()
        terminal.set_status("Streaming", "info")
        handle = StreamHandle()
        active["handle"] = handle
        stream_btn.set_loading(True)
        stop_btn.disabled = False
        page.update()

        compose_file = (
            RESOLVED_COMPOSE_PATH if RESOLVED_COMPOSE_PATH.is_file() else None
        )
        service = (
            None
            if service_dd.dropdown.value == _ALL
            else service_dd.dropdown.value
        )
        # Highlight the docker service prefix only when showing every service
        terminal.with_service = service is None

        def settle() -> None:
            """
            Restores the controls once the stream ends, however it ended
            """
            stream_btn.set_loading(False)
            stop_btn.disabled = True
            active["handle"] = None

        def done(_: object) -> None:
            # A stop request ends the stream the same way, so report it as a
            # deliberate stop rather than a natural completion
            if handle.cancelled:
                terminal.set_status("Stopped", "info")
            else:
                terminal.set_status("Done", "success")
            settle()
            page.update()

        def fail(message: str) -> None:
            terminal.set_status("Failed", "danger")
            settle()
            state.notify(message, "danger")
            page.update()

        run_stream(
            page,
            lifecycle.logs(
                service,
                follow=bool(follow_cb.value),
                tail=tail,
                compose_file=compose_file,
                handle=handle,
            ),
            terminal,
            on_done=done,
            on_error=fail,
        )

    def stop(_: ft.Event[ft.Button]) -> None:
        handle = active["handle"]
        if handle is None:
            return
        terminal.set_status("Stopping", "info")
        stop_btn.disabled = True
        page.update()
        handle.cancel()

    stream_btn = theme.PrimaryActionButton(
        "Stream Logs", on_click=stream, icon=ft.Icons.PLAY_ARROW
    )
    stop_btn = theme.SecondaryActionButton(
        "Stop", on_click=stop, icon=ft.Icons.STOP
    )
    stop_btn.disabled = True

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
                    controls=[
                        service_dd,
                        tail_input,
                        follow_cb,
                        stream_btn,
                        stop_btn,
                    ],
                ),
            ),
            terminal,
        ],
    )
