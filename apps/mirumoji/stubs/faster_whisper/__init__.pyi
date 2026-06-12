"""
Minimal stubs for the `faster_whisper` library (only what the server uses)
"""

from .transcribe import (
    Segment,
    TranscriptionInfo,
    TranscriptionOptions,
    WhisperModel,
    Word,
)
from .vad import VadOptions

__all__ = [
    "Segment",
    "TranscriptionInfo",
    "TranscriptionOptions",
    "VadOptions",
    "WhisperModel",
    "Word",
]
