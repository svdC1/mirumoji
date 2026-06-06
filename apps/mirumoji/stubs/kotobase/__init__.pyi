"""
Minimal stubs for the `kotobase` library (only what the server uses)
"""
from . import api
from .api import Kotobase

__all__ = [
    'Kotobase',
    'api',
    ]
