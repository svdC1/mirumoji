"""
Defines the `FastAPI` Mirumoji Server API

Exposes a `create_app` factory that builds and wires the application, plus a
module-level `app = create_app()` singleton for the `mirumoji.server.app:app`
import string (uvicorn, the Docker `CMD`, and the `mirumoji-server` script)

Importing this module has no side effects beyond constructing the app object
logging configuration, storage/database initialisation, and startup logging all
happen inside the lifespan handler, so the module is safe to import as a
library
"""

import asyncio
import logging
import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..exceptions import MirumojiServerError
from . import media
from .config import setup_logging, using_modal
from .constants import DB_URL
from .db import get_engine, init_db
from .processing.processor import Processor
from .routers.audio import audio_router
from .routers.dict import dict_router
from .routers.health_router import health_router
from .routers.llm import llm_router
from .routers.video import video_router

LOGGER = logging.getLogger(__name__)

# --- Lifespan + Handlers ---


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    """
    Manages the API's lifecycle

    info: Startup Operations
        - Logging Configuration

        - Database + Media Storage Initialisation

        - Lifespan-Scoped `Processor` Initialisation

    info: Shutdown Operations
        - Disposes the Database Engine

        - Clears Temporary Media

    Args:
      app (FastAPI): The API object

    Yields:
        Control back to the running application
    """
    setup_logging()
    await init_db()
    media.init_storage()
    app.state.processor = Processor()
    LOGGER.info(f"Database URL: {DB_URL}")
    LOGGER.info(f"USING_MODAL={using_modal()}")
    LOGGER.info(f"Serving '{media.BASE_PATH}' at '/media'.")
    LOGGER.info("Setup Complete")
    yield
    await get_engine().dispose()
    await asyncio.to_thread(
        shutil.rmtree,
        media.TEMP_PATH,
        ignore_errors=True,
    )


async def mirumoji_exception_handler(
    request: Request,
    exc: MirumojiServerError,
) -> JSONResponse:
    """
    Translate domain exceptions into the structured error envelope

    Reads the HTTP contract (`http_status`, `code`) and optional `details`
    that each `MirumojiServerError` subclass carries, so domain code never
    constructs HTTP responses itself

    Args:
      request (Request): Incoming request object
      exc (MirumojiServerError): Raised domain exception

    Returns:
      JSONResponse: The structured error response to return
    """
    LOGGER.warning(f"[{exc.code}] {exc}")
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": exc.details,
            },
        },
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Custom exception handler for all HTTP errors

    Emits the same nested envelope as the domain handler so the frontend has a
    single error shape to parse. The machine-readable `code` is derived from
    the HTTP status phrase (e.g. 404 -> "NotFound")

    Args:
      request (Request): Incoming request object
      exc (HTTPException): Raised exception object

    Returns:
      JSONResponse: The exception response to return
    """
    phrase = HTTPStatus(exc.status_code).phrase.replace(" ", "")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": phrase,
                "message": exc.detail,
                "details": None,
            },
        },
    )


# --- App Factory ---


def create_app() -> FastAPI:
    """
    Builds and wires the Mirumoji FastAPI application without performing I/O
    operations

    info: Operations Performed
        - App Construction

        - Static File Mounting

        - CORS Configuration

        - Domain / HTTP Exception Handler Registration

        - Router Registration

    Returns:
      FastAPI: The fully-configured application
    """
    app = FastAPI(
        title="Mirumoji",
        description="Japanese sentence breakdown, audio processing and LLM.",
        lifespan=lifespan,
    )

    app.mount(
        "/media",
        # check_dir=False
        # Directory is created at startup by media.init_storage()
        StaticFiles(directory=media.BASE_PATH, check_dir=False),
        name="media",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(
        MirumojiServerError,
        mirumoji_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]

    app.include_router(health_router)
    app.include_router(audio_router)
    app.include_router(video_router)
    app.include_router(dict_router)
    app.include_router(llm_router)

    return app


app = create_app()


def run() -> None:
    """
    Entry point for the `mirumoji-server` console script

    Launches `Uvicorn` on `0.0.0.0:8000` with auto-reload enabled
    (development mode)

    For production deployments use the Docker image directly
    """
    import uvicorn

    uvicorn.run(
        "mirumoji.server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
