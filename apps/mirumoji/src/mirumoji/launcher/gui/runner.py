"""
Defines helpers for running the blocking external command calls defined in the
launcher's core (Environment Checks, Docker Lifecycle Commands, ...) in a
separate OS thread tied to the main page

The core's checks and lifecycle operations block (subprocess calls), so they
are run via `page.run_thread` to keep the Flet UI responsive. Results are
delivered back through callbacks that update controls
"""

import asyncio
import logging
import subprocess
import threading
from collections.abc import Callable, Generator
from typing import Any, TypeVar

import flet as ft

from ..core.errors import LauncherError
from .theme import TerminalSurface

LOGGER = logging.getLogger(__name__)

_T = TypeVar("_T")

# Coalesce a burst of streamed lines into one repaint at most this often, so a
# chatty subprocess doesn't flood the event loop with per-line updates
_FLUSH_INTERVAL_S = 0.1


def run_blocking(
    page: ft.Page,
    fn: Callable[[], _T],
    on_done: Callable[[_T], None],
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    """
    Runs a blocking function in a background thread

    The `on_done` / `on_error` callbacks mutate UI controls, so they are
    marshalled back onto the page's event loop with `page.run_task` instead of
    running on the worker thread. Touching Flet controls off the event loop
    races the loop's own diffing and corrupts the control tree

    Args:
        page (ft.Page): The page used to schedule the worker thread
        fn (Callable[[], _T]): The blocking function to run
        on_done (Callable[[_T], None]): Called with the result on success
        on_error (Callable[[Exception], None] | None): Called on failures
    """

    async def deliver_done(result: _T) -> None:
        """
        Runs the success callback on the event loop
        """
        on_done(result)

    async def deliver_error(exc: Exception) -> None:
        """
        Runs the error callback on the event loop
        """
        if on_error is not None:
            on_error(exc)

    def worker() -> None:
        """
        Runs the blocking `fn` function and delivers the result / exception
        back to the event loop
        """
        try:
            result = fn()
        except Exception as exc:
            LOGGER.exception("GUI Background Task Failed")
            page.run_task(deliver_error, exc)
            return
        page.run_task(deliver_done, result)

    page.run_thread(worker)


def run_stream(
    page: ft.Page,
    gen: Generator[str, None, Any],
    terminal: TerminalSurface,
    *,
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[str], None] | None = None,
) -> None:
    """
    Runs a `launcher.core` generator on a background thread and streams its
    yielded output into a `TerminalSurface`

    info: Behaviour
        - Yielded lines are buffered and flushed to `terminal` in batches on
          the page's event loop, at most once per `_FLUSH_INTERVAL_S`, so a
          busy stream doesn't repaint the page per line

        - All UI work (appending lines, the `on_done` / `on_error` callbacks)
          runs on the event loop via `page.run_task`

        - The worker thread never touches Flet controls directly, which would
          race the loop's diff and corrupt the control tree

        - The generator's return value is delivered to `on_done`

        - launcher / process errors are mapped to a message for `on_error`

    Args:
        page (ft.Page): The page used to schedule the worker thread
        gen (Generator[str, None, Any]): The `launcher.core` generator to run
        terminal (TerminalSurface): The surface in which to append output lines
        on_done (Callable[[Any], None] | None): Called with the return value
        on_error (Callable[[str], None] | None): Called with an error message
    """

    buffer: list[str] = []
    lock = threading.Lock()
    # Single-slot flag so overlapping emits coalesce into one scheduled flush
    flush_pending = False

    def drain() -> list[str]:
        """Atomically takes and clears the buffered lines"""
        with lock:
            lines = buffer.copy()
            buffer.clear()
            return lines

    def render(lines: list[str]) -> None:
        """Appends `lines` to the terminal and repaints once (event loop)"""
        if not lines:
            return
        for line in lines:
            terminal.append_log(line)
        page.update()

    async def flush() -> None:
        """Coalesces a burst of lines into a single batched repaint"""
        nonlocal flush_pending
        await asyncio.sleep(_FLUSH_INTERVAL_S)
        with lock:
            flush_pending = False
        render(drain())

    async def finish(value: Any) -> None:
        """Flushes any tail lines, then delivers the return value"""
        render(drain())
        if on_done is not None:
            on_done(value)

    async def fail(message: str) -> None:
        """Delivers an error message on the event loop"""
        if on_error is not None:
            on_error(message)

    def emit(line: str) -> None:
        """Buffers a line and schedules a flush (worker thread)"""
        nonlocal flush_pending
        with lock:
            buffer.append(line)
            if flush_pending:
                return
            flush_pending = True
        page.run_task(flush)

    def worker() -> None:
        """
        Runs the generator, buffering output and mapping launcher / process
        exceptions to user-friendly messages
        """
        try:
            while True:
                try:
                    line = next(gen)
                except StopIteration as stop:
                    page.run_task(finish, stop.value)
                    return
                emit(line)
        except LauncherError as exc:
            page.run_task(fail, str(exc))
        except subprocess.CalledProcessError as exc:
            page.run_task(fail, f"Command Failed ({exc.returncode})")
        except FileNotFoundError as exc:
            page.run_task(fail, f"Command Not Found: {exc.filename}")
        except Exception as exc:
            LOGGER.exception("GUI Stream Failed")
            page.run_task(fail, str(exc))

    page.run_thread(worker)
