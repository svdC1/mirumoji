"""
Defines themed `Rich` progress bars for server-side oprations

info: One Shared Display
    - File uploads and `Modal` volume transfers report their byte progress
      through `transfer_bar`, a context manager that yields an `advance`
      callable

    - All bars share a single `rich.progress.Progress` object
      (obtained lazily via `_progress_display_manager`) drawn on the shared
      console, so concurrent transfers (batches) render as
      stacked tasks in one display instead of fighting over stdout

    - On a non-interactive stream (the server under Docker / uvicorn) the bars
      are a no-op, so nothing is written except the surrounding `LOGGER` lines
"""

import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import BinaryIO, TypeAlias

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ..log import get_console

Advance: TypeAlias = Callable[[int], None]
"""
The signature of the `advance` callback called by each tracked-progress
operation with the number representing how much to advance the progress counter
"""


class _ProgressDisplayManager:
    """
    Owns the single shared `rich.progress.Progress` instance and multiplexes
    progres-tracked tasks onto it

    Encapsulates the display, its thread lock, and the active-task count as
    an instance state (obtained through the cached `_progress_display_manager`
    accessor). The `Progress` starts on the first active task and stops when
    the last one finishes
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = 0
        self._progress = Progress(
            TextColumn("[heading]{task.description}[/]"),
            TextColumn("[muted]•[/]"),
            BarColumn(
                style="warning",
                complete_style="accent",
                finished_style="success",
                pulse_style="accent.soft",
            ),
            TextColumn("[muted]•[/]"),
            DownloadColumn(),
            TextColumn("[muted]•[/]"),
            TransferSpeedColumn(),
            TextColumn("[muted]•[/]"),
            TimeRemainingColumn(
                compact=True,
                elapsed_when_finished=True,
            ),
            console=get_console(),
            transient=True,
        )

    @contextmanager
    def task(self, description: str, total: int | None) -> Iterator[Advance]:
        """
        Adds a progress-tracked task to the shared display and yields its
        `advance` callable

        Args:
            description (str): The task label
            total (int | None): The total byte count, or `None` when unknown
                (renders an indeterminate bar)

        Yields:
            A callable which advances the task by an arbitrary number
        """
        if not get_console().is_terminal:
            # Disable For Non-Interactive Streams (Docker / Uvicorn)
            yield lambda _advanced: None
            return

        with self._lock:
            if self._active == 0:
                self._progress.start()
            self._active += 1
            task_id = self._progress.add_task(description, total=total)

        try:
            yield lambda advanced: self._progress.update(
                task_id,
                advance=advanced,
            )
        finally:
            with self._lock:
                self._progress.remove_task(task_id)
                self._active -= 1
                if self._active == 0:
                    self._progress.stop()


@lru_cache(maxsize=1)
def _progress_display_manager() -> _ProgressDisplayManager:
    """
    Accessor for the shared progress display manager, built once on first use
    and persisted for the rest of the process' lifespan

    Returns:
        The process-wide `_ProgressDisplayManager` instance
    """
    return _ProgressDisplayManager()


@contextmanager
def transfer_bar(
    description: str,
    total: int | None = None,
) -> Iterator[Advance]:
    """
    Shows a themed byte-transfer progress bar for the duration of the block

    Args:
        description (str): The bar label
        total (int | None): The total byte count, or `None` when unknown

    Yields:
        A callable which advances the bar by a number of bytes
    """
    with _progress_display_manager().task(description, total) as advance:
        yield advance


class CountingReader:
    """
    A transparent binary-reader proxy that reports every read to an
    `Advance` callable

    question: Why
        - The chunked uploader (Modal's `batch_upload`) reads a source file
          itself, so the caller has no per-chunk hook to advance a progress bar

        - Wrapping the file in this proxy makes each `read` also report the
          number of bytes returned, so the bar advances as the uploader
          consumes the file, without changing how the uploader reads

    info: Transparency
        - Only `read` is intercepted

        - Every other attribute (`seek`, `tell`, `close`, `mode`, ...) is
          delegated to the wrapped file via `__getattr__`, so the proxy still
          behaves like the binary stream the uploader expects
    """

    def __init__(self, raw: BinaryIO, advance: Advance) -> None:
        """
        Constructs the proxy

        Args:
            raw (BinaryIO): The real binary file object to read from
            advance (Advance): Called with the byte count of each read
        """
        self._raw = raw
        self._advance = advance

    def read(self, size: int = -1) -> bytes:
        """
        Reads from the wrapped file and advances the bar by the bytes read

        Args:
            size (int): Maximum number of bytes to read, or `-1` for the rest
                of the file

        Returns:
            The bytes read, empty at end of file
        """
        chunk = self._raw.read(size)
        self._advance(len(chunk))
        return chunk

    def __getattr__(self, name: str) -> object:
        """
        Delegates any non-intercepted attribute to the wrapped file

        Only reached for attributes not defined on the proxy itself (so not
        `read`), which keeps `seek` / `tell` / `close` / ... pointing at the
        real file

        Args:
            name (str): The attribute being accessed

        Returns:
            The corresponding attribute of the wrapped binary file
        """
        return getattr(self._raw, name)
