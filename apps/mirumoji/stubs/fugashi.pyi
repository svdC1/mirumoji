"""
Minimal stubs for the `fugashi` library (only what the server uses)
"""

from typing import Any

class Tagger:
    def __init__(self, *args: Any) -> None: ...
    def __call__(self, text: str) -> list[Any]: ...
