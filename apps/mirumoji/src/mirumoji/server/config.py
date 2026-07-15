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
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from importlib.util import find_spec
from typing import Any, Literal

from dotenv import load_dotenv

from .. import __version__
from ..exceptions import ModalError, WhisperUnavailableError
from .constants import (
    DEFAULT_BREAKDOWN_SYS_MSG,
    DEFAULT_MODAL_SCALEDOWN_WINDOW,
    DEFAULT_SRT_SYS_MSG,
    MAX_LLM_CONCURRENCY,
)

LOGGER = logging.getLogger(__name__)

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


def _env_int(key: str, default: int) -> int:
    """
    Reads a non-negative integer from the environment, falling back on error

    Args:
        key (str): Environment variable name
        default (int): Value to use when the variable is unset or invalid

    Returns:
        The parsed integer, or `default` when unset or not a valid integer
    """
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        LOGGER.warning(f"Invalid {key} '{raw}', Using Default {default}")
        return default


@dataclass(frozen=True)
class Settings:
    """
    Resolved, environment-dependent server configuration

    Attributes:
        logging_level (str): Python logging level name
        modal_gpu (str): GPU type requested for Modal jobs
        modal_image (str): Docker image used for Modal containers
        modal_scaledown_window (int): Seconds an idle Modal container is kept
            warm before it scales down
        max_llm_concurrency (int): How many LLM requests run at once when
            fixing a batch of subtitles
        srt_sys_msg (str): System message for SRT-fixing
        breakdown_sys_msg (str): System message for word-nuance breakdowns
    """

    logging_level: str
    modal_gpu: str
    modal_image: str
    modal_scaledown_window: int
    max_llm_concurrency: int
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
            f"docker.io/svdc1/mirumoji-modal-gpu:{__version__}",
        ),
        modal_scaledown_window=_env_int(
            "MIRUMOJI_MODAL_SCALEDOWN_WINDOW",
            DEFAULT_MODAL_SCALEDOWN_WINDOW,
        ),
        max_llm_concurrency=_env_int(
            "MIRUMOJI_MAX_LLM_CONCURRENCY",
            MAX_LLM_CONCURRENCY,
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


# --- System Information ---


def gpu_available() -> dict[str, bool | str]:
    """
    Checks whether a CUDA GPU is available to the local transcription engine
    (`CTranslate2`, which powers `faster-whisper`)

    info: Return Values
        This function returns a dictionary with the following keys

        - `available (bool)` &rarr; `True` if `ctranslate2` is installed and
          reports at least one usable CUDA device, `False` otherwise

        - `name (str)` &rarr; the device name from `nvidia-smi` when it can be
          queried, `''` otherwise

    Returns:
        dict with keys "available" and "name"
    """
    try:
        import ctranslate2
    except ImportError:
        return {"available": False, "name": ""}

    if ctranslate2.get_cuda_device_count() <= 0:
        return {"available": False, "name": ""}

    name = ""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            name = lines[0].strip()
    except (OSError, subprocess.SubprocessError):
        name = ""

    return {"available": True, "name": name}


def nvenc_available(ffmpeg_path: str) -> bool:
    """
    Checks whether the NVIDIA `NVENC` H.264 encoder is actually usable by the
    given `FFMPEG` build on the current machine

    question: Why A Real Probe
        - A CUDA device being present (`gpu_available`) does not mean an
          encoder exists. The data center compute GPUs (`A100`, `H100`, `Bx00`)
          expose `NVDEC` for decoding but have no `NVENC` encoder at all

        - This runs a tiny synthetic encode and checks the exit code, so it
          reports the true capability of whatever GPU and `FFMPEG` build are
          present instead of guessing from a hard-coded GPU list

    info: Where To Call It
        - Run this in the same process that runs the conversion, since that is
          where `FFMPEG` actually executes

        - For the `local` backend that is the host, for the `modal` backend
          that is the GPU container

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable

    Returns:
        `True` if `h264_nvenc` initialises and encodes a probe frame, `False`
            otherwise
    """
    # The probe frame must clear NVENC's minimum supported dimensions (~145x49
    # for H.264). A smaller frame is rejected with "Frame Dimension less than
    # the minimum supported value", which would make this report False on a GPU
    # whose encoder actually works
    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=black:s=256x256:d=0.1",
        "-frames:v",
        "1",
        "-c:v",
        "h264_nvenc",
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:
        LOGGER.warning(f"NVENC Probe Could Not Run, Converting On CPU: {e}")
        return False

    if result.returncode != 0:
        LOGGER.warning(
            f"NVENC Probe Failed, Converting On CPU: {result.stderr.strip()}"
        )
        return False

    return True


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
