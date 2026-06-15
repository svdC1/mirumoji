"""
Defines `Modal` GPU jobs for `Whisper` transcription

info: Transcription-Only
    - Jobs return raw transcription

    - LLM post-processing (SRT-Fixing) is applied by the `Processor` afterwards
      through the provider-agnostic LLM layer, so the same path works for both
      local and `Modal` transcription
"""

from typing import Any, Literal


def transcribe_job(
    vol_fp: str,
    vol_id: str,
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

    info: File Transfer
        - The input media is read out of the per-job ephemeral volume into a
          container-local temp directory before being handed to `Whisper`

        - That directory is removed once the job finishes

    Args:
        vol_fp (str): Path of the input media inside the per-job ephemeral
            volume
        vol_id (str): ID of the per-job ephemeral volume
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
        ModalVolumeError: If the input can't be read from the volume
        WhisperUnavailableError: If the model can't be loaded
        TranscriptionError: If transcription fails
    """
    import logging
    import shutil
    import tempfile
    from pathlib import Path

    import modal

    from mirumoji.server.modal_processing.volume_io import download_from_volume
    from mirumoji.server.processing import whisper

    # Configure Container Logging
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{levelname}-{name}-{message}",
    )
    logger = logging.getLogger(__name__)

    vol = modal.Volume.from_id(vol_id)
    workdir = Path(tempfile.mkdtemp(prefix="mirumoji_transcribe_"))

    try:
        # Stream The Input Out Of The Volume Into Container-Local Storage
        local_fp = workdir / Path(vol_fp).name
        download_from_volume(vol, vol_fp, local_fp)

        logger.info(
            f"'transcribe_job' Started For '{local_fp}' "
            f"(output format '{output_format}')"
        )

        model = whisper.load_model(w_model_args)
        logger.info(
            f"Whisper Model Loaded | "
            f"'model_opts': {w_model_args} | "
            f"'transcribe_opts': {w_transcribe_args}"
        )

        segments, _info = whisper.transcribe(
            model=model,
            audio_path=local_fp,
            w_transcribe_args=w_transcribe_args,
        )
        logger.info("Transcription Succeeded")

        if output_format == "joined":
            return whisper.to_string(segments)
        return whisper.to_srt(segments)

    finally:
        shutil.rmtree(workdir, ignore_errors=True)
