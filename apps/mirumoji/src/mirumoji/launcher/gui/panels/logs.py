"""
Defines the Logs panel

Streams Docker Compose container logs for the whole stack or a single service,
or the Modal-hosted app's logs when the host is deployed
"""

from collections.abc import Generator

import flet as ft

from ....exceptions import ModalError
from ....paths import HOST_CONFIG_FILE
from ...core import envfile, lifecycle, process
from ...core.compose import RESOLVED_COMPOSE_PATH
from ...core.constants import BACKEND_SERVICE, FRONTEND_SERVICE
from ...core.process import StreamHandle
from ...modal import lifecycle as modal_lifecycle
from ...modal.constants import HOST_APP_NAME, MODAL_LOGS_MAX_TAIL
from .. import theme
from ..runner import run_stream
from ..state import AppState

_ALL = "all"

_DOCKER_SOURCE = "Docker"
"""
Log source label for the local Docker Compose stack
"""

_MODAL_SOURCE = "Modal"
"""
Log source label for the Modal-hosted app
"""


def _modal_logs(
    tail: int | None,
    follow: bool,
    handle: StreamHandle,
) -> Generator[str, None, None]:
    """
    Streams the Modal-hosted app's logs

    info: Credential Lifetime
        `modal_credentials` mutates `os.environ` for the duration of its block,
        and the caller consumes this generator lazily on a worker thread. The
        block is therefore opened inside the generator, so the credentials are
        still in place when the process is actually spawned

    Args:
        tail (int | None): How many recent entries to fetch, or `None` for the
            default
        follow (bool): Live-follow instead of fetching recent entries
        handle (StreamHandle): Cancellation token for the followed stream

    Yields:
        The log lines

    Raises:
        ModalError: If credentials are missing or the logs cannot be read
    """
    env = envfile.resolve_managed_config(HOST_CONFIG_FILE)
    entries = min(tail or 100, MODAL_LOGS_MAX_TAIL)
    with modal_lifecycle.modal_credentials(env):
        if not follow:
            output = modal_lifecycle.fetch_app_logs(HOST_APP_NAME, entries)
            yield from (output.rstrip("\n").splitlines() or ["No Log Entries"])
            return
        if not modal_lifecycle.modal_cli_available():
            raise ModalError(
                "Following Modal Logs Needs A Python Interpreter On This "
                "Machine. Untick Follow To Fetch Recent Entries Instead"
            )
        # `check=False` because cancelling a followed stream kills the process,
        # which then exits non-zero through no fault of its own
        yield from process.stream(
            modal_lifecycle.app_logs_command(
                HOST_APP_NAME, follow=True, tail=entries
            ),
            check=False,
            handle=handle,
        )


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

    def on_source_select(_: ft.Event[ft.Dropdown]) -> None:
        # The Service picker only means anything for the compose stack, so it
        # is disabled rather than silently ignored when reading Modal logs
        service_dd.disabled = source_dd.dropdown.value == _MODAL_SOURCE
        page.update()

    source_dd = theme.SettingsDropdown(
        "Source",
        _DOCKER_SOURCE,
        [_DOCKER_SOURCE, _MODAL_SOURCE],
        width=180,
    )
    source_dd.dropdown.on_select = on_source_select

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

        on_modal = source_dd.dropdown.value == _MODAL_SOURCE
        compose_file = (
            RESOLVED_COMPOSE_PATH if RESOLVED_COMPOSE_PATH.is_file() else None
        )
        service = (
            None
            if service_dd.dropdown.value == _ALL
            else service_dd.dropdown.value
        )
        # Highlight the docker service prefix only when showing every service.
        # Modal's lines carry no service prefix at all
        terminal.with_service = service is None and not on_modal

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

        gen = (
            _modal_logs(tail, bool(follow_cb.value), handle)
            if on_modal
            else lifecycle.logs(
                service,
                follow=bool(follow_cb.value),
                tail=tail,
                compose_file=compose_file,
                handle=handle,
            )
        )
        run_stream(page, gen, terminal, on_done=done, on_error=fail)

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
                "Container Logs From The Running Docker Compose Application, "
                "Or The Modal-Hosted App",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            ),
            theme.Section(
                "Controls",
                ft.Row(
                    spacing=16,
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[
                        source_dd,
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
