"""
Minimal stubs for the `genanki` library (only what the server uses)
"""

from typing import Any

class Model:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class Deck:
    notes: list[Any]
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def add_note(self, note: Any) -> None: ...

class Note:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class Package:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def write_to_file(self, path: Any) -> None: ...
