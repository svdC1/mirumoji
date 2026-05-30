"""
Defines stateless helpers for local Whisper transcription with `faster-whisper`

abstract: Usage
    - The heavy `WhisperModel` is owned by the `Processor` and is loaded once
      during the first transcription request

    - This module only exposes pure functions that operate on a model handle or
      its output

    - Post-processing concerns (LLM SRT-fixing, file writing) live in the
      `Processor` and use other stateless helper from the `processing` module

info: Local Imports
    - `faster-whisper` is an optional dependency (`whisper-local` extra), so
      it's imported lazily inside `load_model`

    - Deployments that offload to Modal don't need it installed

Attributes:
    DEFAULT_TRANSCRIBE_OPTS (dict): Default `faster-whisper` transcribe options
        tuned for long-form Japanese media
"""

from __future__ import annotations

import datetime
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import srt

from ...exceptions import TranscriptionError, WhisperUnavailableError

if TYPE_CHECKING:
    from faster_whisper import WhisperModel
    from faster_whisper.transcribe import (
        Segment,
        TranscriptionInfo,
    )

LOGGER = logging.getLogger(__name__)

DEFAULT_TRANSCRIBE_OPTS: dict[str, Any] = {
    "beam_size": 5,
    "word_timestamps": False,
    "vad_filter": False,
    "no_speech_threshold": 0.3,
    "log_prob_threshold": -1.0,
    "condition_on_previous_text": False,
    "compression_ratio_threshold": 2.0,
}


def load_model(
    model_name: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
) -> WhisperModel:
    """
    Load a `faster-whisper` `WhisperModel`

    Args:
        model_name (str): Whisper model name
        device (str): Device to run on (`cuda`, `cpu`, or `auto`)
        compute_type (str): Compute type (e.g `float16`, `int8`)

    Returns:
        A loaded `WhisperModel` object

    Raises:
        WhisperUnavailableError: If `faster-whisper` is not installed or the
            model fails to load
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise WhisperUnavailableError(
            "Local Whisper transcription requires the 'whisper-local' extra "
            "(faster-whisper) to be installed",
        ) from e
    try:
        return WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
    except Exception as e:
        raise WhisperUnavailableError(
            f"Failed to load Whisper model '{model_name}': {e}",
        ) from e


def transcribe(
    model: WhisperModel,
    audio_path: str | os.PathLike[str],
    *,
    language: str = "ja",
    options: dict[str, Any] | None = None,
) -> tuple[list[Segment], TranscriptionInfo]:
    """
    Transcribe an audio file into a list of segments

    Args:
        model (WhisperModel): A loaded `WhisperModel` object
        audio_path (str | os.PathLike[str]): Path to the audio/video file
        language (str): Language code to transcribe in
        options (dict | None): Overrides for `DEFAULT_TRANSCRIBE_OPTS`

    Returns:
        Tuple containg the list of segment objects (each with `.start`, `.end`,
            `.text`) and the transcription info as returned by
            `model.transcribe`

    Raises:
        TranscriptionError: If the file is missing or transcription fails
    """
    path = Path(audio_path).resolve()
    if not path.is_file():
        raise TranscriptionError(f"Audio File Not Found: '{audio_path}'")

    opts = {**DEFAULT_TRANSCRIBE_OPTS, "language": language}
    if options:
        opts.update(options)

    try:
        segments, info = model.transcribe(audio=str(path), **opts)
        return list(segments), info
    except Exception as e:
        raise TranscriptionError(f"Transcription Failed: {e}") from e


def to_srt(segments: list[Segment]) -> str:
    """
    Composes sentence-level `SRT` content from transcription segments

    Args:
        segments (list): Segment objects from `transcribe`

    Returns:
        The composed `.srt` content as a string
    """
    subtitles = [
        srt.Subtitle(
            index=i,
            start=datetime.timedelta(seconds=seg.start),
            end=datetime.timedelta(seconds=seg.end),
            content=seg.text,
        )
        for i, seg in enumerate(segments, start=1)
    ]
    return srt.compose(subtitles)


def to_string(segments: list[Segment]) -> str:
    """
    Joins transcription segments into a single string

    Args:
        segments (list): Segment objects from `transcribe`

    Returns:
        The segment texts joined with the Japanese full stop
    """
    return "。".join(seg.text for seg in segments)
