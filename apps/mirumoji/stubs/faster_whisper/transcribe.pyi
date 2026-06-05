"""
Minimal stubs for `faster_whisper.transcribe` (only what the server uses)
"""

class Segment:
    start: float
    end: float
    text: str

class TranscriptionInfo: ...
