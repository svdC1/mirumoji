"""
Defines the shared Modal deployment lifecycle used across Mirumoji

Both Modal integrations reuse these helpers but keep their app definitions with
their owner. Only the shared, app-agnostic lifecycle functions lives here

abstract: Server
    The server auto-deploys its GPU-offload app (see `server/modal_processing`)
    which runs only transcription and conversion on modal while everything else
    runs locally

abstract: Launcher
    The launcher deploys mirumoji itself as a hosted app, with both backend
    and frontend running on Modal. Its launcher-only host operations
    (credentials, volume management, URLs, and logs) live in
    `launcher.modal.lifecycle`

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
from typing import TYPE_CHECKING

from .exceptions import ModalError

if TYPE_CHECKING:
    import modal

LOGGER = logging.getLogger(__name__)

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
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


def clean_subprocess_error(stderr: str) -> str:
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
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        message = f"Could Not Stop Modal App '{name}': {e}"
        LOGGER.warning(message)
        return message
    if result.returncode != 0:
        detail = clean_subprocess_error(result.stderr)
        message = f"Could Not Stop Modal App '{name}': {detail}"
        LOGGER.warning(message)
        return message
    return None
