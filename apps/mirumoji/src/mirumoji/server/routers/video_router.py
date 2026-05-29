"""
This module defines the `video_router` of the Mirumoji API.

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
  video_router (APIRouter): The FastAPI Router Object.
"""

import asyncio
import logging
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, Header, HTTPException, status

from mirumoji.server.db.db import DbManager
from mirumoji.server.processing.audio import AudioTools
from mirumoji.server.processing.Processor import Processor
from mirumoji.server.profile_manager import ensure_profile_exists
from mirumoji.server.utils.env_utils import using_modal
from mirumoji.server.utils.file_utils import MediaFileHandler, get_stream_file

USING_MODAL = using_modal()
LOGGER = logging.getLogger(__name__)
video_router = APIRouter(prefix="/video")
MEDIA_FILE_HANDLER = MediaFileHandler()
processor = Processor()
db_manager = DbManager()


@video_router.post("/generate_srt")
async def generate_srt(
    video_file: Path = Depends(get_stream_file),
    profile_id: str = Header(..., alias="X-Profile-ID"),
) -> dict:
    """
    POST endpoint for generating an SRT string from a video file.

    Args:
      video_file (Path): Path of where the streamed file was saved
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Response with key `srt_content`

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     generating the SRT
    """
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required.",
        )
    await ensure_profile_exists(profile_id)

    op_id = str(uuid.uuid4())
    op_tmp_dir = MEDIA_FILE_HANDLER.get_temp_dir(video_file.parent.name)
    srt_dir = MEDIA_FILE_HANDLER.get_profile_dir(profile_id, "subtitles")
    srt_fp = srt_dir / f"{op_id}.srt"
    relative_srt_fp = MEDIA_FILE_HANDLER.get_relative_path(srt_fp)

    # Temporary location for the uploaded video within the operation's temp dir
    tmp_vid_upload_loc = video_file

    try:
        # 1. Save uploaded video to operation's temp dir

        LOGGER.info(f"Temp video for SRT: '{tmp_vid_upload_loc}'")

        # 2. Init AudioTools with operation's temp dir
        audio_tools = AudioTools()

        # 3. Extract audio
        extracted_audio_fpath = await asyncio.to_thread(
            audio_tools.extract_audio,
            input_path=str(tmp_vid_upload_loc),
            output_path=str(tmp_vid_upload_loc.with_suffix(".wav")),
        )
        if (
            not extracted_audio_fpath
            or not Path(extracted_audio_fpath).exists()
        ):
            LOGGER.error(f"Audio extraction failed for '{tmp_vid_upload_loc}'")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract audio from video.",
            )
        LOGGER.info(f"Audio extracted to '{extracted_audio_fpath}'")

        # 4. Transcribe extracted audio to SRT string
        # If Modal env variables are available use MODAL
        if USING_MODAL:
            LOGGER.info("Conversion sent to Modal")
            LOGGER.info(f"Local Filepath: '{extracted_audio_fpath}'")
            extracted_audio_fpath = MEDIA_FILE_HANDLER.get_modal_path(
                extracted_audio_fpath,
            )
            LOGGER.info(
                f"Media Filepath Adapted for Modal: '{extracted_audio_fpath}'",
            )
            srt_result = await processor.modal_transcribe_to_srt(
                media_fp=str(extracted_audio_fpath),
            )
        # Run locally
        else:
            # Processor will have `fwhisper` attribute
            LOGGER.info("Running Locally")
            LOGGER.info(f"Local Filepath: '{extracted_audio_fpath}'")
            srt_result = await asyncio.to_thread(
                processor.fwhisper.transcribe_to_srt,
                audio_path=str(extracted_audio_fpath),
                output_path=" ",
                string_result=True,
                fix_with_chat_gpt=True,
            )

        if not srt_result:
            LOGGER.error(
                f"SRT transcription failed for '{extracted_audio_fpath}'",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate SRT from audio.",
            )
        async with aiofiles.open(srt_fp, "w", encoding="utf-8") as f:
            await f.write(srt_result)
        LOGGER.info(f"SRT content generated for profile '{profile_id}'")

        # 5. Save metadata
        vid_rec_id = str(uuid.uuid4())
        values = {
            "id": vid_rec_id,
            "profile_id": profile_id,
            "file_name": srt_fp.name,
            "file_path": str(relative_srt_fp),
            "file_type": "srt",
        }
        await db_manager.create("profile_files", values)
        LOGGER.info(f"SRT record saved for profile '{profile_id}'")

        return {"srt_content": srt_result}

    except HTTPException:
        # Propagate Exceptions
        raise
    except Exception as e:
        LOGGER.exception(
            f"Error generating SRT for '{video_file.name}'"
            f"profile: '{profile_id}'",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during SRT generation: '{e!s}'",
        ) from e
    finally:
        # 6. Clean up temp operation directory
        await MEDIA_FILE_HANDLER.delete_dir(
            MEDIA_FILE_HANDLER.get_relative_path(op_tmp_dir),
        )


