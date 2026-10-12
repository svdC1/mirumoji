"""
Minimal stubs for the `ctranslate2` library (only what the server uses)
"""

from . import models as models

def get_cuda_device_count() -> int: ...

__all__ = ["get_cuda_device_count", "models"]
