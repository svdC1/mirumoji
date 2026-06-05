"""
Minimal stubs for the `kotobase` library (only what the server uses)
"""

from typing import Any

class Kotobase:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def lookup(self, *args: Any, **kwargs: Any) -> Any: ...
