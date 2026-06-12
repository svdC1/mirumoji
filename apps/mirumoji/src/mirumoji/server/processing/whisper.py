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
"""

from __future__ import annotations

import copy
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
    "language": "ja",
    "beam_size": 5,
    "word_timestamps": False,
    "vad_filter": False,
    "no_speech_threshold": 0.3,
    "log_prob_threshold": -1.0,
    "condition_on_previous_text": False,
    "compression_ratio_threshold": 2.0,
}
"""
Default keyword-arguments for `faster_whisper.WhisperModel.transcribe`, tuned
for long-form Japanese media
"""


DEFAULT_MODEL_OPTS: dict[str, Any] = {
    "model_size_or_path": "large-v3",
    "device": "cuda",
    "compute_type": "float16",
}
"""
Default keyword-arguments for `faster_whisper.WhisperModel`, loads the
`large-v3` model on `cuda`, with `float16` as the compute-type
"""


def load_model(w_model_args: dict[str, Any] | None = None) -> WhisperModel:
    """
    Loads a `faster_whisper.WhisperModel` object

    Args:
        w_model_args (dict | None): Additional arguments for
            `WhisperModel`. Overrides the ones set in `DEFAULT_MODEL_OPTS`

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
        opts = copy.deepcopy(DEFAULT_MODEL_OPTS)

        if w_model_args:
            opts.update(w_model_args)

        return WhisperModel(**opts)
    except Exception as e:
        raise WhisperUnavailableError(
            f"Failed to load Whisper model `{opts['model']}`: {e}",
        ) from e


def transcribe(
    model: WhisperModel,
    audio_path: str | os.PathLike[str],
    *,
    w_transcribe_args: dict[str, Any] | None = None,
) -> tuple[list[Segment], TranscriptionInfo]:
    """
    Transcribe an audio file into a list of segments

    Args:
        model (WhisperModel): A loaded `WhisperModel` object
        audio_path (str | os.PathLike[str]): Path to the audio/video file
        w_transcribe_args (dict | None): Additional arguments for
            `WhisperModel.transcribe`. Overrides the ones set in
            `DEFAULT_TRANSCRIBE_OPTS`

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

    opts = copy.deepcopy(DEFAULT_TRANSCRIBE_OPTS)

    if w_transcribe_args:
        opts.update(w_transcribe_args)

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
