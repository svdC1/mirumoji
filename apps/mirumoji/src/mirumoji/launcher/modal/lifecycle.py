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
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ...exceptions import ModalError
from ...modal import (
    NO_WINDOW,
    VERSION_KEY,
    clean_subprocess_error,
    deployed_tags,
    ensure_authenticated,
    stop,
)

__all__ = [
    "VERSION_KEY",
    "app_logs_command",
    "dashboard_url",
    "delete_volume",
    "deployed_tags",
    "download_volume",
    "ensure_volume",
    "fetch_app_logs",
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

    info: CLI-Backed
        The `Modal` SDK exposes no bulk recursive download, so this shells out
        to `modal volume get`, which downloads the whole volume tree in one
        pass (mirroring how `stop` shells out for an app stop)

    info: Overwrites
        Passes `--force`, so re-downloading into a populated directory
        overwrites the existing copies rather than failing

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
    ensure_authenticated()
    # Guard the common case with a clean message instead of the modal CLI's
    # noisy "volume not found" stderr
    if not volume_exists(name):
        raise ModalError(
            f"The Data Volume '{name}' Does Not Exist. Deploy The Host App "
            "First To Create It"
        )
    LOGGER.info(f"Downloading Modal Volume '{name}' To '{destination}'")
    try:
        destination.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "modal",
                "volume",
                "get",
                name,
                "/",
                str(destination),
                "--force",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise ModalError(f"Failed To Download Volume '{name}': {e}") from e
    if result.returncode != 0:
        detail = clean_subprocess_error(result.stderr)
        raise ModalError(f"Failed To Download Volume '{name}': {detail}")


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
    """
    argv = [
        sys.executable,
        "-m",
        "modal",
        "app",
        "logs",
        name,
        "--timestamps",
    ]
    if follow:
        argv.append("-f")
    else:
        argv += ["--tail", str(tail)]
    return argv


def fetch_app_logs(name: str, tail: int) -> str:
    """
    Fetches the most recent log entries of a deployed Modal app

    info: CLI-Backed
        The `Modal` SDK exposes no log reader, so this shells out to
        `modal app logs`, which resolves a deployed app by name and prints its
        recent entries (see streaming `app_logs_command(follow=True)` through
        `launcher.core.process.stream` for the live-follow variant)

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
        result = subprocess.run(
            app_logs_command(name, follow=False, tail=tail),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise ModalError(f"Failed To Read Logs For '{name}': {e}") from e
    if result.returncode != 0:
        detail = clean_subprocess_error(result.stderr)
        raise ModalError(f"Failed To Read Logs For '{name}': {detail}")
    return result.stdout
