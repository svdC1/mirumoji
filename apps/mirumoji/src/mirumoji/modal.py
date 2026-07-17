"""
Defines the shared Modal deployment lifecycle used across Mirumoji

Both Modal integrations reuse these helpers but keep their app definitions with
their owner. Only the shared, app-agnostic lifecycle functions lives here

abstract: Server
    The server auto-deploys its GPU-offload app (see `server/modal_processing`)
    which runs only transcription and conversion on modal while everything else
    runs locally

abstract: Launcher
    The launcher deploys mirumoji itself as a hosted app, with both
    backend and frontend running on Modal

info: Authentication
    Every call authenticates through the environment's `MODAL_TOKEN_ID` /
    `MODAL_TOKEN_SECRET` variables, so managing apps on the user's
    own workspace needs nothing but those two tokens

info: Ownership
    Apps deployed through `ensure_deployed` are tagged `managed-by=mirumoji`
    with the deploying package version, so a running install can recognise its
    own app, keep it current, and never create a duplicate

info: Import Cost
    - `modal` is only imported lazily inside each function so that importing
      this module (which the `launcher` does on every command) stays cheap

    - `modal` is a core dependency of the package so importing it here would
      be safe otherwise
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import ModalError

if TYPE_CHECKING:
    import modal

LOGGER = logging.getLogger(__name__)

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
"""
Suppresses the transient console window a console-less GUI process would
otherwise flash when spawning the `modal` CLI on Windows (a no-op elsewhere),
matching `launcher.core.process`
"""

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
"""
Matches the ANSI colour escape codes the `modal` CLI writes to its output
"""

_BOX_DRAWING = "".join(chr(code) for code in range(0x2500, 0x2580))
"""
Every character in Unicode's Box Drawing block, so the borders `Rich` frames
the `modal` CLI's error panels with can be stripped whatever style it uses
"""

_ASCII_BORDER = "+-|"
"""
The ASCII characters `Rich` draws its panel borders with when it renders to a
non-`UTF` terminal (a Windows `cp1252` console)
"""


def _clean_subprocess_error(stderr: str) -> str:
    """
    Distils the `modal` CLI's noisy error output down to one readable line

    The `modal` CLI frames errors with `Rich`, so its stderr carries ANSI
    colour codes and box-drawing borders. This strips both and returns the last
    line that still has content, which is where the CLI puts the actual error

    info: ASCII Borders
        `Rich` falls back to `+`, `-`, and `|` borders on a non-`UTF` terminal
        (a Windows `cp1252` console), so those are stripped too. Otherwise a
        border line would survive and be returned as the error

    Args:
        stderr (str): The captured subprocess stderr

    Returns:
        The concise error line, or a generic fallback when none is found
    """
    plain = _ANSI_RE.sub("", stderr)
    content = []
    for line in plain.splitlines():
        stripped = line.strip(_BOX_DRAWING + _ASCII_BORDER + " ")
        if stripped:
            content.append(stripped)
    return content[-1] if content else "Unknown Error"


MANAGED_BY_KEY = "managed-by"
"""
Tag key marking a Modal app as managed by Mirumoji
"""

MANAGED_BY_VALUE = "mirumoji"
"""
Tag value marking a Modal app as managed by Mirumoji
"""

VERSION_KEY = "mirumoji-version"
"""
Tag key recording the package version a Modal app was deployed from
"""


def managed_tags(version: str) -> dict[str, str]:
    """
    Builds the ownership tags applied to every Mirumoji-managed Modal app

    Args:
        version (str): The package version deploying the app

    Returns:
        The `managed-by` and version tag mapping
    """
    return {MANAGED_BY_KEY: MANAGED_BY_VALUE, VERSION_KEY: version}


def ensure_authenticated() -> None:
    """
    Ensures that the `Modal` API credentials are present in the environment

    Raises:
        ModalError: If either `MODAL_TOKEN_ID` or `MODAL_TOKEN_SECRET` is unset
    """
    if not (os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET")):
        raise ModalError(
            "Modal Credentials Are Not Configured. Set MODAL_TOKEN_ID And "
            "MODAL_TOKEN_SECRET To Manage Modal Apps",
        )


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


def deployed_tags(name: str) -> dict[str, str] | None:
    """
    Returns the tags of a deployed  Modal` app, or `None` when it is not
    deployed

    info: Untagged Apps
        - A deployed app whose tags cannot be read is reported as an empty
          mapping rather than `None`

        - This way, callers can tell a non-tagged app apart from one that
          doesn't exist

    Args:
        name (str): The deployed app name

    Returns:
        The app's tag mapping, `{}` when it has none readable, or `None` when
            no app of that name is deployed

    Raises:
        ModalError: If the workspace cannot be reached to look the app up
    """
    import modal
    from modal.exception import NotFoundError

    try:
        app = modal.App.lookup(name, create_if_missing=False)
    except NotFoundError:
        return None
    except Exception as e:
        raise ModalError(f"Could Not Look Up Modal App '{name}': {e}") from e
    try:
        return app.get_tags()
    except Exception:
        return {}


def ensure_deployed(
    app: modal.App,
    name: str,
    *,
    version: str,
    force: bool = False,
) -> None:
    """
    Deploys a Modal `app` under `name` unless an app of the same name
    containing the `managed_tags(version)` is already deployed

    info: Idempotent + Tracked
        - Looks the app up first and returns early when a Mirumoji-managed app
          of the same version is already deployed

        - If there's no app deployed under `name`, or that app doesn't have the
          `managed_tags(__version__)` tags, the app is deployed with those tags
          set

        - Redeploys happen in place (Modal updates an app of the same `name`
          rather than creating a duplicate), so a package upgrade transparently
          rolls the deployed app forward

    info: Force
        - When `force=True`, the app is always redeployed

        - This is needed to roll out a code or image change without a version
          bump during development

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        app (modal.App): The locally-defined app to deploy
        name (str): The deployed app name
        version (str): The package version being deployed
        force (bool): Redeploy even when the same version is already live

    Raises:
        ModalError: If credentials are missing or the deploy fails
    """
    ensure_authenticated()
    tags = deployed_tags(name)
    if (
        not force
        and tags is not None
        and tags.get(MANAGED_BY_KEY) == MANAGED_BY_VALUE
        and tags.get(VERSION_KEY) == version
    ):
        LOGGER.info(
            f"Modal App '{name}' Already Deployed At Version {version}"
        )
        return

    LOGGER.info(f"Deploying Modal App '{name}' (Version {version})")
    try:
        app.deploy(name=name)
        app.set_tags(managed_tags(version))
    except Exception as e:
        raise ModalError(f"Failed To Deploy Modal App '{name}': {e}") from e
    LOGGER.info(f"Deployed Modal App '{name}'")


def stop(name: str) -> str | None:
    """
    Stops a deployed `Modal` app under `name`, removing it from the workspace

    info: CLI-Backed
        - Modal's Python SDK exposes no public call to stop an app, so this
          shells out to the modal's CLI `modal app stop` via a subprocess
          call

        - Stopping is one-way, so a stopped app is redeployed
          rather than restarted

    info: Best Effort
        - Never raises, so a server caller (shutdown) can ignore the return

        - The failure reason is both logged and returned, so a CLI / GUI caller
          can surface it to the user instead of reporting a false success

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        name (str): The deployed app name to stop

    Returns:
        A short error message when the stop failed, or `None` on success
    """

    LOGGER.info(f"Stopping Modal App '{name}'")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "modal", "app", "stop", name, "-y"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        message = f"Could Not Stop Modal App '{name}': {e}"
        LOGGER.warning(message)
        return message
    if result.returncode != 0:
        detail = _clean_subprocess_error(result.stderr)
        message = f"Could Not Stop Modal App '{name}': {detail}"
        LOGGER.warning(message)
        return message
    return None


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
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise ModalError(f"Failed To Download Volume '{name}': {e}") from e
    if result.returncode != 0:
        detail = _clean_subprocess_error(result.stderr)
        raise ModalError(f"Failed To Download Volume '{name}': {detail}")
