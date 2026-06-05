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
    branch: str = DEFAULT_BRANCH,
) -> Generator[str, None, Path]:
    """
    Clones or updates the managed source checkout, yielding progress lines

    Clones `repo_url` into `repo_path` when absent, otherwise fetches and
    fast-forwards the tracked branch. Output is yielded line by line

    Args:
        repo_url (str): The repository URL to clone
        repo_path (Path): Where the checkout lives (the user-data dir)
        branch (str): The branch to check out / pull

    Yields:
        Each git output line as it is produced

    Returns:
        The path to the ready checkout

    Raises:
        BuildSourceError: If git is missing or the clone/update fails
    """
    if not git().ok:
        raise BuildSourceError(
            "Git Is Required To Build Images Locally But Was Not Found",
        )

    try:
        if not (repo_path / ".git").is_dir():
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            yield f"Cloning {repo_url} Into {repo_path}"
            yield from process.stream(
                ["git", "clone", "--branch", branch, repo_url, str(repo_path)],
            )
        else:
            yield f"Updating Checkout At {repo_path}"
            yield from process.stream(
                ["git", "-C", str(repo_path), "fetch", "--all", "--prune"],
            )
            yield from process.stream(
                ["git", "-C", str(repo_path), "checkout", branch],
            )
            yield from process.stream(
                ["git", "-C", str(repo_path), "pull", "--ff-only"],
            )
    except Exception as exc:
        raise BuildSourceError(
            f"Could Not Prepare Source Checkout  ↦  {exc}",
        ) from exc

    return repo_path
