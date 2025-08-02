"""
Module defining the FastAPI API. Sets up Database connection
and manages application lifecycle.

Attributes:
  LOGGER (logging.Logger): Root Logging object.
  LOGGING_LEVEL (str): Level for the Logging object.
"""
import logging
from typing import AsyncGenerator, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routers.gpt_router import gpt_router
from routers.audio_router import audio_router
from routers.health_router import health_router
from routers.dict_router import dict_router
from routers.video_router import video_router
from routers.profile_router import profile_router
import asyncio
import shutil
from contextlib import asynccontextmanager
from db.db import connect_db, disconnect_db, DATABASE_URL
from utils.env_utils import using_modal
from utils.logging_utils import setup_logging
from utils.file_utils import MediaFileHandler

setup_logging()
LOGGER = logging.getLogger(__name__)
MEDIA_FILE_HANDLER = MediaFileHandler()

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
    await connect_db()
    LOGGER.info(f"Storage ensured at: '{MEDIA_FILE_HANDLER.base_path}'")
    yield
    await disconnect_db()
    await asyncio.to_thread(shutil.rmtree,
                            MEDIA_FILE_HANDLER.temp_path,
                            ignore_errors=True
                            )


app = FastAPI(
    title="Mirumoji",
    description="Japanese sentence breakdown, audio processing and GPT.",
    lifespan=lifespan
)

app.mount("/media",
          StaticFiles(directory=MEDIA_FILE_HANDLER.base_path),
          name="media")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request,
                                 exc: HTTPException
                                 ) -> JSONResponse:
    """
    Custom Exception Handler for all HTTP Errors.

    Args:
      request (Request): Incoming request object.
      exc (HTTPException): Raised Exception Object.

    Returns:
      JSONResponse: The exception response to return.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False,
                 "message": exc.detail},
    )

app.include_router(gpt_router)
app.include_router(audio_router)
app.include_router(health_router)
app.include_router(dict_router)
app.include_router(video_router)
app.include_router(profile_router)


LOGGER.info(f"Database URL: {DATABASE_URL}")
LOGGER.info(f"USING_MODAL={using_modal()}")
LOGGER.info("Setup Complete")
LOGGER.info(f"Serving '{MEDIA_FILE_HANDLER.base_path}' at '/media'.")