@video_router.post("/convert_to_mp4")
async def convert_to_mp4(
    video_file: Path = Depends(get_stream_file),
    profile_id: str = Header(..., alias="X-Profile-ID"),
) -> dict:
    """
    POST endpoint for converting a video file to MP4 format.

    Args:
      video_file (Path): Path where the streamed file was saved
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Response with key `converted_video_url`

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     converting the video
    """
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required.",
        )
    await ensure_profile_exists(profile_id)
    op_id = str(uuid.uuid4())
    op_tmp_dir = MEDIA_FILE_HANDLER.get_temp_dir(video_file.parent.name)

    # Temp location for the initially uploaded file
    tmp_uploaded_vid_loc = video_file

    # Final storage paths
    prof_conv_dir = MEDIA_FILE_HANDLER.get_profile_dir(profile_id, "converted")

    # Using unique names for stored files
    conv_fname_stem = video_file.stem
    conv_stored_fname = f"{conv_fname_stem}_{op_id[:8]}_converted.mp4"

    final_conv_stored_loc = prof_conv_dir / conv_stored_fname

    rel_conv_db_path = MEDIA_FILE_HANDLER.get_relative_path(
        final_conv_stored_loc,
    )

    try:
        # 1. Save uploaded video to temp location
        LOGGER.info(f"Temp video for conversion: '{tmp_uploaded_vid_loc}'")

        # 2. Convert video, saving to final converted location
        # If MODAL env variables are available use MODAL
        if USING_MODAL:
            LOGGER.info("Conversion sent to Modal")
            LOGGER.info(f"Video Filepath:'{tmp_uploaded_vid_loc}'")
            LOGGER.info(f"Output Path: '{final_conv_stored_loc}'")
            conv_path_obj = await processor.modal_convert_to_mp4(
                video_fp=str(tmp_uploaded_vid_loc),
                outpath=str(final_conv_stored_loc),
            )
        # Run Locally
        # If CPU version ->
        # NVENC is not available but to_mp4 falls back to normal enconding
        else:
            LOGGER.info("Running Locally")
            LOGGER.info(f"Video Filepath:'{tmp_uploaded_vid_loc}'")
            LOGGER.info(f"Output Path: '{final_conv_stored_loc}'")
            audio_tools = AudioTools()
            conv_path_obj = await asyncio.to_thread(
                audio_tools.to_mp4,
                input_path=str(tmp_uploaded_vid_loc),
                output_path=str(final_conv_stored_loc),
                use_nvenc=True,
            )

        if not conv_path_obj or not final_conv_stored_loc.exists():
            LOGGER.error(f"MP4 conversion failed for '{tmp_uploaded_vid_loc}'")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Video conversion to MP4 failed.",
            )
        LOGGER.info(f"Video converted to '{final_conv_stored_loc}'")

        # 3. Save metadata for converted files to DB
        conv_rec_id = str(uuid.uuid4())
        values = {
            "id": conv_rec_id,
            "profile_id": profile_id,
            "file_name": conv_stored_fname,
            "file_path": str(rel_conv_db_path),
            "file_type": "mp4",
        }
        await db_manager.create("profile_files", values)
        LOGGER.info(
            f"Converted video records saved for profile:'{profile_id}'",
        )

        # 4. Construct URL for frontend
        converted_video_url = f"/media/{rel_conv_db_path!s}"

        return {"converted_video_url": converted_video_url}

    except HTTPException:
        # Propagate Exceptions
        raise
    except Exception as e:
        LOGGER.exception(
            f"Error converting '{video_file.name}'for profile '{profile_id}'",
        )
        # Attempt to clean up partially created files
        for loc in [final_conv_stored_loc]:
            if loc.exists():
                try:
                    await MEDIA_FILE_HANDLER.delete_file(loc, check=True)
                except OSError:
                    LOGGER.error(f"Could not remove '{loc}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during video conversion: '{e!s}'",
        ) from e
    finally:
        # 5. Clean up temp operation directory
        if op_tmp_dir.exists():
            try:
                await MEDIA_FILE_HANDLER.delete_dir(
                    MEDIA_FILE_HANDLER.get_relative_path(op_tmp_dir),
                )
            except OSError as e_os:
                LOGGER.error(
                    f"Error cleaning temp dir '{op_tmp_dir}': '{e_os}'",
                )
