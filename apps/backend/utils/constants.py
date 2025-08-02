"""
This module defines constant and environemnt variables that are used
throughout the application for consistency.
"""

import os
from pathlib import Path
from textwrap import dedent


LOG_DIR = Path(os.getenv("MIRUMOJI_LOG_DIR", Path.home() / ".mirumoji_logs"))
BASE_MEDIA_DIR = Path(os.getenv("MIRUMOJI_BASE_MEDIA_DIR", "media_files"))
TEMP_DIR = BASE_MEDIA_DIR / 'temp'
_WHISPER_GPT_DEFAULT = dedent(
    """You are an expert subtitle editor for Japanese anime.
    You understand:
      - Conversational Japanese, character names, honorifics onomatopoeia and
        scene-specific slang.
      - How to pick the correct Kanji/Kana from phonetic transcriptions based
        on context.
      - Natural sentence flow and typical timing for subtitles.

    Your job is to **clean only the text** of each SRT cue:
      • Fix mis-recognized Kanji or Kana.
      • Merge cues that split a single sentence
        (new cue’s start = earlier, end = later).
      • Remove any pure gibberish or repeated song-lyric artifacts.
      • Insert correct punctuation (。？！、) and adjust spacing.

    **You must not**:
      - Change any start/end timestamps.
      - Renumber beyond simple sequential order.
      - Add or remove cues (only merge as above).
      - Add any commentary or explanations.

    Output **only** the cleaned `.srt` file content."""
    )

FWHISPER_GPT_DEFAULT_SYS_MSG = os.getenv(
    "MIRUMOJI_FWHISPER_GPT_DEFAULT_SYS_MSG", _WHISPER_GPT_DEFAULT
    )

MODAL_GPU = os.getenv("MIRUMOJI_MODAL_GPU", "A10G")
MODAL_IMAGE = os.getenv("MIRUMOJI_MODAL_IMAGE",
                        "docker.io/svdc1/mirumoji-modal-gpu:latest"
                        )

LOGGING_LEVEL = os.getenv("MIRUMOJI_LOGGING_LEVEL", "INFO").upper()
