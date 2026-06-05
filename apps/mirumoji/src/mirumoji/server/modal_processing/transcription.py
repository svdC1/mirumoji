"""
Defines `Modal` GPU jobs for `Whisper` transcription

info: Transcription-Only
    - Jobs return raw transcription

    - LLM post-processing (SRT-Fixing) is applied by the `Processor` afterwards
      through the provider-agnostic LLM layer, so the same path works for both
      local and `Modal` transcription
"""

import os
from typing import Any, Literal


def transcribe_job(
    rel_media_fp: str | os.PathLike[str],
    output_format: Literal["srt", "joined"] = "srt",
    *,
    w_model_args: dict[str, Any] | None = None,
    w_transcribe_args: dict[str, Any] | None = None,
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
        output_format (Literal["srt", "joined"]): `srt` for sentence-level SRT
            content, `joined` for a single joined string. Defaults to `srt`
        w_model_args (dict | None): Additional arguments for
            `WhisperModel`. Overrides the ones set in
            `mirumoji.server.processing.whisper.DEFAULT_MODEL_OPTS`
        w_transcribe_args (dict | None): Additional arguments for
            `WhisperModel.transcribe`. Overrides the ones set in
            `mirumoji.server.processing.whisper.DEFAULT_TRANSCRIBE_OPTS`

    Returns:
        The raw transcription as `SRT` content

    Raises:
        WhisperUnavailableError: If the model can't be loaded
        TranscriptionError: If transcription fails
    """
    import logging
    from pathlib import Path

    from mirumoji.server.processing import whisper

    # Configure Container Logging
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{levelname}-{name}-{message}",
    )
    logger = logging.getLogger(__name__)
    logger.info(
        f"'transcribe_job' started for media : '{rel_media_fp}'"
        f" with output format : '{output_format}'"
    )

    model = whisper.load_model(w_model_args)
    input = Path(rel_media_fp)

    logger.info(
        f"'model_opts' : {w_model_args} | "
        f"'transcribe_opts': {w_transcribe_args}"
    )
    segments, _info = whisper.transcribe(
        model=model, audio_path=input, w_transcribe_args=w_transcribe_args
    )

    logger.info("Transcription Succeeded")

    if output_format == "joined":
        return whisper.to_string(segments)

    return whisper.to_srt(segments)
