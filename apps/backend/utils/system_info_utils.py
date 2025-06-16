from __future__ import annotations
import os
import platform
import socket
import datetime
from typing import Any, Dict


def gpu_available() -> Dict[bool, str]:
    """
    Return True if a CUDA GPU is visible to torch, False otherwise.
    """
    try:
        import torch
        if torch.cuda.is_available():
            idx = torch.cuda.current_device()
            return {"available": True,
                    "name": torch.cuda.get_device_name(idx),
                    }
        else:
            return {'available': False,
                    "name": ""}
    except ImportError:
        return {'available': False,
                'name': ""}


def get_system_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "time": datetime.datetime.now().isoformat(timespec="seconds") + "Z",
        "hostname": socket.gethostname(),
        "platform": platform.platform(aliased=True, terse=True),
        "python": platform.python_version(),
        "cpu_cores": os.cpu_count(),
        "gpu_available": gpu_available()['available'],
        'gpu_name': gpu_available()["name"]
    }

    return info
