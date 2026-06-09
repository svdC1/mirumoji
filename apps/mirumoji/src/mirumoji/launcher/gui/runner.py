"""
Defines helpers for running the blocking external command calls defined in the
launcher's core (Environment Checks, Docker Lifecycle Commands, ...) in a
separate OS thread tied to the main page

The core's checks and lifecycle operations block (subprocess calls), so they
are run via `page.run_thread` to keep the Flet UI responsive. Results are
delivered back through callbacks that update controls
"""

import logging
import subprocess
from collections.abc import Callable, Generator
from typing import Any, TypeVar

import flet as ft

from ..core.errors import LauncherError
from .theme import TerminalSurface

LOGGER = logging.getLogger(__name__)

_T = TypeVar("_T")


def run_blocking(
    page: ft.Page,
    fn: Callable[[], _T],
    on_done: Callable[[_T], None],
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    """
    Runs a blocking function in a background thread

    Args:
        page (ft.Page): The page used to schedule the worker thread
        fn (Callable[[], _T]): The blocking function to run
        on_done (Callable[[_T], None]): Called with the result on success
        on_error (Callable[[Exception], None] | None): Called on failures
    """

    def worker() -> None:
        """
        Runs the blocking `fn` function and calls
        `on_done` and `on_error` with the result / exception
        as their arguments
        """
        try:
            result = fn()
        except Exception as exc:
            LOGGER.exception("GUI Background Task Failed")
            if on_error is not None:
                on_error(exc)
            return
        on_done(result)

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
    Runs a `launcher.core` generator function on a background thread and
    streams its yielded output output into a `TerminalSurface` (`ft.Container`)

    info: Behaviour
        - Each yielded line is appended to `terminal` and triggers a page
          reload.

        - The generator's return value is delivered to `on_done`

        - Any launcher / process error is mapped to a message for `on_error`

    Args:
        page (ft.Page): The page used to schedule the worker thread
        gen (Generator[str, None, Any]): The `launcher.core` generator to run
        terminal (TerminalSurface): The surface in which to append output lines
        on_done (Callable[[Any], None] | None): Called with the return value
        on_error (Callable[[str], None] | None): Called with an error message
    """

    def emit(line: str) -> None:
        """
        Appends an output line to `terminal` and updates the page

        Args:
            line (str): The line to append to `terminal`
        """
        terminal.append_log(line)
        page.update()

    def worker() -> None:
        """
        Runs the `launcher.core` generator function, mapping
        launcher / proccess exceptions to user-friendly messages

        """
        try:
            while True:
                try:
                    line = next(gen)
                except StopIteration as stop:
                    if on_done is not None:
                        on_done(stop.value)
                    return
                emit(line)
        except LauncherError as exc:
            if on_error is not None:
                on_error(str(exc))
        except subprocess.CalledProcessError as exc:
            if on_error is not None:
                on_error(f"Command Failed ({exc.returncode})")
        except FileNotFoundError as exc:
            if on_error is not None:
                on_error(f"Command Not Found: {exc.filename}")
        except Exception as exc:
            LOGGER.exception("GUI Stream Failed")
            if on_error is not None:
                on_error(str(exc))

    page.run_thread(worker)
