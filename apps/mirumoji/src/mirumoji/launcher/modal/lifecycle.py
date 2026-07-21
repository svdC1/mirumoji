"""
Holds the launcher-only Modal host lifecycle operations (credentials, volume
management, URLs, and logs)

The app-agnostic surface the server also uses stays in `mirumoji.modal`

This module is the launcher's single Modal facade, so the app-agnostic
surface it needs from `mirumoji.modal` (`stop`, `deployed_tags`,
`VERSION_KEY`) is re-exported here for callers alongside the launcher-only
operations defined below
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from ...exceptions import ModalError
from ...modal import (
    NO_WINDOW,
    VERSION_KEY,
    clean_subprocess_error,
    deployed_tags,
    ensure_authenticated,
    modal_cli_argv,
    stop,
)
from ..core.process import StreamHandle, stream

__all__ = [
    "VERSION_KEY",
    "app_logs_command",
    "dashboard_url",
    "delete_volume",
    "deployed_tags",
    "download_volume",
    "ensure_volume",
    "fetch_app_logs",
    "follow_app_logs",
    "modal_credentials",
    "stop",
    "volume_exists",
    "web_url",
]

LOGGER = logging.getLogger(__name__)

_CREDENTIAL_KEYS = ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET")
"""
The environment variables the `Modal` SDK and CLI authenticate from
"""

_FORCE_BUILD_KEY = "MODAL_FORCE_BUILD"
"""
The environment variable the `Modal` SDK reads at deploy time to rebuild a
cached image instead of reusing it
"""

_CHILD_ENCODING = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
"""
Forces `utf-8` on the `modal` CLI subprocesses' own standard streams

question: Why
    - On Windows, a subprocess writing to a captured (non-`TTY`) pipe encodes
      its output with the legacy `cp1252` codec, so the CLI crashes with a
      `UnicodeEncodeError` the moment it prints a character `cp1252` can't
      represent (a box border, a progress glyph, or a Japanese filename),
      aborting the command partway through

    - Exporting these into the child's environment makes it encode as `utf-8`,
      so `download-data`, `stop`, and `logs` don't crash encoding their output
