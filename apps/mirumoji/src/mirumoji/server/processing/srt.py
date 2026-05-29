"""
This module defines helper functions for SRT manipulation.

Attributes:
  LOGGER (logging.Logger): Logger's Module
"""

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    """
    Format seconds into SRT timestamp format.

    Args:
      seconds (float): The time to format in seconds.

    Returns:
      str: Formatted time in the format HH:MM:SS,mmm.
    """
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{ms:03}"


def generate_srt(result: dict[str, Any], srt_path: str) -> str:
    """
    Generate an SRT file from Whisper transcription result.

    Args:
      result (dict): The result object from FasterWhisper's transcribe
                     function.
      srt_path (str): Path to save the SRT file.

    Returns:
      str: The Path where the file was saved from `srt_path`

    """
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
