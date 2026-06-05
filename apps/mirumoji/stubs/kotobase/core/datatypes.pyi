"""
Minimal stubs for `kotobase.core.datatypes` (only what the server uses)
"""

from typing import Any

class JMDictEntryDTO:
    def __getattr__(self, name: str) -> Any: ...

class JMNeDictEntryDTO:
    def __getattr__(self, name: str) -> Any: ...
