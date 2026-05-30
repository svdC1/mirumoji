"""
Defines helpers for environment and capability detection

The capability helpers let the `Processor` route per capability by checking
which optional dependencies are installed (via `importlib.util.find_spec`)
and which environment variables are configured, without importing the heavy
packages themselves
"""

import os
from importlib.util import find_spec

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
