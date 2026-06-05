"""
Defines helpers for environment and capability detection

The capability helpers let the `Processor` route per capability by checking
which optional dependencies are installed (via `importlib.util.find_spec`)
and which environment variables are configured, without importing the heavy
packages themselves
"""

import datetime
import logging
import os
import platform
import socket
import sys
from dataclasses import dataclass
from functools import lru_cache
from importlib.util import find_spec
from typing import Any, Literal

from dotenv import load_dotenv
from tqdm.auto import tqdm

from ..exceptions import ModalError, WhisperUnavailableError
from ..paths import HOST_LOG_PATH
from .constants import (
    DEFAULT_BREAKDOWN_SYS_MSG,
    DEFAULT_SRT_SYS_MSG,
)

# --- Environment Loading + Settings ---


@lru_cache(maxsize=1)
def _load_env_once() -> None:
    """
    Loads variables from a `.env` file into the environment

    warning: Single Execution
        - This function is meant to be executed only once during the
          application lifetime

        - It's cached so that environment reads throughout the server can
          consume `.env` values without re-reading the file

        - Variables already set in the real environment are no overriden
    """
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    """
    Resolved, environment-dependent server configuration

    Attributes:
        logging_level (str): Python logging level name
        modal_gpu (str): GPU type requested for Modal jobs
        modal_image (str): Docker image used for Modal containers
        srt_sys_msg (str): System message for SRT-fixing
        breakdown_sys_msg (str): System message for word-nuance breakdowns
    """

    logging_level: str
    modal_gpu: str
    modal_image: str
    srt_sys_msg: str
    breakdown_sys_msg: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Resolves environment-dependent settings once, after loading `.env`

    Reads the environment lazily (not at import) so that values reflect a
    `.env` loaded at startup + variables that the launcher sets before the
    process starts. Cached for the process lifetime

    Returns:
        The resolved `Settings`
    """
    _load_env_once()
    return Settings(
        logging_level=os.environ.get(
            "MIRUMOJI_LOGGING_LEVEL",
            "INFO",
        ).upper(),
        modal_gpu=os.environ.get("MIRUMOJI_MODAL_GPU", "A10G"),
        modal_image=os.environ.get(
            "MIRUMOJI_MODAL_IMAGE",
            "docker.io/svdc1/mirumoji-modal-gpu:latest",
        ),
        srt_sys_msg=os.environ.get(
            "MIRUMOJI_SRT_DEFAULT_SYS_MSG",
            DEFAULT_SRT_SYS_MSG,
        ),
        breakdown_sys_msg=os.environ.get(
            "MIRUMOJI_BREAKDOWN_DEFAULT_SYS_MSG",
            DEFAULT_BREAKDOWN_SYS_MSG,
        ),
    )


# --- Capability Detection ---


def has_module(name: str) -> bool:
    """
    Checks whether an importable module is installed without importing it

    Args:
        name (str): Top-level module/package name (e.g. `"faster_whisper"`)

    Returns:
        `True` if the module can be located on the import path
    """
    try:
        return find_spec(name) is not None
    except ModuleNotFoundError:
        # Parent Package In The Path Is Missing
        return False


def env_present(*keys: str) -> bool:
    """
    Check whether every given environment variable (`*keys`) is set and
    non-empty

    Args:
        *keys (str): Environment variable names to require

    Returns:
        `True` only if all named variables are present and non-empty
    """
    _load_env_once()
    return all(os.environ.get(k) for k in keys)


def whisper_local_available() -> bool:
    """
    Checks whether local `Whisper` transcription is possible in this
    deployment

    Returns:
        `True` if `faster-whisper` is installed
    """
    return has_module("faster_whisper")


def using_modal() -> bool:
    """
    Checks if `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` variables
    are present in the environment

    Returns:
        `True` if variables are present, `False` otherwise
    """
    return env_present("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET")


def transcribe_backend() -> Literal["local", "modal", "none"]:
    """
    Resolves which transcription backend the server should use

    tip: Transcribe Backend
        - Reads `MIRUMOJI_TRANSCRIBE_BACKEND` (`auto` | `local` | `modal`)

        - `auto` or unset picks `modal` when Modal tokens are configured, or
          `local` when faster-whisper is installed, otherwise `none`

        - Explicit `local` or `modal` overrides are validated and raise when
          that backend isn't available

    Returns:
        The resolved backend identifier

    Raises:
        WhisperUnavailableError: If `local` is forced but faster-whisper isn't
            installed
        ModalError: If `modal` is forced but Modal tokens aren't configured
        ValueError: If the variable holds an unrecognised value
    """
    _load_env_once()
    choice = (
        os.environ.get(
            "MIRUMOJI_TRANSCRIBE_BACKEND",
            "auto",
        )
        .strip()
        .lower()
    )

    if choice == "modal":
        if not using_modal():
            raise ModalError(
                "MIRUMOJI_TRANSCRIBE_BACKEND=modal but MODAL_TOKEN_ID / "
                "MODAL_TOKEN_SECRET are not configured",
            )
        return "modal"

    if choice == "local":
        if not whisper_local_available():
            raise WhisperUnavailableError(
                "MIRUMOJI_TRANSCRIBE_BACKEND=local but faster-whisper "
                "(the whisper-local extra) is not installed",
            )
        return "local"

    if choice == "auto":
        if using_modal():
            return "modal"
        if whisper_local_available():
            return "local"
        return "none"

    raise ValueError(
        f"Invalid MIRUMOJI_TRANSCRIBE_BACKEND '{choice}'; "
        f"expected one of: auto, local, modal",
    )


# --- Logging ---


class TqdmStreamHandler(logging.StreamHandler):
    """
    Handler for displaying `tqdm` progress bars properly with python logging
    """

    def __init__(self) -> None:
        super().__init__(sys.stdout)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg, file=self.stream)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """
    Configures the `mirumoji` logger with custom formatters and handlers

    Reads the logging level from the resolved settings, attaches a file handler
    (under `HOST_LOG_PATH`) and a `tqdm`-aware stream handler, and creates the
    logging directory if it doesn't already exist
    """
    level = getattr(logging, get_settings().logging_level, logging.INFO)

    # Get the logger and set its level
    logger = logging.getLogger("mirumoji")
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        "{asctime} -- {levelname} -- ({name}:{funcName}) || {message}",
        style="{",
        datefmt="%H:%M:%S[%z]",
    )

    # Create DIR and add handlers
    HOST_LOG_PATH.mkdir(parents=True, exist_ok=True)
    log_file = str((HOST_LOG_PATH / "backend.log").resolve())
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = TqdmStreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


# --- System Information ---


def gpu_available() -> dict[str, bool | str]:
    """
    Uses PyTorch to check if there's a GPU available in the machine running
    the program

    info: Return Values
        This function returns a dictionary with the following keys

        - `available (bool)` &rarr; `True` if `torch` can be imported and
          `torch.cuda.is_available` evaluates to `True`, `False` otherwise

        - `name (str)` &rarr;
          `torch.cuda.get_device_name(torch.cuda.current_device())` when
          `available=True`, `''` otherwise

    Returns:
        dict with keys "available" and "name"
    """
    try:
        import torch

        if torch.cuda.is_available():
            idx = torch.cuda.current_device()
            return {
                "available": True,
                "name": torch.cuda.get_device_name(idx),
            }
        else:
            return {"available": False, "name": ""}
    except ImportError:
        return {"available": False, "name": ""}


def get_system_info() -> dict[str, Any]:
    """
    Uses `os`, `socket`, and `platform` to collect basic information about the
    system running the program

    Returns:
        dict with information about the system
    """
    gpu = gpu_available()
    info = {
        "time": datetime.datetime.now().isoformat(timespec="seconds") + "Z",
        "hostname": socket.gethostname(),
        "platform": platform.platform(aliased=True, terse=True),
        "python": platform.python_version(),
        "cpu_cores": os.cpu_count(),
        "gpu_available": gpu["available"],
        "gpu_name": gpu["name"],
    }

    return info
