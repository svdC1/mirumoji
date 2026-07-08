"""
Defines the host-storage reset for the launcher

Deletes the `platformdirs` folder Mirumoji writes to on the host, so a user can
wipe their local data without hunting for it. Docker named volumes are out of
scope (use `down --volumes` for those)
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from ...log import teardown_logging
from ...paths import (
    HOST_CONFIG_FILE,
    HOST_DB_PATH,
    HOST_LOG_PATH,
    HOST_MEDIA_PATH,
    HOST_REPO_PATH,
    HOST_STORAGE,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResetStep:
    """
    The outcome of clearing one storage target

    Attributes:
        label (str): Human-readable name of the target
        status (str): One of `removed`, `absent`, or `failed`
        detail (str): The OS error message when `status` is `failed`
    """

    label: str
    status: str
    detail: str = ""


def _remove(label: str, *paths: Path) -> ResetStep:
    """
    Removes one or more files or directory trees under a single label

    Tolerates a missing path (reported as `absent`) and a locked one (reported
    as `failed`), so one target never aborts the wider reset

    Args:
        label (str): Human-readable name for reporting
        *paths (Path): The files or directories grouped under this label

    Returns:
        A `ResetStep` describing the combined outcome
    """
    present = [p for p in paths if p.exists()]
    if not present:
        return ResetStep(label, "absent")
    for path in present:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            LOGGER.warning(f"Could Not Remove {path}: {exc}")
            return ResetStep(label, "failed", str(exc))
    return ResetStep(label, "removed")


def _prune_empty(*directories: Path) -> None:
    """
    Removes each directory and its app-folder parent when left empty

    Clears the now-empty version and app folders so the storage directory is
    actually gone rather than an empty shell. Only ever removes empty
    directories, so a sibling (such as another version) is preserved

    info: No Deduplication
        A shared parent is attempted on every pass rather than once, since a
        parent only becomes empty after its last child is pruned

    Args:
        *directories (Path): The version directories to prune upward from
    """
    for directory in directories:
        for candidate in (directory, directory.parent):
            try:
                if candidate.is_dir() and not any(candidate.iterdir()):
                    candidate.rmdir()
            except OSError:
                pass


def reset_storage(
    *,
    keep_config: bool = False,
    keep_logs: bool = False,
) -> list[ResetStep]:
    """
    Deletes Mirumoji's host storage folder

    Removes the media, database (and its sidecars), source checkout, and cache.
    The config (env keys) and logs go too unless kept. Docker named volumes are
    not touched

    info: Log Handle
        - The launcher holds `launcher.log` open, so logging is torn down
          before the logs directory is removed

        - This releases the file so the folder is deletable on Windows

    info: Best Effort
        - Each target is cleared independently

        - A locked path (such as the database while a native server runs) is
          reported as `failed` rather than aborting the reset

    Args:
        keep_config (bool): Preserve the managed config file when `True`
        keep_logs (bool): Preserve the logs directory when `True`

    Returns:
        One `ResetStep` per target, in the order attempted
    """
    db_sidecars = sorted(HOST_DB_PATH.parent.glob(f"{HOST_DB_PATH.name}-*"))

    steps = [
        _remove("Media files", HOST_MEDIA_PATH),
        _remove("Database", HOST_DB_PATH, *db_sidecars),
        _remove("Source checkout", HOST_REPO_PATH),
        _remove("Cache", HOST_STORAGE.user_cache_path),
    ]

    if not keep_config:
        steps.append(_remove("Config", HOST_CONFIG_FILE))

    if not keep_logs:
        # Release launcher.log before removing the directory it lives in
        teardown_logging()
        steps.append(_remove("Logs", HOST_LOG_PATH))

    _prune_empty(
        HOST_STORAGE.user_data_path,
        HOST_STORAGE.user_cache_path,
        HOST_STORAGE.user_log_path,
        HOST_STORAGE.user_config_path,
    )

    return steps
