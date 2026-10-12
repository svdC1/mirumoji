"""
Minimal stubs for `ctranslate2.models` (only what the server uses)
"""

class Whisper:
    def unload_model(self, to_cpu: bool = False) -> None: ...

__all__ = ["Whisper"]
