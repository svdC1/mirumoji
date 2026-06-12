"""
Defines functions that check whether or not mirumoji's required
python / system dependencies are available in the end-user's machine

Contains functions that check for the presence of executables with `shutil`
and run system commands using `subprocess` to inspect external dependecies

Each `probe` function inspects one external dependency and returns a
`CheckResult` rather than raising so that a frontend (CLI / GUI) can present a
full report
"""

import logging
import platform
import shutil
from importlib.util import find_spec

from . import process
from .constants import _GPU_PROBE_IMAGE
from .errors import DependencyError
from .models import Backend, CheckResult, CheckStatus, ImageSource

LOGGER = logging.getLogger(__name__)


def _probe(name: str, cmd: list[str], *, ok_detail: str = "") -> CheckResult:
    """
    Runs a command in a subprocess in order to inspect an external depencendy,
    mapping the command's outcome to a `CheckResult`

    Args:
        name (str): The capability being checked
        cmd (list[str]): Which command to run and its arguments
        ok_detail (str): Detail to attach when the command succeeds. The first
            line of the command output is used when empty

    Returns:
        The mapped check result
    """

    # Resolve via the PATH with shutil so that Windows `.bat` / `.cmd`
    # shims like `flutter.bat` are found. The Bare CreateProcess run by
    # subprocess can't find those

    exe = shutil.which(cmd[0])
    if exe is None:
        return CheckResult(name, CheckStatus.MISSING, "Not Installed")
    try:
        # Try to get additional information
        result = process.run([exe, *cmd[1:]], check=False)
    except OSError:
        # Found on PATH but not directly executable (e.g. a shell shim that
        # needs a command processor). Presence is enough to report OK
        return CheckResult(name, CheckStatus.OK, ok_detail or "Installed")

    lines = result.stdout.strip().splitlines()
    first = lines[0] if lines else ""
    if result.returncode != 0:
        return CheckResult(name, CheckStatus.MISSING, first or "Check Failed")
    return CheckResult(name, CheckStatus.OK, ok_detail or first or "Installed")


def docker() -> CheckResult:
    """
    Checks whether the Docker Daemon is installed and running

    Returns:
        The Docker check result
    """
    return _probe(
        "Docker",
        ["docker", "info", "--format", "{{.ServerVersion}}"],
    )


def docker_compose() -> CheckResult:
    """
    Checks whether the Docker Compose v2 plugin is available

    Returns:
        The Docker Compose check result
    """
    return _probe("Docker Compose", ["docker", "compose", "version"])


def git() -> CheckResult:
    """
    Checks whether git is installed

    Returns:
        The git check result
    """
    return _probe("Git", ["git", "--version"])


def nvidia_gpu() -> CheckResult:
    """
    Checks whether an NVIDIA GPU is visible via `nvidia-smi`

    Returns:
        The NVIDIA GPU check result (skipped on macOS)
    """
    if platform.system() not in ("Windows", "Linux"):
        return CheckResult(
            "NVIDIA GPU",
            CheckStatus.SKIPPED,
            "Unsupported Platform",
        )
    return _probe(
        "NVIDIA GPU",
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
    )


def _image_present(image: str) -> bool:
    """
    Checks whether a Docker Image already exists locally

    Args:
        image (str): The image reference to look up

    Returns:
        `True` if `docker image inspect` finds the image
    """
    try:
        result = process.run(
            ["docker", "image", "inspect", image],
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def nvidia_toolkit() -> CheckResult:
    """
    Checks whether the NVIDIA Container Toolkit can expose a GPU to Docker

    Runs a short-lived CUDA container with `--gpus all`. Requires both a GPU
    and a running Docker Daemon

    info: No Side Effects
        The probe image is removed afterwards unless it was already present
        locally before the check, so the check leaves Docker as it found it

    Returns:
        The NVIDIA Container Toolkit check result
    """
    if not nvidia_gpu().ok:
        return CheckResult(
            "NVIDIA Container Toolkit",
            CheckStatus.MISSING,
            "No NVIDIA GPU Detected",
        )
    if not docker().ok:
        return CheckResult(
            "NVIDIA Container Toolkit",
            CheckStatus.MISSING,
            "Docker Not Running",
        )

    # Remember whether the probe image existed before the check
    # If the check pulled it, delete it afterwards
    keep_image = _image_present(_GPU_PROBE_IMAGE)

    result = _probe(
        "NVIDIA Container Toolkit",
        [
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            _GPU_PROBE_IMAGE,
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
        ],
        ok_detail="GPU Reachable From Docker",
    )

    # Best-effort cleanup of the pulled image (ignore failures)
    if not keep_image:
        try:
            process.run(["docker", "rmi", _GPU_PROBE_IMAGE], check=False)
        except OSError:
            LOGGER.debug(f"Could Not Remove Probe Image {_GPU_PROBE_IMAGE}")

    return result


def _module(name: str, label: str) -> CheckResult:
    """
    Checks whether a Python Module is importable without importing it

    Args:
        name (str): The importable module name
        label (str): The capability label for the result

    Returns:
        The module check result
    """
    try:
        present = find_spec(name) is not None
    except ModuleNotFoundError:
        present = False
    if present:
        return CheckResult(label, CheckStatus.OK, "Installed")
    return CheckResult(label, CheckStatus.MISSING, "Not Installed")


def flet() -> CheckResult:
    """
    Checks whether the `flet` GUI dependency is installed

    Returns:
        The Flet check result
    """
    return _module("flet", "Flet")


def flutter() -> CheckResult:
    """
    Checks whether the Flutter SDK is installed (needed to build the GUI)

    Returns:
        The Flutter check result
    """
    return _probe("Flutter", ["flutter", "--version"])


def require_docker() -> None:
    """
    Ensures that a Docker Daemon is running

    Raises when an action cannot proceed without a running Docker Daemon

    Raises:
        DependencyError: If Docker is not installed or not running
    """
    result = docker()
    if not result.ok:
        raise DependencyError(
            f"Docker Is Not Available  ↦  {result.detail}. "
            "Start Docker Desktop And Try Again",
        )


def validate_deploy(
    backend: Backend,
    source: ImageSource,
) -> list[CheckResult]:
    """
    Runs all external dependency checks relevant to a specific deploy
    configuration

    info: Required For All Deploys
        - `Docker`

        - `Compose`

    info: Required When Building Images Locally
        - `Docker`

        - `Compose`

        - `Git`

    info: Required For The `LOCAL` Backend
        - `NVIDIA GPU`

        - `NVIDIA Container Toolkit`

    Args:
        backend (Backend): The chosen transcription backend
        source (ImageSource): Whether images are pulled or built locally

    Returns:
        The ordered list of check results
    """
    results = [docker(), docker_compose()]
    if source is ImageSource.BUILD:
        results.append(git())
    if backend is Backend.LOCAL:
        results.append(nvidia_gpu())
        results.append(nvidia_toolkit())
    return results
