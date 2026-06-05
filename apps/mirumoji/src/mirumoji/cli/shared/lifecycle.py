"""
Defines Docker Compose lifecycle operations for the launcher

Thin, presentation-free wrappers over `docker compose` and `docker build` that
stream their output
"""

import logging
from collections.abc import Generator
from pathlib import Path

from . import checks, process
from .constants import (
    BACKEND_CONTEXT,
    BACKEND_CPU_DOCKERFILE,
    BACKEND_CPU_LOCAL_IMAGE,
    BACKEND_GPU_DOCKERFILE,
    BACKEND_GPU_LOCAL_IMAGE,
    FRONTEND_CONTEXT,
    FRONTEND_DOCKERFILE,
    FRONTEND_LOCAL_IMAGE,
    PROJECT_NAME,
)
from .errors import BuildSourceError
from .models import Backend, ImageSource

LOGGER = logging.getLogger(__name__)


def _compose_base(
    project: str,
    compose_file: Path | None,
    env_file: Path | None = None,
) -> list[str]:
    """
    Builds the `docker compose` invocation prefix

    Args:
        project (str): The compose project name
        compose_file (Path | None): The resolved compose file, if any
        env_file (Path | None): A `.env` file to pass, if any

    Returns:
        The base command up to (but excluding) the compose subcommand
    """
    cmd = ["docker", "compose"]
    if compose_file is not None:
        cmd += ["-f", str(compose_file)]
    if env_file is not None:
        cmd += ["--env-file", str(env_file)]
    cmd += ["-p", project]
    return cmd


def up(
    compose_file: Path,
    *,
    env_file: Path | None = None,
    detach: bool = True,
    project: str = PROJECT_NAME,
) -> Generator[str, None, int]:
    """
    Starts the application with `docker compose up`

    Args:
        compose_file (Path): The resolved compose file to run
        env_file (Path | None): A `.env` file to pass to compose
        detach (bool): Run detached when `True`
        project (str): The compose project name

    Yields:
        Each line of compose output

    Returns:
        The compose exit code
    """
    checks.require_docker()
    cmd = [*_compose_base(project, compose_file, env_file), "up"]
    if detach:
        cmd.append("-d")
    return (yield from process.stream(cmd))


def pull(
    compose_file: Path,
    *,
    env_file: Path | None = None,
    project: str = PROJECT_NAME,
) -> Generator[str, None, int]:
    """
    Pulls the application's images with `docker compose pull`

    Args:
        compose_file (Path): The resolved compose file
        env_file (Path | None): A `.env` file to pass to compose
        project (str): The compose project name

    Yields:
        Each line of compose output

    Returns:
        The compose exit code
    """
    checks.require_docker()
    cmd = [*_compose_base(project, compose_file, env_file), "pull"]
    return (yield from process.stream(cmd))


def down(
    *,
    volumes: bool = False,
    compose_file: Path | None = None,
    project: str = PROJECT_NAME,
) -> Generator[str, None, int]:
    """
    Stops the application with `docker compose down`

    Args:
        volumes (bool): Also remove named data volumes when `True`
        compose_file (Path | None): The resolved compose file, if available
        project (str): The compose project name

    Yields:
        Each line of compose output

    Returns:
        The compose exit code
    """
    checks.require_docker()
    cmd = [*_compose_base(project, compose_file), "down"]
    if volumes:
        cmd.append("-v")
    return (yield from process.stream(cmd))


def ps(
    *,
    compose_file: Path | None = None,
    project: str = PROJECT_NAME,
) -> str:
    """
    Returns the application's services as compose JSON

    Args:
        compose_file (Path | None): The resolved compose file, if available
        project (str): The compose project name

    Returns:
        The raw `docker compose ps --format json` output

    Raises:
        DependencyError: If Docker is not running
    """
    checks.require_docker()
    cmd = _compose_base(project, compose_file)
    cmd += ["ps", "-a", "--format", "json"]
    return process.run(cmd).stdout


def logs(
    service: str | None = None,
    *,
    follow: bool = False,
    tail: int | None = None,
    compose_file: Path | None = None,
    project: str = PROJECT_NAME,
) -> Generator[str, None, int]:
    """
    Streams container logs with `docker compose logs`

    Args:
        service (str | None): A single service to scope to, or all when `None`
        follow (bool): Keep following new output when `True`
        tail (int | None): Limit to the last N lines when given
        compose_file (Path | None): The resolved compose file, if available
        project (str): The compose project name

    Yields:
        Each log line

    Returns:
        The compose exit code
    """
    checks.require_docker()
    cmd = [*_compose_base(project, compose_file), "logs"]
    if follow:
        cmd.append("-f")
    if tail is not None:
        cmd += ["--tail", str(tail)]
    if service is not None:
        cmd.append(service)
    return (yield from process.stream(cmd))


def _build(image: str, dockerfile: Path, context: Path) -> list[str]:
    """
    Builds a `docker build` command

    Args:
        image (str): The tag to assign
        dockerfile (Path): The Dockerfile to build with
        context (Path): The build context directory

    Returns:
        The build command

    Raises:
        BuildSourceError: If the Dockerfile or context is missing
    """
    if not dockerfile.is_file():
        raise BuildSourceError(f"Dockerfile Not Found  ↦  {dockerfile}")
    if not context.is_dir():
        raise BuildSourceError(f"Build Context Not Found  ↦  {context}")
    return [
        "docker",
        "build",
        "-t",
        image,
        "-f",
        str(dockerfile),
        str(context),
    ]


def build_images(
    repo_path: Path,
    backend: Backend,
    source: ImageSource = ImageSource.BUILD,
) -> Generator[str, None, None]:
    """
    Builds the frontend and backend images from the checked out repo

    Args:
        repo_path (Path): The managed source checkout root
        backend (Backend): Selects the backend Dockerfile + Tag
        source (ImageSource): Accepted for symmetry. Builds regardless

    Yields:
        Each line of build output

    Raises:
        DependencyError: If Docker is not running
        BuildSourceError: If a Dockerfile or context is missing
    """
    checks.require_docker()

    yield "Building Frontend Image"
    yield from process.stream(
        _build(
            FRONTEND_LOCAL_IMAGE,
            repo_path / FRONTEND_DOCKERFILE,
            repo_path / FRONTEND_CONTEXT,
        ),
    )

    if backend is Backend.LOCAL:
        image, dockerfile = BACKEND_GPU_LOCAL_IMAGE, BACKEND_GPU_DOCKERFILE
    else:
        image, dockerfile = BACKEND_CPU_LOCAL_IMAGE, BACKEND_CPU_DOCKERFILE

    yield "Building Backend Image"
    yield from process.stream(
        _build(
            image,
            repo_path / dockerfile,
            repo_path / BACKEND_CONTEXT,
        ),
    )
