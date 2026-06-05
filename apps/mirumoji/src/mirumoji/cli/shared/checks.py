"""
Defines environment validation checks for the launcher

Each `probe` inspects one external dependency and returns a `CheckResult`
rather than raising, so that a front-end can present a full report
"""

import logging
import platform
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
        cmd (list[str]): The probe command and its arguments
        ok_detail (str): Detail to attach when the probe succeeds. The first
            line of the command output is used when empty

    Returns:
        The mapped check result
    """
    try:
        result = process.run(cmd, check=False)
    except FileNotFoundError:
        return CheckResult(name, CheckStatus.MISSING, "Not Installed")
    lines = result.stdout.strip().splitlines()
    first = lines[0] if lines else ""
    if result.returncode != 0:
        return CheckResult(name, CheckStatus.MISSING, first or "Check Failed")
    return CheckResult(name, CheckStatus.OK, ok_detail or first)


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


def nvidia_toolkit() -> CheckResult:
    """
    Checks whether the NVIDIA Container Toolkit can expose a GPU to Docker

    Runs a short-lived CUDA container with `--gpus all`. Requires both a GPU
    and a running Docker Daemon

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
    return _probe(
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
    Checks whether the Flutter SDK is installed (needed to build executables)

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


def validate(
    backend: Backend,
    source: ImageSource,
) -> list[CheckResult]:
    """
    Runs the checks relevant to a specific deploy configuration

    info: Checks Performed
        - Always Checks Docker + Compose

        - Checks Git When Building Locally

        - Checks NVIDIA Stack When Local Transcription Backend Is Selected

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
