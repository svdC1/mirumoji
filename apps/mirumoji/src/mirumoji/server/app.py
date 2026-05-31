"""
Defines the `FastAPI` Mirummoji Server API

Sets up database connection and manages application lifecycle
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

from mirumoji.exceptions import MirumojiServerError
from mirumoji.server.constants import DB_URL
from mirumoji.server.db import get_engine, init_db
from mirumoji.server.routers.audio_router import audio_router
from mirumoji.server.routers.dict_router import dict_router
from mirumoji.server.routers.gpt_router import gpt_router
from mirumoji.server.routers.health_router import health_router
from mirumoji.server.routers.llm_router import llm_router
from mirumoji.server.routers.profile_router import profile_router
from mirumoji.server.routers.video_router import video_router

from . import media
from .config import using_modal
from .logging_setup import setup_logging
from .processing.processor import Processor

setup_logging()
LOGGER = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────
# App setup
# ───────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    """
    Context Manager for managing API's lifecyle.

    Args:
      app (FastAPI): The API object.

    Yields:
      Any: Application
    """
    await init_db()
    media.init_storage()
    app.state.processor = Processor()
    yield
    await get_engine().dispose()
    await asyncio.to_thread(
        shutil.rmtree,
        media.TEMP_PATH,
        ignore_errors=True,
    )


app = FastAPI(
    title="Mirumoji",
    description="Japanese sentence breakdown, audio processing and GPT.",
    lifespan=lifespan,
)

app.mount(
    "/media",
    # check_dir=False: the directory is created at startup by
    # media.init_storage(), after this module is imported
    StaticFiles(directory=media.BASE_PATH, check_dir=False),
    name="media",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MirumojiServerError)
async def mirumoji_exception_handler(
    request: Request,
    exc: MirumojiServerError,
) -> JSONResponse:
    """
    Translate domain exceptions into the structured error envelope.

    Reads the HTTP contract (`http_status`, `code`) and optional `details`
    that each `MirumojiServerError` subclass carries, so domain code never
    constructs HTTP responses itself.

    Args:
      request (Request): Incoming request object.
      exc (MirumojiServerError): Raised domain exception.

    Returns:
      JSONResponse: The structured error response to return.
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


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Custom Exception Handler for all HTTP Errors

    Emits the same nested envelope as the domain handler so the frontend has a
    single error shape to parse. The machine-readable `code` is derived from
    the HTTP status phrase (e.g. 404 -> "NotFound").

    Args:
      request (Request): Incoming request object.
      exc (HTTPException): Raised Exception Object.

    Returns:
      JSONResponse: The exception response to return.
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


app.include_router(gpt_router)
app.include_router(audio_router)
app.include_router(health_router)
app.include_router(dict_router)
app.include_router(video_router)
app.include_router(profile_router)
app.include_router(llm_router)


LOGGER.info(f"Database URL: {DB_URL}")
LOGGER.info(f"USING_MODAL={using_modal()}")
LOGGER.info("Setup Complete")
LOGGER.info(f"Serving '{media.BASE_PATH}' at '/media'.")


def run() -> None:
    """Entry point for the ``mirumoji-server`` console script.

    Launches Uvicorn on ``0.0.0.0:8000`` with auto-reload enabled (development
    mode). For production deployments use the Docker image directly.
    """
    import uvicorn

    uvicorn.run(
        "mirumoji.server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
