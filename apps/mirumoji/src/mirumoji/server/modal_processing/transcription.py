"""
Defines `Modal` GPU jobs for `Whisper` transcription

info: Transcription-Only
    - Jobs return raw transcription

    - LLM post-processing (SRT-Fixing) is applied by the `Processor` afterwards
      through the provider-agnostic LLM layer, so the same path works for both
      local and `Modal` transcription
"""

import os
from pathlib import Path
from typing import Literal


def transcribe_job(
    rel_media_fp: str | os.PathLike[str],
    output_format: Literal["srt", "joined"] = "srt",
    *,
    load_model_kwargs: dict | None = None,
    transcribe_kwargs: dict | None = None,
) -> str:
    """
    Transcribe media on a `Modal` GPU and return raw SRT content

    info: `output_format`
        - When `output_format="srt"`, sentence-level `SRT` content is
          composed from transcription segments, returning a string ready to be
          saved as a `.srt` file

        - When `output_format="joined"`, transcription segment texts are
          joined with the Japanese full stop into a single string without any
          timing information

    Args:
        rel_media_fp (str | os.PathLike[str]): Path to the media relative to
            `HOST_MEDIA_PATH`
        output_format (Literal["srt_str", "joined_str"]): How to format the
            transcription output. Defaults to `srt_str`
        load_model_kwargs (dict | None): Argument overrides for
            `mirumoji.server.processing.whisper.load_model`
        transcribe_kwargs (dict | None): Overrides for
            `mirumoji.server.processing.whisper.transcribe`

    Returns:
        The raw transcription as `SRT` content

    Raises:
        WhisperUnavailableError: If the model can't be loaded
        TranscriptionError: If transcription fails
    """
    import logging

    from mirumoji.server.processing import whisper

    # Configure Container Logging
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{levelname}-{name}-{message}",
    )
    logger = logging.getLogger(__name__)
    logger.info(
        f"'transcribe_job' started for media: '{rel_media_fp}'",
    )

    load_model_kwargs = load_model_kwargs or {}

    model = whisper.load_model(**load_model_kwargs)
    input = Path(rel_media_fp)

    transcribe_kwargs = transcribe_kwargs or {}

    transcribe_kwargs.update(
        model=model,
        audio_path=input,
    )

    segments, _info = whisper.transcribe(**transcribe_kwargs)

    if output_format == "joined":
        return whisper.to_string(segments)

    return whisper.to_srt(segments)
