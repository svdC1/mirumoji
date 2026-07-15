"""
Defines the `FastAPI` application that the `mirumoji-host` Modal app runs

Builds a FastAPI application that serves the built React frontend and mounts
the server's routers under `/api`, so a single Modal ASGI app answers both the
`SPA` and the `API` on one origin

The server's own `create_app` factory is left untouched, this reuses its
lifespan, exception handlers, and routers by import
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from .auth import BasicAuthMiddleware
from .constants import WEB_PASSWORD_ENV, WEB_USERNAME

if TYPE_CHECKING:
    from fastapi import FastAPI

LOGGER = logging.getLogger(__name__)


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


def create_host_app(frontend_dir: Path) -> FastAPI:
    """
    Builds the FastAPI application server by the `mirumoji-host` Modal app

    info: Additive
        - Does not modify or call `server.app.create_app`

        - Reuses the server's `lifespan`, exception handlers, and routers by
          import, mounting the routers under `/api` (matching the frontend's
          relative `/api` base) and serving the built frontend as a single-page
          app for everything else

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
    from ...paths import HOST_LOG_PATH
    from ...server import media
    from ...server.app import (
        http_exception_handler,
        lifespan,
        mirumoji_exception_handler,
    )
    from ...server.config import get_settings
    from ...server.middleware import LoggingMiddleware
    from ...server.routers.dict import dict_router
    from ...server.routers.health import health_router
    from ...server.routers.jobs import jobs_router
    from ...server.routers.llm import llm_router
    from ...server.routers.profile import profile_router

    takeover_logging(
        log_file="backend.log",
        console=True,
        level=get_settings().logging_level,
    )

    _build_start = perf_counter()

    LOGGER.info("App Build Started")

    LOGGER.info(f"Storing Logs At '{HOST_LOG_PATH / 'backend.log'}'")

    app = FastAPI(
        title="Mirumoji",
        description="Japanese sentence breakdown, audio processing and LLM.",
        lifespan=lifespan,
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
    # the directory is created by `media.init_storage()` in the lifespan
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
