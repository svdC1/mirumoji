"""
Defines the `FastAPI` application that the `mirumoji-host` Modal app runs

Builds a FastAPI application that serves the built React frontend and mounts
the server's routers under `/api`, so a single Modal ASGI app answers both the
`SPA` and the `API` on one origin

info: Local-Disk Data With Background Volume Sync
    - The persistent `modal.Volume` is not mounted on the path where the server
      reads and writes user data. Instead the server operates on the
      container's local disk (`CONTAINER_CACHE`) and a background task mirrors
      every change to the volume mount (`DATA_MOUNT`)

    - This keeps media serving and database access off the volume's `FUSE`
      layer, whose per-request random reads are slow enough to stall video
      playback, while `Modal`'s background and shutdown volume commits still
      persist the data durably

The server's own `create_app` factory is left untouched. This wraps its
`lifespan` (never modifying it) and reuses its exception handlers and routers
by import
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from .auth import BasicAuthMiddleware
from .constants import (
    CONTAINER_CACHE,
    DATA_MOUNT,
    WEB_PASSWORD_ENV,
    WEB_USERNAME,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import FastAPI

LOGGER = logging.getLogger(__name__)

_HOST_EXIT_BUDGET_S = 10.0
"""
Seconds the host waits for a clean shutdown before forcing the process to exit

A stranded `FUSE` write on a non-daemon thread (the volume syncer, or `Modal`'s
own volume commit) can keep the process alive past `Modal`'s shutdown grace, so
a daemon watchdog forces the exit within this budget, which sits comfortably
above a normal shutdown and below `Modal`'s grace, turning a grace-period
`SIGKILL` into a clean exit
"""

_PARTIAL_SUFFIX = ".mirumoji-partial"
"""
Reserved suffix of an in-progress write the volume syncer skips

The server writes media to a uniquely named temporary sibling and
atomically renames it into place (mirroring `server.media.PARTIAL_SUFFIX`).
The suffix isreserved, so it never matches a real uploaded filename,
and skipping it keeps a partially written file from reaching the volume
"""

_DB_FILENAME = "mirumoji.db"
"""
Base name of the `SQLite` database file (matches `paths.HOST_DB_PATH.name`)

The database and its `-wal` / `-shm` sidecars are mirrored to the volume
in the middle of each batch, after media additions and before media deletions,
so the volume never holds a committed row that references a media file not yet
mirrored
"""

_SYNC_COPY_ATTEMPTS = 3
"""
How many times the volume syncer tries a single media copy before giving up

