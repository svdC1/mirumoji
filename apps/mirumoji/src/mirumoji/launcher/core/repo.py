"""
Defines helpers to clone / checkout a git repository

The `mirumoji` frontend (`apps/frontend`) directory is not shipped with the
python library, so this module clones or updates the `mirumoji` repo into the
app's user-data directory so that the frontend image can be built locally
"""

import logging
from collections.abc import Generator
from pathlib import Path

from ...paths import HOST_REPO_PATH
from . import process
from .checks import git
from .constants import DEFAULT_BRANCH, REPO_URL
from .errors import BuildSourceError

LOGGER = logging.getLogger(__name__)


def ensure_repo(
    *,
    repo_url: str = REPO_URL,
    repo_path: Path = HOST_REPO_PATH,
    ref: str = DEFAULT_BRANCH,
) -> Generator[str, None, Path]:
    """
    Clones or updates the mirumoji repo at `ref`, yielding progress lines

    Clones `repo_url` into `repo_path` when absent, otherwise fetches tags
    and checks `ref` out. Output is yielded line by line

    info: Release Tags
        `ref` is normally a release tag such as `v3.6.0`, so the build matches
        the pinned image version. A tag checks out a detached `HEAD`, so no
        branch fast-forward is attempted (tags are immutable)

    Args:
        repo_url (str): The repository URL to clone
        repo_path (Path): Where the checkout lives (the user-data dir)
        ref (str): The branch or tag to check out

    Yields:
        Each git output line as it is produced

    Returns:
        The path to the ready checkout

    Raises:
        BuildSourceError: If git is missing or the clone/checkout fails
    """
    if not git().ok:
        raise BuildSourceError(
            "Git Is Required To Build Images Locally But Was Not Found",
        )

    try:
        if not (repo_path / ".git").is_dir():
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            yield f"Cloning '{repo_url}' At '{ref}' Into '{repo_path}'"
            yield from process.stream(
                ["git", "clone", "--branch", ref, repo_url, str(repo_path)],
            )
        else:
            yield f"Updating Checkout At '{repo_path}' To '{ref}'"
            yield from process.stream(
                [
                    "git",
                    "-C",
                    str(repo_path),
                    "fetch",
                    "--all",
                    "--tags",
                    "--prune",
                ],
            )
            yield from process.stream(
                ["git", "-C", str(repo_path), "checkout", "--force", ref],
            )
    except Exception as exc:
        raise BuildSourceError(
            f"Could Not Prepare The Mirumoji Repo At '{ref}'  ↦  {exc}",
        ) from exc

    return repo_path
