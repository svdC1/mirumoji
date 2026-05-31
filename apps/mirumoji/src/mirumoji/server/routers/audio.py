"""
This module defines the `audio_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    audio_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import media
from ..db import UnitOfWork
from ..dependencies import get_processor, get_stream_file
from ..models.requests import TranscribeAudioRequest
from ..models.responses import AudioTranscriptResponse
from ..processing import audio
from ..processing.processor import Processor
from ..profile_manager import ensure_profile_exists

LOGGER = logging.getLogger(__name__)
audio_router = APIRouter(prefix="/audio")


@audio_router.post("/transcribe", response_model=AudioTranscriptResponse)
async def transcribe(
    opts: Annotated[TranscribeAudioRequest, Query()],
    file: Path = Depends(get_stream_file),
    profile_id: str = Depends(ensure_profile_exists),
    processor: Processor = Depends(get_processor),
) -> AudioTranscriptResponse:
    """
    Transcribes an uploaded audio file (no LLM step)

    Streams the upload, optionally cleans it, stores it under the profile,
    transcribes it via the configured backend, and persists the transcript.
    Call `/llm/explain_sentence` afterward for an explanation

    Args:
        opts (TranscribeAudioRequest): Query options (clean_audio + curated
            transcription options)
        file (Path): Path to the streamed upload
        profile_id (str): Validated profile id
        processor (Processor): The transcription orchestrator

    Returns:
        The saved transcript, its id, the original file name, and the stored
            audio's media URL

    Raises:
        FFmpegError: If audio cleaning fails
        TranscriptionError: If transcription fails
        WhisperUnavailableError: If no transcription backend is available
        ModalError: If a Modal job fails
        StorageError: If storing the audio fails
        DatabaseError: If persistence fails
    """
    op_id = uuid.uuid4().hex
    audios_dir = media.get_profile_dir(profile_id, "audios")
    persistent_loc = audios_dir / f"{op_id}_{file.name}"
    rel_path = media.get_relative_path(persistent_loc)

    try:
        # Optional Pre-Processing
        source = file
        if opts.clean_audio:
            ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
            cleaned = file.parent / f"cleaned_{op_id}_{file.name}.wav"
            await asyncio.to_thread(
                audio.filter_audio,
                ffmpeg,
                str(file),
                str(cleaned),
            )
            source = cleaned

        # Persist the (cleaned or original) audio under the profile
        await media.copy_file(source, rel_path)

        # Transcribe The Stored Audio With Available Backend
        w_transcribe_args = opts.model_dump(
            exclude_none=True,
            exclude={"clean_audio"},
        )
        text = await processor.transcribe(
            persistent_loc,
            output_format="joined",
            w_transcribe_args=w_transcribe_args,
        )

        # 4. Persist File + Transcript
        async with UnitOfWork() as uow:
            file_rec = await uow.files.add(
                profile_id=profile_id,
                name=file.name,
                path=str(rel_path),
                type="audio",
            )
            transcript_rec = await uow.transcripts.add(
                profile_id=profile_id,
                file_id=file_rec.id,
                text=text,
            )
            await uow.commit()

        return AudioTranscriptResponse(
            transcript_id=str(transcript_rec.id),
            transcript=text,
            original_file_name=file.name,
            audio_url=f"/media/{rel_path.as_posix()}",
        )
    finally:
        # Clean up the upload's temporary directory
        try:
            await media.delete_dir(media.get_relative_path(file.parent))
        except Exception:
            LOGGER.warning(
                f"Failed to clean temp dir '{file.parent}'",
                exc_info=True,
            )
