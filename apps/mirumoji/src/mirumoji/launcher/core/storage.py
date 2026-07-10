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


def _mirumoji_root(path: Path) -> Path:
    """
    Resolves a `platformdirs` path to the `mirumoji` app folder it belongs to

    Returns the path itself when it is already the `mirumoji` folder, otherwise
    its nearest `mirumoji`-named ancestor. This maps a nested platform subdir
    (the Windows `Cache` / `Logs` folders, or the Linux `log` subdir of the
    state folder) back to the app folder that should be pruned, while leaving
    the shared system root above it untouched

    Args:
        path (Path): A `platformdirs` directory (data, config, cache, state, or
            log)

    Returns:
        The `mirumoji` app folder for `path`, or `path` itself when it has no
            `mirumoji` ancestor
    """
    candidate = path
    while candidate.name != "mirumoji" and candidate.parent != candidate:
        candidate = candidate.parent
    return candidate


def _prune_empty(*directories: Path) -> None:
    """
    Removes each `mirumoji` app folder that is now empty

    info: App Folders Only
        - Every argument is a `mirumoji`-named folder (see `_mirumoji_root`),
          so removal never reaches a shared system root such as
          `%LOCALAPPDATA%`, `~/Library/Caches`, or `~/.local/state`

        - A folder the user chose to keep (its config file or logs still
          present) is left in place because it is not empty

    Args:
        *directories (Path): The `mirumoji` app folders to remove when empty
    """
    for directory in directories:
        if directory.is_dir() and not any(directory.iterdir()):
            try:
                directory.rmdir()
            except OSError as exc:
                LOGGER.warning(f"Could Not Remove {directory}: {exc}")


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

    # Prune the now-empty `mirumoji` app folder in every platformdirs root. On
    # Windows these collapse to one folder, on macOS / Linux they are several,
    # and the state folder is only reachable through its `log` subdir, so each
    # root is mapped to its `mirumoji` folder and de-duplicated before pruning
    _prune_empty(
        *sorted(
            {
                _mirumoji_root(path)
                for path in (
                    HOST_STORAGE.user_data_path,
                    HOST_STORAGE.user_config_path,
                    HOST_STORAGE.user_cache_path,
                    HOST_STORAGE.user_state_path,
                    HOST_STORAGE.user_log_path,
                )
            }
        )
    )

    return steps
