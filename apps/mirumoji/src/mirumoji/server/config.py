"""
This module defines helpers for environment and capability detection.

The capability helpers let the `Processor` route per capability by checking
which optional dependencies are installed (via ``importlib.util.find_spec``)
and which environment variables are configured, without importing the heavy
packages themselves.

Attributes:
  LOGGER (logging.Logger): Module's logger.
"""

import logging
import os
from importlib.util import find_spec

from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)


def check_env(
    expected: list,
    input: dict,
    dotenv_path: str | None = None,
) -> dict:
    """
    Check if environment variables are available.

    Args:
      expected (list): list of expected environment variables.
      input (dict): dictionary with custom valued variables which
                    don't need to be present in environment
      dotenv_path (str, optional): Optional custom path to look for .env file.

    Raises:
      ValueError: If a variable cannot be found.

    Returns:
      dict: dictionary with all checked variables.
    """
    # Load from dotenv
    load_dotenv(dotenv_path=dotenv_path)
    # Get available vars from env
    API_KEYS = {k: v for k, v in os.environ.items() if k in expected}
    LOGGER.info(f"Retrieved {','.join(API_KEYS.keys())} from ENV")
    missing = [k for k in expected if k not in API_KEYS]
    # Get missing from input
    if missing:
        LOGGER.info(f"{','.join(missing)} not found in ENV")
        for m in missing:
            if m not in input or not input[m]:
                raise ValueError(f"Could not find variable: {m}")
            API_KEYS[m] = input[m]
    return API_KEYS


def using_modal() -> bool:
    """
    Checks if MODAL_TOKEN_ID and MODAL_TOKEN_SECRET variables
    are present in the environment

    Returns:
     bool: True if variables are present, false otherwise.
    """
    load_dotenv()
    keys = ["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"]
    return keys[0] in os.environ and keys[1] in os.environ


# --- Capability detection ---


def has_module(name: str) -> bool:
    """
    Check whether an importable module is installed without importing it.

    Args:
      name (str): Top-level module/package name (e.g. ``"faster_whisper"``).

    Returns:
      bool: True if the module can be located on the import path.
    """
    try:
        return find_spec(name) is not None
    except ModuleNotFoundError:
        # A parent package in the path is missing.
        return False


def env_present(*keys: str) -> bool:
    """
    Check whether every given environment variable is set (and non-empty).

    Args:
      *keys (str): Environment variable names to require.

    Returns:
      bool: True only if all named variables are present and non-empty.
    """
    load_dotenv()
    return all(os.environ.get(k) for k in keys)


def whisper_local_available() -> bool:
    """
    Whether local Whisper transcription is possible in this deployment.

    Returns:
      bool: True if the ``whisper-local`` extra (``faster-whisper``) is
            installed.
    """
    return has_module("faster_whisper")
