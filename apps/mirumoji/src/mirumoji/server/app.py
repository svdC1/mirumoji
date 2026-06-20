"""
Defines the `FastAPI` Mirumoji Server API

Exposes custom exception handlers, a `create_app` factory that builds and
wires the application, and a `run` function to start the application

abstract: Module Import
    - Importing this module has no side effects beyond constructing the
      `FastAPI` app object so that it can serve as an entry-point for
      uvicorn and Docker

    - logging configuration, storage/database initialisation, and startup
      logging all happen inside the lifespan handler
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
from ..log import setup_logging
from ..paths import HOST_LOG_PATH
from . import media
from .config import get_settings
from .db import get_engine, init_db
from .jobs import HANDLERS, JobQueueManager
from .processing.processor import Processor
from .routers.dict import dict_router
from .routers.health import health_router
from .routers.jobs import jobs_router
from .routers.llm import llm_router
from .routers.profile import profile_router

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

        - Lifespan-Scoped `JobQueueManager` Initialisation

    info: Shutdown Operations
        - Stops the Async Job Queue Task, marking any running jobs as failed

        - Disposes the Database Engine

        - Clears Temporary Media

    Args:
      app (FastAPI): The API object

    Yields:
        Control back to the running application
    """

    # Create Log Directory + Register Handlers
    setup_logging(
        log_file="backend.log",
        console=True,
        level=get_settings().logging_level,
    )
    LOGGER.info(f"Storing Logs At '{HOST_LOG_PATH / 'backend.log'}'")

    # Create / Initialise Database
    await init_db()

    # Create Media Directory If It Doesn't Exist
    media.init_storage()
    LOGGER.info(f"Serving '{media.BASE_PATH}' At '/media'")

    # Intialise Application-Scoped Stateful Processor
    app.state.processor = Processor()

    # Initialise Application-Scoped Async Job Queue Task
    app.state.job_manager = JobQueueManager(app.state.processor)

    # Register Job Handlers
    for job_type, handler in HANDLERS.items():
        app.state.job_manager.register_handler(job_type, handler)

    LOGGER.info(f"Registered {len(HANDLERS)} Handlers To Job Manager")

    await app.state.job_manager.start()

    LOGGER.info("Configuration Complete")

    yield

    # Stop Job Queue Worker
    # Needs to run before disposing the engine since `stop` marks running jobs
    # failed in the database
    await app.state.job_manager.stop()

    # Dispose Engine
    await get_engine().dispose()
    LOGGER.info("Database Engine Disposed")

    # Delete Temporary Data
    try:
        await asyncio.to_thread(
            shutil.rmtree,
            media.TEMP_PATH,
        )
        LOGGER.info(f"Deleted Temporary Media At '{media.TEMP_PATH}'")
    except Exception:
        LOGGER.exception(
            f"Failed To Delete Temporary Media At '{media.TEMP_PATH}'"
        )

    LOGGER.info("Shut Down Complete")


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
    app.add_exception_handler(
        HTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )

    app.include_router(health_router)
    app.include_router(dict_router)
    app.include_router(llm_router)
    app.include_router(profile_router)
    app.include_router(jobs_router)

    return app
