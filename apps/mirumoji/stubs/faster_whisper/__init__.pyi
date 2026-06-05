"""
Minimal stubs for the `faster_whisper` library (only what the server uses)
"""

from collections.abc import Iterable
from typing import Any

from faster_whisper.transcribe import Segment, TranscriptionInfo

class WhisperModel:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def transcribe(
        self,
        audio: Any,
        **kwargs: Any,
    ) -> tuple[Iterable[Segment], TranscriptionInfo]: ...
