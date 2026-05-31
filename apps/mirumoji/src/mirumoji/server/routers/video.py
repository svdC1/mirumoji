"""
This module defines the `video_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    video_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import media
from ..db import UnitOfWork
from ..dependencies import (
    ensure_profile_exists,
    get_processor,
    get_stream_file,
)
from ..models.requests import ConvertVideoRequest, GenerateSrtRequest
from ..models.responses import ConvertVideoResponse, GenerateSrtResponse
from ..processing import audio
from ..processing.processor import Processor

LOGGER = logging.getLogger(__name__)
video_router = APIRouter(prefix="/video")


@video_router.post("/generate_srt", response_model=GenerateSrtResponse)
async def generate_srt(
    opts: Annotated[GenerateSrtRequest, Query()],
    video_file: Path = Depends(get_stream_file),
    profile_id: str = Depends(ensure_profile_exists),
    processor: Processor = Depends(get_processor),
) -> GenerateSrtResponse:
    """
    Generates raw SRT subtitles from an uploaded video (no LLM step)

    Streams the upload, extracts its audio, transcribes it to SRT, and stores
    the SRT under the profile. Call `/llm/fix_srt` afterward to clean it up

    Args:
        opts (GenerateSrtRequest): Curated transcription options
        video_file (Path): Path to the streamed upload
        profile_id (str): Validated profile id
        processor (Processor): The transcription orchestrator

    Returns:
        The saved SRT file's id, the raw SRT content, and its media URL

    Raises:
        FFmpegError: If audio extraction fails
        TranscriptionError: If transcription fails
        WhisperUnavailableError: If no transcription backend is available
        ModalError: If a Modal job fails
        StorageError: If storing the SRT fails
        DatabaseError: If persistence fails
    """
    op_id = uuid.uuid4().hex
    subtitles_dir = media.get_profile_dir(profile_id, "subtitles")
    srt_loc = subtitles_dir / f"{op_id}.srt"
    rel_srt = media.get_relative_path(srt_loc)

    try:
        # Extract audio (returns the input unchanged if already audio)
        ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
        extracted = await asyncio.to_thread(
            audio.extract_audio,
            ffmpeg,
            str(video_file),
            str(video_file.with_suffix(".wav")),
        )

        # Transcribe to raw SRT
        w_transcribe_args = opts.model_dump(exclude_none=True)
        srt_content = await processor.transcribe(
            extracted,
            output_format="srt",
            w_transcribe_args=w_transcribe_args,
        )

        # Store the SRT + persist the file record
        await media.write_file(rel_srt, srt_content)
        async with UnitOfWork() as uow:
            file_rec = await uow.files.add(
                profile_id=profile_id,
                name=srt_loc.name,
                path=str(rel_srt),
                type="srt",
            )
            await uow.commit()

        return GenerateSrtResponse(
            file_id=str(file_rec.id),
            srt_content=srt_content,
            srt_url=f"/media/{rel_srt.as_posix()}",
        )
    finally:
        try:
            await media.delete_dir(media.get_relative_path(video_file.parent))
        except Exception:
            LOGGER.warning(
                f"Failed to clean temp dir '{video_file.parent}'",
                exc_info=True,
            )


@video_router.post("/convert_to_mp4", response_model=ConvertVideoResponse)
async def convert_to_mp4(
    opts: Annotated[ConvertVideoRequest, Query()],
    video_file: Path = Depends(get_stream_file),
    profile_id: str = Depends(ensure_profile_exists),
    processor: Processor = Depends(get_processor),
) -> ConvertVideoResponse:
    """
    Converts an uploaded video to MP4 and stores it under the profile

    Args:
        opts (ConvertVideoRequest): Conversion options (resolution, bitrate)
        video_file (Path): Path to the streamed upload
        profile_id (str): Validated profile id
        processor (Processor): The conversion orchestrator

    Returns:
        The converted MP4's media URL

    Raises:
        FFmpegError: If conversion fails
        ModalError: If a Modal job fails
        StorageError: If storing the converted file fails
        DatabaseError: If persistence fails
    """
    op_id = uuid.uuid4().hex
    converted_dir = media.get_profile_dir(profile_id, "converted")
    out_loc = converted_dir / f"{video_file.stem}_{op_id}_converted.mp4"
    rel_out = media.get_relative_path(out_loc)

    try:
        # Convert via the configured backend
        to_mp4_kwargs = opts.model_dump(exclude_none=True)
        await processor.convert_to_mp4(
            video_file,
            out_loc,
            to_mp4_kwargs=to_mp4_kwargs,
        )

        # Persist the converted file record
        async with UnitOfWork() as uow:
            await uow.files.add(
                profile_id=profile_id,
                name=out_loc.name,
                path=str(rel_out),
                type="mp4",
            )
            await uow.commit()

        return ConvertVideoResponse(
            converted_video_url=f"/media/{rel_out.as_posix()}",
        )
    finally:
        try:
            await media.delete_dir(media.get_relative_path(video_file.parent))
        except Exception:
            LOGGER.warning(
                f"Failed to clean temp dir '{video_file.parent}'",
                exc_info=True,
            )
