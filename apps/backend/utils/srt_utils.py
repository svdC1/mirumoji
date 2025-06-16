from typing import (Dict,
                    Any)
import logging

logger = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    """Format seconds into SRT timestamp format: HH:MM:SS,mmm."""
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{ms:03}"


def generate_srt(result: Dict[str, Any], srt_path: str) -> str:
    """Generate an SRT file from Whisper transcription result."""
    srt_content = ""
    segments = result.get("segments", [])
    srt_lines = []
    for i, segment in enumerate(segments, start=1):
        start = format_time(segment["start"])
        end = format_time(segment["end"])
        text = segment["text"].strip()
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    srt_content = "\n".join(srt_lines)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    return srt_path
