"""
This module defines helper functions for colleting information
about the system running the program
"""

from __future__ import annotations

import datetime
import os
import platform
import socket
from typing import Any


def gpu_available() -> dict[str, bool | str]:
    """
    Uses PyTorch to checks if there's a GPU available in the machine running
    the program

    info: Return Values
        This function returns a dictionary with the following keys

        - `available (bool)` &rarr; `True` if `torch` can be imported and
          `torch.cuda.is_available` evaluates to `True`, `False` otherwise

        - `name (str)` &rarr;
          `torch.cuda.get_device_name(torch.cuda.current_device())` when
          `available=True`, `''` otherwise.

    Returns:
        dict with keys "available" and "name".
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
    info = {
        "time": datetime.datetime.now().isoformat(timespec="seconds") + "Z",
        "hostname": socket.gethostname(),
        "platform": platform.platform(aliased=True, terse=True),
        "python": platform.python_version(),
        "cpu_cores": os.cpu_count(),
        "gpu_available": gpu_available()["available"],
        "gpu_name": gpu_available()["name"],
    }

    return info
