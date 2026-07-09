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
    `modal` is imported lazily inside each function so that importing this
    module (which the launcher does on every command) stays cheap
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import TYPE_CHECKING

from .exceptions import ModalError

if TYPE_CHECKING:
    import modal

LOGGER = logging.getLogger(__name__)

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
    Ensures Modal API credentials are present in the environment

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
    Returns the tags of a deployed Modal app, or `None` when it is not deployed

    info: Untagged Apps
        A deployed app whose tags cannot be read is reported as an empty
        mapping rather than `None`, so callers can still tell it apart from an
        app that is absent

    Args:
        name (str): The deployed app name

    Returns:
        The app's tag mapping, `{}` when it has none readable, or `None` when
            no app of that name is deployed
    """
    import modal
    from modal.exception import NotFoundError

    try:
        app = modal.App.lookup(name, create_if_missing=False)
    except NotFoundError:
        return None
    try:
        return app.get_tags()
    except Exception:
        return {}


def is_deployed(name: str) -> bool:
    """
    Reports whether a Modal app is currently deployed

    Args:
        name (str): The deployed app name

    Returns:
        `True` if an app with that name is deployed
    """
    return deployed_tags(name) is not None


def ensure_deployed(app: modal.App, name: str, *, version: str) -> None:
    """
    Deploys a Modal `app` under `name` unless the current `version` is already
    live

    info: Idempotent + Tracked
        - Looks the app up first and returns early when a Mirumoji-managed app
          of the same version is already deployed

        - Otherwise deploys in place (Modal updates an app of the same name
          rather than creating a duplicate) and tags it for ownership, so a
          package upgrade transparently rolls the deployed app forward

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        app (modal.App): The locally-defined app to deploy
        name (str): The deployed app name
        version (str): The package version being deployed

    Raises:
        ModalError: If credentials are missing or the deploy fails
    """
    ensure_authenticated()
    tags = deployed_tags(name)
    if (
        tags is not None
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


def stop(name: str) -> None:
    """
    Stops a deployed app, removing it from the workspace

    info: CLI-Backed
        - Modal's Python SDK exposes no public call to stop an app, so this
          shells out to `modal app stop` via subprocess

        - Stopping is one-way, so a stopped app is redeployed
          rather than restarted

    info: Best Effort
        Tolerates a missing app and a failed stop, so it never blocks a caller
        such as server shutdown

    info: Blocking
        Performs network I/O, so a caller on the event loop should run it in a
        thread

    Args:
        name (str): The deployed app name to stop
    """

    LOGGER.info(f"Stopping Modal App '{name}'")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "modal", "app", "stop", name, "-y"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        LOGGER.warning(f"Could Not Stop Modal App '{name}': {e}")
        return
    if result.returncode != 0:
        LOGGER.warning(
            f"Could Not Stop Modal App '{name}': {result.stderr.strip()}"
        )