"""


@contextmanager
def modal_credentials(env: dict[str, str]) -> Iterator[None]:
    """
    Exports the Modal credentials for the duration of a block, restoring the
    previous process environment on exit

    info: Exported Keys
        - The `Modal` SDK and the `modal` CLI subprocesses (`stop`, volume
          download, `logs`) authenticate from `MODAL_TOKEN_ID` /
          `MODAL_TOKEN_SECRET` in the environment, so those are exported

        - `MODAL_FORCE_BUILD` is exported too, but only when explicitly
          enabled, since the SDK reads it from the local process at
          `app.deploy()` to rebuild a cached image instead of reusing it

        - `PYTHONIOENCODING` / `PYTHONUTF8` are exported so the CLI
          subprocesses encode their output as `utf-8` and don't crash on a
          Windows `cp1252` pipe (see `_CHILD_ENCODING`)

        - The rest of the managed config reaches a deploy through the
          container's inline `Secret`, not the local process, so it never
          needs to touch `os.environ`

    info: Restored On Exit
        - A long-running process (the GUI) would otherwise accumulate config in
          `os.environ`, which `envfile.overlay_environ` then leaks back into a
          later config resolution, so a value cleared in the UI could still
          reach the next deploy

        - Restoring keeps the environment clean between commands

    Args:
        env (dict[str, str]): The resolved managed configuration values

    Yields:
        None, with the credentials exported for the duration of the block
    """
    keys = (*_CREDENTIAL_KEYS, _FORCE_BUILD_KEY, *_CHILD_ENCODING)
    saved = {key: os.environ.get(key) for key in keys}
    for key in _CREDENTIAL_KEYS:
        if env.get(key):
            os.environ[key] = env[key]
    # Export MODAL_FORCE_BUILD only when set to "1", so the managed default
    # "0" never forces a rebuild
    if env.get(_FORCE_BUILD_KEY) == "1":
        os.environ[_FORCE_BUILD_KEY] = "1"
    # Force utf-8 on the CLI subprocesses so they don't crash encoding their
    # own output on a Windows cp1252 pipe
    os.environ.update(_CHILD_ENCODING)
    try:
        yield
    finally:
        for key, previous in saved.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def web_url(app_name: str, function_name: str) -> str | None:
    """
    Returns the public URL of a web function deployed to `Modal`

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        app_name (str): The deployed app's name
        function_name (str): The web function's name within the app

    Returns:
        The function's web URL, or `None` when the app or function is absent or
            the URL cannot be read
    """
    import modal
    from modal.exception import NotFoundError

    try:
        function = modal.Function.from_name(app_name, function_name)
        return function.get_web_url()
    except NotFoundError as e:
        LOGGER.warning(
            f"Could Not Get URL Of Web Function '{function_name}' For App "
            f"'{app_name}' : {e}"
        )
        return None
    except Exception as e:
        LOGGER.warning(
            f"Could Not Read Web URL Of Web Function '{function_name}' "
            f"For '{app_name}': {e}"
        )
        return None


def dashboard_url(name: str) -> str | None:
    """
    Returns the `Modal` dashboard URL of a deployed app

    Args:
        name (str): The deployed app name

    Returns:
        The app's dashboard URL, or `None` when it is absent or the URL cannot
            be read
    """
    import modal
    from modal.exception import NotFoundError

    try:
        app = modal.App.lookup(name, create_if_missing=False)
        return app.get_dashboard_url()
    except NotFoundError as e:
        LOGGER.warning(f"Could Not Get Dashboard URL For App '{name}' : {e}")
        return None
    except Exception as e:
        LOGGER.warning(f"Could Not Read Dashboard URL For App '{name}': {e}")
        return None


def ensure_volume(name: str) -> None:
    """
    Creates a named `modal.Volume` if it does not already exist

    Creation is idempotent, so this is safe to call on every deploy

    info: Name-Tracked
        The `Modal` SDK exposes no tags for volumes, so a Mirumoji-managed
        volume is tracked by its reserved name

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        name (str): The volume name

    Raises:
        ModalError: If credentials are missing or the volume cannot be created
    """
    import modal

    ensure_authenticated()
    try:
        modal.Volume.from_name(name, create_if_missing=True)
    except Exception as e:
        raise ModalError(f"Failed To Ensure Volume '{name}': {e}") from e


def volume_exists(name: str) -> bool:
    """
    Reports whether a named `modal.Volume` exists

    Args:
        name (str): The volume name

    Returns:
        `True` when a volume of that name exists

    Raises:
        ModalError: If the workspace cannot be reached to check the volume
    """
    import modal
    from modal.exception import NotFoundError

    try:
        modal.Volume.from_name(name, create_if_missing=False).hydrate()
        return True
    except NotFoundError:
        return False
    except Exception as e:
        raise ModalError(f"Could Not Check Volume '{name}': {e}") from e


def delete_volume(name: str) -> None:
    """
    Deletes a named `modal.Volume` and everything it holds

    Tolerates missing volumes

    info: Destructive + One-Way
        - Deleting a volume erases its data and cannot be undone

        - The volume's app must be stopped first, since Modal refuses to delete
          a volume that a running app still mounts

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        name (str): The volume name to delete

    Raises:
        ModalError: If the deletion fails
    """
    import modal

    try:
        modal.Volume.objects.delete(name, allow_missing=True)
    except Exception as e:
        raise ModalError(f"Failed To Delete Volume '{name}': {e}") from e


def download_volume(name: str, destination: Path) -> None:
    """
    Downloads every file in a named `modal.Volume` into a local directory

    info: SDK-Backed
        - Walks the volume with `listdir(recursive=True)` and streams each file
          out through the SDK, so nothing is spawned

        - This used to shell out to `modal volume get`. In the packaged desktop
          GUI `sys.executable` is the app binary rather than an interpreter, so
          that spawned a second GUI window and blocked forever waiting on it

    info: Overwrites
        An existing local copy is replaced, so re-downloading into a populated
        directory refreshes it rather than failing

    info: Blocking
        Performs network I/O and can take a while for a large volume, so a
        caller on the event loop should run it in a thread

    Args:
        name (str): The volume name to download
        destination (Path): The local directory to download the volume into

    Raises:
        ModalError: If credentials are missing, the volume is absent, or the
            download fails
    """
    import modal

    ensure_authenticated()
    # Guard the common case with a clean message instead of a raw SDK error
    if not volume_exists(name):
        raise ModalError(
            f"The Data Volume '{name}' Does Not Exist. Deploy The Host App "
            "First To Create It"
        )
    LOGGER.info(f"Downloading Modal Volume '{name}' To '{destination}'")
    try:
        destination.mkdir(parents=True, exist_ok=True)
        volume = modal.Volume.from_name(name)
        entries = volume.listdir("/", recursive=True)
    except Exception as e:
        raise ModalError(f"Failed To Download Volume '{name}': {e}") from e

    copied = 0
    for entry in entries:
        # Directories are implied by their files, so only files are streamed
        if getattr(entry, "type", None) == modal.types.FileEntryType.DIRECTORY:
            continue
        relative = PurePosixPath(entry.path.lstrip("/"))
        target = destination / Path(*relative.parts)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as f:
                for chunk in volume.read_file(entry.path):
                    f.write(chunk)
        except Exception as e:
            raise ModalError(
                f"Failed To Download '{entry.path}' From Volume '{name}': {e}"
            ) from e
        copied += 1

    LOGGER.info(
        f"Downloaded {copied} File(s) From Volume '{name}' To '{destination}'"
    )


_FOLLOW_POLL_SECONDS = 2.0
"""
How long the in-process follow fallback waits between log polls
"""

_FOLLOW_POLL_STEP = 0.2
"""
How often the poll wait checks its `StreamHandle` for a stop request, so the
Stop button stays responsive while the fallback sleeps between polls
"""

_FOLLOW_POLL_LIMIT = 1000
"""
How many entries each follow poll requests, bounding a burst between polls
"""


def _tail_logs_in_process(
    name: str,
    tail: int,
    since: datetime | None = None,
) -> list[tuple[float, str]]:
    """
    Fetches recent log entries of a deployed Modal app through the SDK

    question: Why Not A Subprocess
        - The Modal SDK exposes no public log reader, and the packaged desktop
          GUI has no interpreter to shell out with, so the CLI's underlying
          fetch helper is driven directly

        - The internals are imported inside the function so a modal release
          that moves or reshapes them surfaces as `ImportError` or
          `AttributeError`, which the caller turns into a CLI fallback rather
          than a hard failure (the `_stop_in_process` contract)

    info: Cursor Fetches
        `since` is an inclusive hard floor in modal's fetch, so a follow
        caller can poll with the newest timestamp it has seen and drop the
        entries it already yielded

    info: Synchronizer Loop
        - The blocking `App.lookup` creates modal's singleton client on the
          SDK's own synchronizer event loop, so the fetch coroutine must run
          on that same loop

        - Running it on a second loop (a plain `asyncio.run`) makes the RPC
          lose its cancellation context and hang, with modal warning
          `RPC request made outside of task context`, so the coroutine is
          handed to modal's `synchronizer` the way the SDK's CLI helpers are

    Args:
        name (str): The deployed app name
        tail (int): How many recent entries to fetch
        since (datetime | None): Only return entries at or after this time

    Returns:
        The fetched entries as `(timestamp, text)` pairs

    Raises:
        ModalError: If the app is not deployed
        ImportError: If modal no longer ships the internals driven here
        AttributeError: If modal reshaped those internals
    """
    import modal
    from modal._logs import tail_logs
    from modal._utils.async_utils import synchronizer
    from modal.client import _Client
    from modal.exception import NotFoundError

    try:
        app_id = modal.App.lookup(name, create_if_missing=False).app_id
    except NotFoundError as e:
        raise ModalError(f"The Modal App '{name}' Is Not Deployed") from e
    if app_id is None:
        raise ModalError(f"The Modal App '{name}' Is Not Deployed")

    async def _collect() -> list[tuple[float, str]]:
        client = await _Client.from_env()
        entries: list[tuple[float, str]] = []
        async for batch in tail_logs(client, app_id, tail, since=since):
            for item in batch.items:
                entries.append((item.timestamp, item.data))
        return entries

    result: list[tuple[float, str]] = synchronizer.wrap(_collect)()
    return result


def _format_log_lines(entries: list[tuple[float, str]]) -> list[str]:
    """
    Renders fetched `(timestamp, text)` log entries as timestamped lines

    An entry's text can span multiple lines, so each is split and every line
    carries the entry's `ISO-8601` `UTC` timestamp. Empty entries are skipped.
    The rendering is close to, though not byte-identical with, the
    `modal app logs --timestamps` output the CLI path produces

    Args:
        entries (list[tuple[float, str]]): The fetched log entries

    Returns:
        The timestamped log lines
    """
    lines: list[str] = []
    for timestamp, data in entries:
        if not data:
            continue
        prefix = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        for line in data.splitlines():
            lines.append(f"{prefix} {line}")
    return lines


def app_logs_command(name: str, *, follow: bool, tail: int) -> list[str]:
    """
    Builds the `modal app logs` argv for fetching or following an app's logs

    info: Fetch vs Follow
        - `follow=False` fetches the last `tail` entries and exits, suited to
          a captured one-shot read (see `fetch_app_logs`)

        - `follow=True` live-streams until interrupted, suited to
          `launcher.core.process.stream`, whose `StreamHandle` cancels it so
          the CLI and GUI can stop the follow cleanly

    Args:
        name (str): The deployed app name
        follow (bool): Live-follow instead of fetching recent entries
        tail (int): How many recent entries to fetch (ignored when following)

    Returns:
        The `modal app logs` argv

    Raises:
        ModalError: If there is no interpreter or `modal` executable to spawn
    """
    argv = modal_cli_argv("app", "logs", name, "--timestamps")
    if follow:
        argv.append("-f")
    else:
        argv += ["--tail", str(tail)]
    return argv


def fetch_app_logs(name: str, tail: int) -> str:
    """
    Fetches the most recent log entries of a deployed Modal app

    info: In-Process First
        - Reads the logs through the Modal SDK in-process, so the packaged
          desktop GUI (whose `sys.executable` is the app binary rather than an
          interpreter) can fetch them without spawning anything

        - Falls back to the `modal app logs` CLI when modal moved or reshaped
          the internals the in-process read drives, mirroring the `stop` path

    Args:
        name (str): The deployed app name
        tail (int): How many recent log entries to fetch

    Returns:
        The fetched log text, timestamped and ready to print

    Raises:
        ModalError: If credentials are missing or the app has no readable logs
    """
    ensure_authenticated()
    try:
        entries = _tail_logs_in_process(name, tail)
    except (ImportError, AttributeError, TypeError) as e:
        # Modal moved or reshaped its internals, so fall back to the CLI
        LOGGER.warning(
            f"Could Not Read Logs For '{name}' In-Process, Falling Back To "
            f"The Modal CLI : {e}"
        )
    except ModalError:
        raise
    except Exception as e:
        raise ModalError(f"Failed To Read Logs For '{name}': {e}") from e
    else:
        lines = _format_log_lines(entries)
        return "\n".join(lines) + "\n" if lines else ""

    try:
        argv = app_logs_command(name, follow=False, tail=tail)
    except ModalError as e:
        raise ModalError(
            f"Failed To Read Logs For '{name}': {e}. Read Them From The Modal "
            "Dashboard Or The 'mirumoji modal logs' Command Instead"
        ) from e
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            stdin=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise ModalError(f"Failed To Read Logs For '{name}': {e}") from e
    if result.returncode != 0:
        detail = clean_subprocess_error(result.stderr)
        raise ModalError(f"Failed To Read Logs For '{name}': {detail}")
    return result.stdout


def follow_app_logs(
    name: str,
    *,
    tail: int,
    handle: StreamHandle,
) -> Generator[str, None, None]:
    """
    Live-follows a deployed Modal app's logs until the handle is cancelled

    info: CLI Stream First
        - Outside the packaged bundle, when a `modal` CLI argv can be built,
          the follow is a real `modal app logs -f` subprocess through
          `launcher.core.process.stream`, which is the lowest-latency stream
          and the behavior the CLI and dev GUI have always had

        - `check=False` because cancelling kills the process, which then
          exits non-zero through no fault of its own

    info: Polling Fallback
        - The packaged desktop GUI never spawns a CLI. Its own interpreter is
          the app binary, and whatever `python` the `PATH` offers is not the
          one carrying its modal (on Windows it can even be the Store alias
          stub that only prints an install prompt), so there the follow polls
          the SDK-backed fetch about every 2 seconds with a timestamp cursor,
          deduping the entries that share the cursor's timestamp

        - Entries therefore arrive with up to a couple of seconds of delay
          rather than live, which is the closest the SDK allows without a
          subprocess

    info: Cancellation
        Cooperative through `handle`. The CLI stream is killed by it and the
        polling loop checks it several times a second while waiting

    Args:
        name (str): The deployed app name
        tail (int): How many recent entries to show when the follow starts
        handle (StreamHandle): Cancellation token that stops the follow

    Yields:
        The log lines

    Raises:
        ModalError: If credentials are missing or the logs cannot be read
    """
    argv: list[str] | None = None
    if getattr(sys, "frozen", False):
        LOGGER.info(f"Packaged Bundle, Following Logs For '{name}' In-Process")
    else:
        try:
            argv = app_logs_command(name, follow=True, tail=tail)
        except ModalError:
            LOGGER.info(
                f"No Modal CLI Available, Following Logs For '{name}' "
                "In-Process"
            )
    if argv is not None:
        yield from stream(argv, check=False, handle=handle)
        return

    ensure_authenticated()
    cursor: float | None = None
    seen: set[tuple[float, str]] = set()
    while not handle.cancelled:
        since = (
            datetime.fromtimestamp(cursor, tz=timezone.utc)
            if cursor is not None
            else None
        )
        limit = tail if cursor is None else _FOLLOW_POLL_LIMIT
        try:
            entries = _tail_logs_in_process(name, limit, since=since)
        except ModalError:
            raise
        except Exception as e:
            raise ModalError(
                f"Failed To Follow Logs For '{name}': {e}. Read Them From "
                "The Modal Dashboard Instead"
            ) from e
        fresh = [entry for entry in entries if entry not in seen]
        if fresh:
            yield from _format_log_lines(fresh)
            cursor = max(timestamp for timestamp, _ in fresh)
            # Only entries sharing the cursor's timestamp can reappear in the
            # next poll (`since` is inclusive), so the dedupe set stays small
            seen = {entry for entry in seen | set(fresh) if entry[0] == cursor}
        waited = 0.0
        while waited < _FOLLOW_POLL_SECONDS and not handle.cancelled:
            time.sleep(_FOLLOW_POLL_STEP)
            waited += _FOLLOW_POLL_STEP
