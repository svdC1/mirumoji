"""
Defines and starts the Mirumoji Launcher GUI
"""

from fastapi import (FastAPI,
                     HTTPException,
                     Request
                     )
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
from typing import (AsyncGenerator,
                    Any
                    )
from contextlib import asynccontextmanager
from mirumoji.gui.core import ensure_repo
import sys
import shutil
import asyncio
from mirumoji.gui.paths import (LOG_DIR,
                                REPO_URL,
                                REPO_DIR,
                                APP_DIR,
                                WEB_DIR
                                )
from mirumoji.gui.router import router
from flaskwebgui import FlaskUI
import uvicorn
from threading import Thread
from multiprocessing import freeze_support

# --- Environment Variables ---
LOGGER = logging.getLogger(__name__)
LOGGING_LEVEL = os.getenv("MIRUMOJI_LAUNCHER_LOG_LEVEL", "INFO").upper()
PORT = int(os.getenv("MIRUMOJI_LAUNCHER_PORT", 4667))

# --- Logging ---


def setup_logging() -> None:
    """
    Setups custom logging for the launcher.

    Includes a formatted stream handler and a file
    handler directed to `~/.mirumoji_launcher/logs/main.log`
    """
    level = getattr(logging, LOGGING_LEVEL, logging.INFO)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "{asctime} -- {levelname} -- ({name}:{funcName}) || {message}",
        style="{",
        datefmt="%H:%M:%S[%z]"
    )

    # Create and add handlers
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = str((LOG_DIR / "main.log").resolve())
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

# --- API Setup ---


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    """
    Context Manager for managing API's lifecyle.

    Args:
      app (FastAPI): The API object.

    Yields:
      Any: Application
    """
    # --- Setup Repository ---
    try:
        APP_DIR.mkdir(exist_ok=True)
        ensure_repo(REPO_URL,
                    REPO_DIR
                    )
        LOGGER.info(f"Repo ensured at: '{REPO_DIR}'")
        yield
    except Exception as e:
        LOGGER.error(f"Application failed to start: '{e}'")
        sys.exit(1)
    await asyncio.to_thread(shutil.rmtree,
                            REPO_DIR,
                            ignore_errors=True
                            )


app = FastAPI(
    title="Mirumoji Launcher",
    description="GUI Launcher for the `mirumoji` application",
    lifespan=lifespan
)

app.include_router(router)

app.mount("/",
          StaticFiles(directory=WEB_DIR, html=True),
          name="stactic"
          )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    rbody = "{}"
    if request.method == "POST":
        rbody = await request.json()
        url = request.url.path
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False,
                 "message": exc.detail,
                 "url": url,
                 "body": rbody,
                 },
        media_type="application/json"
    )


def run_server():
    """
    Function to run the Uvicorn server in a thread,
    binding to the correct host and port.
    """
    server_thread = Thread(
        target=uvicorn.run,
        kwargs={"app": "mirumoji.gui.main:app",
                "host": "127.0.0.1",
                "port": PORT},
        daemon=True
        )
    server_thread.start()


if __name__ == "__main__":
    freeze_support()
    # --- Setup Logging ---
    setup_logging()
    # --- Start Web GUI ---
    FlaskUI(
        app=app,
        port=PORT,
        server=run_server,
        fullscreen=False,
        width=1200,
        height=800
        ).run()
