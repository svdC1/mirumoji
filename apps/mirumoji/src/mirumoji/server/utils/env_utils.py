"""
This module defines helper functions for environment management.

Attributes:
  LOGGER (logging.Logger): Module's logger.
"""

import logging
import os

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