A `Modal` volume is `FUSE`-backed, so a copy can hit a transient error that
clears on a retry. A file that still fails is left pending
(see `_volume_syncer`)
"""

_SYNC_RETRY_BACKOFF = 0.5
"""
Seconds the volume syncer waits between failed copy attempts of one file
"""


def _is_within(root: Path, path: Path) -> bool:
    """
    Reports whether `path` resolves to a location inside `root`

    question: Why
        This guards the `SPA` file server against path-traversal requests that
        try to escape the frontend directory

    Args:
        root (Path): The directory that must contain `path`
        path (Path): The candidate file path

    Returns:
        `True` when `path` is inside `root`
    """
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _cache_control(full_path: str) -> str:
    """
    Chooses a Cache-Control value for a served frontend file

    Content-hashed build assets under `assets/` never change and are cached
    permanently, while the shell, service worker, and manifest revalidate so a
    new deploy is picked up instead of a stale copy

    Args:
        full_path (str): The requested path below the app root

    Returns:
        The Cache-Control header value
    """
    if full_path.startswith("assets/"):
        return "public, max-age=31536000, immutable"
    return "no-cache"


def _remove(path: Path) -> None:
    """
    Removes a file or a directory tree at `path`, tolerating a missing target

    Args:
        path (Path): The path to remove
    """
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def _dir_size(root: Path) -> int:
    """
    Returns the total size in bytes of every file under `root`

    Used only for the warmup benchmark log, so a file vanishing mid-walk
    or any other `OSError` is skipped rather than raised

    Args:
        root (Path): The directory to measure

    Returns:
        The summed size of every file under `root`
    """
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def _shutdown_log(message: str) -> None:
    """
    Writes a host-shutdown message straight to stdout

    question: Why Not `LOGGER`
        - The core lifespan tears logging down as its final shutdow
          step, so by the time the host's shutdown code runs the
          logger has no handlers

        - Writing to stdout keeps these lines in `Modal`'s captured
          container logs

    Args:
        message (str): The message to write
    """
    print(f"[mirumoji-host] {message}", flush=True)


def _arm_shutdown_watchdog() -> None:
    """
    Starts a daemon thread that forces the process to exit if a clean shutdown
    overruns `_HOST_EXIT_BUDGET_S`

    info: Why
        - A `FUSE` write left running on a non-daemon worker thread can block
          interpreter exit long enough to overrun `Modal`'s shutdown grace,
          which then reports a `SIGKILL` failure

        - A daemon thread never blocks a clean exit, so when shutdown finishes
          in time the process exits first and the watchdog dies with it. Only a
          genuinely stuck shutdown ever reaches the `os._exit`
    """
    import threading

    def _force_exit() -> None:
        time.sleep(_HOST_EXIT_BUDGET_S)
        _shutdown_log(
            f"[Shutdown Watcher] Shutdown Exceeded "
            f"{_HOST_EXIT_BUDGET_S:.0f}s, Forcing Exit"
        )
        os._exit(0)

    threading.Thread(
        target=_force_exit,
        name="host-exit-watchdog",
        daemon=True,
    ).start()


async def _warm_cache(cache: Path, mount: Path) -> None:
    """
    Restores the local cache from the volume at startup

    Copies the persisted user data from the volume mount into the local cache
    so a redeployed or restarted container serves the user's existing database
    and media. A first-ever deploy has an empty volume and copies nothing

    info: Benchmark
        Logs the restored size and elapsed time, since this bulk read off the
        volume is the one unavoidable `FUSE` cost and dominates cold-start time

    info: Fail-Closed
        Re-raises on any copy error, so the caller aborts startup rather than
        let the app run on a partial cache that the syncer would then mirror
        back over the intact volume

    Args:
        cache (Path): The local cache directory to populate
        mount (Path): The mounted volume directory to restore from

    Raises:
        OSError: If the restore copy fails
    """
    if not mount.exists() or not any(mount.iterdir()):
        LOGGER.info(f"[Warm Cache] Volume '{mount}' Empty, Nothing To Warm")
        return
    LOGGER.info(
        f"[Warm Cache] Warming Cache From Volume '{mount}' -> '{cache}'"
    )
    start = time.perf_counter()
    await asyncio.to_thread(shutil.copytree, mount, cache, dirs_exist_ok=True)
    elapsed_ms = (time.perf_counter() - start) * 1000
    size_mib = _dir_size(cache) / (1024 * 1024)
    LOGGER.info(
        f"[Warm Cache] Warmed {size_mib:.1f}MiB Into "
        f"Cache In {elapsed_ms:.1f}ms"
    )


def _is_partial(path: Path) -> bool:
    """
    Reports whether `path` is an in-progress write the syncer should skip

    Args:
        path (Path): The changed path

    Returns:
        `True` when the name ends in the reserved partial-write suffix
    """
    return path.name.endswith(_PARTIAL_SUFFIX)


def _is_db_file(path: Path) -> bool:
    """
    Reports whether `path` is the `SQLite` database or one of its sidecars

    Args:
        path (Path): The changed path

    Returns:
        `True` for `mirumoji.db` and its `-wal` / `-shm` files
    """
    return path.name.startswith(_DB_FILENAME)


async def _volume_syncer(cache: Path, mount: Path) -> None:
    """
    Long-running background task mirroring every change under `cache` to
    `mount` for the whole application lifespan, so user data written to the
    fast local disk is persisted to the `Modal` volume

    question: Why
        - The server reads and writes user data on `cache` (local container
          disk) rather than on the volume mount, keeping media serving and
          database access off the volume's slow `FUSE` layer

        - This task copies additions and modifications to `mount` and removes
          deletions from it, so `Modal`'s background and shutdown commits
          persist the data

    info: Ordering
        - Each batch is applied media-additions first, the database in the
          middle, then media-deletions, so a `Modal` volume commit never
          captures a database row whose media file is missing: an added file
          reaches the volume before the row that references it, and a row is
          removed before its file

        - A `WAL` row insert and delete are both a modification of
          `mirumoji.db-wal`, so they can't be told apart by change type;
          keeping the database update between media additions and deletions is
          the safe order for both

        - In-progress writes (the reserved `.mirumoji-partial` suffix) are
          skipped, since the server writes to a temporary sibling and renames
          it into place

    info: Resilience
        - A media copy is retried a few times before it is left pending, and
          the database update is held back while any media copy is pending, so
          a failed copy can't be overtaken by the database row that references
          it (which would strand a row whose file is missing)

        - A media deletion is likewise retried until the file is gone from the
          volume, so a file the user deleted never lingers on the paid volume
          storage

        - Both pending copies and pending deletions are retried at the start of
          every batch, so a transient failure heals on the next change without
          a full rescan

        - A failed database copy only leaves the volume's database lagging
          (never leading) its media, so it is safe and re-runs on the next
          change

        - If the watcher itself errors, it is restarted after a short backoff,
          so a transient failure does not silently end syncing

        - Exits promptly on cancellation at shutdown

    Args:
        cache (Path): The local directory the server reads and writes
        mount (Path): The mounted volume directory kept in sync with `cache`
    """
    # watchfiles ships as a `modal` dependency, so it is always importable in
    # the container the host runs in
    from watchfiles import Change, awatch

    def _order(change: tuple[Change, str]) -> int:
        """
        Determines the order in which changes to the container's local cache
        are mirrored to the persistent modal volume

        Media additions (0) before the database (1) before media deletions
        (2). A WAL row insert and delete are both a `mirumoji.db-wal`
        modification, so the database can't be split by change type. Placing
        it between media additions and deletions keeps the volume consistent
        for both (a file lands before its row, a row is removed before its
        file)

        Args:
            change (tuple[Change, str]): Tuple of the file change reported
                by watchfiles and its source path

        Returns:
            Number between 0-2 representing the priority order of this change's
                sync

        """
        change_type, src_str = change
        if _is_db_file(Path(src_str)):
            return 1
        return 2 if change_type is Change.deleted else 0

    async def _mirror(src: Path, dest: Path, attempts: int) -> bool:
        """
        Copies `src` to `dest`, retrying a `FUSE` hiccup, and reports success

        Args:
            src (Path): The container's local cache added/modified file
            dest (Path): The same file in the peristent modal volume
            attempts (int): How many times to rety on failures

        Returns:
            True if the copy succeded, else False
        """
        for attempt in range(attempts):
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                await asyncio.to_thread(shutil.copy2, src, dest)
                return True
            except Exception as e:
                if attempt + 1 == attempts:
                    LOGGER.error(
                        f"[Volume Syncer] Failed To Copy '{src}' -> "
                        f"'{dest}' : {e}"
                    )
                    return False
                await asyncio.sleep(_SYNC_RETRY_BACKOFF)
        return False

    async def _remove_from_volume(rel_str: str) -> bool:
        """
        Removes a mirrored file from the volume, reporting whether it is gone

        Args:
            rel_str (str): The file's path relative to the container's cache

        Returns:
            `True` when the volume no longer holds the file (removed now or
                already absent), so a delete the user asked for never lingers
                on the paid volume storage
        """
        target = mount / rel_str
        if not target.exists():
            return True
        try:
            await asyncio.to_thread(_remove, target)
            return True
        except Exception as e:
            LOGGER.error(f"[Volume Syncer] Failed To Remove '{target}' : {e}")
            return False

    # Media files whose copy has not succeeded yet, keyed by their cache-
    # relative path. The database update is held back while this is non-empty,
    # so the volume never commits a row whose media file is missing
    pending_copies: dict[str, Path] = {}
    # Volume files whose removal has not succeeded yet. Retried so a file the
    # user deleted never lingers on the paid volume storage
    pending_deletes: set[str] = set()

    LOGGER.info(f"[Volume Syncer] Watching '{cache}' -> '{mount}'")
    while True:
        try:
            async for changes in awatch(cache):
                # Retry operations stranded by an earlier batch first, so a
                # transient failure heals before this batch's database update
                for rel_str, prev in list(pending_copies.items()):
                    if prev.is_file():
                        if await _mirror(prev, mount / rel_str, attempts=1):
                            pending_copies.pop(rel_str, None)
                            LOGGER.info(f"[Volume Syncer] Copied '{rel_str}'")
                    else:
                        # Source gone before it mirrored. Drop the copy and
                        # clear any stale earlier copy left on the volume
                        pending_copies.pop(rel_str, None)
                        if (mount / rel_str).exists():
                            pending_deletes.add(rel_str)
                for rel_str in list(pending_deletes):
                    if await _remove_from_volume(rel_str):
                        pending_deletes.discard(rel_str)

                for change_type, src_str in sorted(changes, key=_order):
                    src = Path(src_str)
                    if _is_partial(src):
                        # Skip the temporary sibling of an in-progress write
                        continue
                    try:
                        rel = src.relative_to(cache)
                    except ValueError:
                        # Not under the cache, ignore
                        continue
                    rel_str = str(rel)
                    dest = mount / rel

                    if change_type is Change.deleted:
                        # Remove the file from the volume, and retry later if
                        # that fails so a file the user deleted never lingers
                        # on the paid volume storage
                        pending_copies.pop(rel_str, None)
                        if await _remove_from_volume(rel_str):
                            pending_deletes.discard(rel_str)
                            LOGGER.info(f"[Volume Syncer] Removed '{rel}'")
                        else:
                            pending_deletes.add(rel_str)
                        continue

                    if _is_db_file(src):
                        # Hold the database back until every media file is
                        # mirrored. The next db-wal change re-runs this. A
                        # failed copy only leaves the volume's database lagging
                        # (never leading) its media, which is safe
                        if pending_copies:
                            LOGGER.warning(
                                "[Volume Syncer] Holding The Database Update "
                                "While A Media File Is Pending"
                            )
                            continue
                        if src.is_file():
                            await _mirror(
                                src, dest, attempts=_SYNC_COPY_ATTEMPTS
                            )
                        continue

                    # A media addition or modification: its file must reach the
                    # volume before the database row that references it
                    if not src.is_file():
                        # Raced with a delete. The delete event mirrors removal
                        continue
                    pending_deletes.discard(rel_str)
                    if await _mirror(src, dest, attempts=_SYNC_COPY_ATTEMPTS):
                        pending_copies.pop(rel_str, None)
                        LOGGER.info(f"[Volume Syncer] Copied '{rel}'")
                    else:
                        pending_copies[rel_str] = src
        except asyncio.CancelledError:
            raise
        except Exception as e:
            LOGGER.error(f"[Volume Syncer] Watcher Failed, Restarting : {e}")
            await asyncio.sleep(1.0)


def _log_syncer_exit(task: asyncio.Task[None]) -> None:
    """
    Done-callback that surfaces an unexpected volume-syncer exit

    A cancelled syncer is the normal shutdown path and is ignored. Any other
    exit means the background mirror stopped while the app was still running,
    which is logged so it is not silent

    Args:
        task (asyncio.Task[None]): The finished syncer task
    """
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        LOGGER.error(f"[Volume Syncer] Exited Unexpectedly : {exc}")


@asynccontextmanager
async def modal_host_lifespan(host_app: FastAPI) -> AsyncIterator[None]:
    """
    Wraps the server's core lifespan with the host's local-disk + volume-sync
    persistence, without modifying the core lifespan

    info: Startup Steps
        - Ensures the local cache exists

        - Warms it from the volume (restoring the user's data on a
          redeploy or restart)

        - Starts the background volume syncer BEFORE the core lifespan, so
          every file the core startup writes (the database, the media tree) is
          mirrored to the volume

        - Runs the core lifespan

    info: Shutdown
        After the core lifespan's teardown (so the database is already closed)

        - A watchdog is armed at shutdown onset so a stranded `FUSE` write can
          never keep the container alive past `Modal`'s grace

        - Cancels the syncer

        - `Modal`'s background and final volume commits persist everything the
          syncer copied, so no explicit reconciliation or commit is needed

    info: Core Untouched
        The server's `lifespan` runs verbatim through `async with`, so the
        Docker deployment that shares it is unaffected

    Args:
        host_app (FastAPI): The host application whose lifecycle is managed

    Yields:
        Control to the running application, matching the core lifespan's yield
    """
    from ...server.app import lifespan

    LOGGER.info("[Host Lifespan] Started Host Config")

    cache = Path(CONTAINER_CACHE)
    mount = Path(DATA_MOUNT)
    syncer: asyncio.Task[None] | None = None
    try:
        cache.mkdir(parents=True, exist_ok=True)
        LOGGER.info(f"[Host Lifespan] Container Cache Ready At '{cache}'")
        # A Failed Warmup Must Abort Startup, Never Run The App On Partial Data
        await _warm_cache(cache, mount)
        LOGGER.info("[Host Lifespan] Starting Volume Syncer")
        syncer = asyncio.create_task(_volume_syncer(cache, mount))
        syncer.add_done_callback(_log_syncer_exit)
        async with lifespan(host_app):
            yield
            # Healthy Shutdown Begins Here
            # Guard Exit Before The Syncer And
            # Modal's Volume Commit Run Their Final FUSE Writes
            _arm_shutdown_watchdog()
    finally:
        if syncer is not None:
            syncer.cancel()
            await asyncio.gather(syncer, return_exceptions=True)
            _shutdown_log("[Volume Syncer] Stopped")
        _shutdown_log("[Host Lifespan] Host Teardown Complete")


def create_host_app(frontend_dir: Path) -> FastAPI:
    """
    Builds the FastAPI application server by the `mirumoji-host` Modal app

    info: Additive
        - Does not modify or call `server.app.create_app`

        - Reuses the server's exception handlers and routers by import,
          mounting the routers under `/api` (matching the frontend's relative
          `/api` base) and serving the built frontend as a single-page app for
          everything else

        - Wraps the server's `lifespan` in `modal_host_lifespan`, which adds
          the local-disk + volume-sync persistence without changing the core
          lifespan

    info: Access Gate
        - When `MIRUMOJI_WEB_PASSWORD` is set, the whole app is wrapped in HTTP
          Basic Auth (see `BasicAuthMiddleware`)

        - When it is unset, the app is served open and a warning is logged,
          which is only expected in local development

    info: Non-Local Import
        The core `mirumoji` package deps don't cover `FastAPI` or the
        `server` extra deps which importing from `server` pull, however
        this function is only ever executed inside a `Modal` container
        that is running mirumoji's CPU-Backend docker image, which
        has `mirumoji` installed with the `server` extra, which is
        why it exists here in the `launcher` sub-package

    Args:
        frontend_dir (Path): The directory holding the built frontend
            (`index.html` plus hashed assets)

    Returns:
        The configured host application
    """
    from time import perf_counter

    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import Response

    from ...exceptions import MirumojiServerError
    from ...log import takeover_logging
    from ...server import media
    from ...server.app import (
        http_exception_handler,
        mirumoji_exception_handler,
    )
    from ...server.config import get_settings
    from ...server.middleware import LoggingMiddleware
    from ...server.routers.dict import dict_router
    from ...server.routers.health import health_router
    from ...server.routers.jobs import jobs_router
    from ...server.routers.llm import llm_router
    from ...server.routers.profile import profile_router

    # No FileHandler. Modal captures container stdout natively
    takeover_logging(
        log_file=None,
        console=True,
        level=get_settings().logging_level,
    )

    _build_start = perf_counter()

    LOGGER.info("App Build Started")

    LOGGER.info("Logging To Stdout (Captured By Modal)")

    app = FastAPI(
        title="Mirumoji",
        description="Japanese sentence breakdown, audio processing and LLM.",
        lifespan=modal_host_lifespan,
    )

    for router in (
        health_router,
        dict_router,
        llm_router,
        profile_router,
        jobs_router,
    ):
        app.include_router(router, prefix="/api")

    # The server serves user media under `media.BASE_PATH`, one level below the
    # frontend so the SPA catch-all never shadows it. `check_dir=False` because
    # the directory is created by `media.init_storage()` in the lifespan.
    # `media.BASE_PATH` is on the container's local disk (`CONTAINER_CACHE`),
    # not the volume mount, so serving media never touches the slow FUSE layer
    app.mount(
        "/api/media",
        StaticFiles(directory=media.BASE_PATH, check_dir=False),
        name="media",
    )
    LOGGER.info(f"Serving '{media.BASE_PATH}' At '/api/media'")

    app.add_exception_handler(
        MirumojiServerError,
        mirumoji_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        HTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )

    index_file = frontend_dir / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> Response:
        """
        Serves a built frontend file, or `index.html` for client-side routes

        An unmatched `/api` path stays a genuine `404` rather than the SPA
        shell, so the frontend still sees API errors as errors

        Args:
            full_path (str): The requested path below the app root

        Returns:
            The requested static file, or the SPA entry point
        """
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = frontend_dir / full_path
        if (
            full_path
            and candidate.is_file()
            and _is_within(frontend_dir, candidate)
        ):
            return FileResponse(
                candidate,
                headers={"Cache-Control": _cache_control(full_path)},
            )
        return FileResponse(
            index_file,
            headers={"Cache-Control": "no-cache"},
        )

    # CORS stays permissive to match the server (the host is single-origin, so
    # it is a no-op for the browser). Basic Auth is added last so it wraps
    # everything and gates the SPA, the assets, and the API uniformly
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    password = os.environ.get(WEB_PASSWORD_ENV)
    if password:
        app.add_middleware(
            BasicAuthMiddleware,
            username=WEB_USERNAME,
            password=password,
        )
    else:
        LOGGER.warning(
            f"{WEB_PASSWORD_ENV} Not Set, Serving The Host App Open"
        )

    _build_end = perf_counter()

    LOGGER.info(
        f"App Build Complete In {(_build_end - _build_start) * 1000:.3f}ms"
    )

    return app
