"""
This module defines the `audio_router` of the Mirumoji API.

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
  audio_router (APIRouter): The FastAPI Router Object.
"""

import logging
import shutil
import uuid
import aiofiles
from pathlib import Path
from fastapi import (APIRouter,
                     UploadFile,
                     Form,
                     Depends,
                     HTTPException,
                     status
                     )
from processing.audio_processing import AudioTools
from profile_manager import ensure_profile_exists
from db.db import DbManager
from processing.Processor import Processor
from utils.env_utils import using_modal
import asyncio

USING_MODAL = using_modal()

LOGGER = logging.getLogger(__name__)
audio_router = APIRouter(prefix="/audio")

BASE_MEDIA_DIR = Path("media_files")
PROFILES_DIR = BASE_MEDIA_DIR / "profiles"
TEMP_DIR = BASE_MEDIA_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
processor = Processor(save_path=TEMP_DIR)
db_manager = DbManager()


@audio_router.post("/transcribe_from_audio")
async def transcribe_from_audio(
    file: UploadFile,
    clean_audio_str: str = Form("false", alias="clean_audio"),
    gpt_explain_str: str = Form("false", alias="gpt_explain"),
    profile_id: str = Depends(ensure_profile_exists),
) -> dict:
    """
    POST endpoint for transcribing an audio file using faster whisper.

    Args:
      file (UploadFile): File uploaded passed through endpoint.
      clean_audio_str (str): Whether to filter the audio or not.
      gpt_explain_str (str): Whether to call OpenAI API for explanation.
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Response with keys `transcript` and `gpt_explanation`

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     transcribing audio.
    """
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required.",
        )

    # 1. Prepare Save Paths
    do_clean_audio = clean_audio_str.lower() == "true"
    do_gpt_explain = gpt_explain_str.lower() == "true"

    op_id = str(uuid.uuid4())
    op_tmp_dir = TEMP_DIR / f"transcribe_audio_{profile_id}_{op_id}"
    op_tmp_dir.mkdir(parents=True,
                     exist_ok=True)

    prof_audio_dir = PROFILES_DIR / profile_id / "audios"
    prof_audio_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename
    persistent_audio_fname = f"{op_id}_{original_filename}"
    final_audio_storage_loc = prof_audio_dir / persistent_audio_fname
    rel_audio_path_db = (
        Path("profiles") / profile_id / "audios" / persistent_audio_fname
    )

    tmp_uploaded_audio_loc = op_tmp_dir / original_filename
    audio_to_process_loc = tmp_uploaded_audio_loc

    try:
        async with aiofiles.open(tmp_uploaded_audio_loc, "wb+") as f_obj:
            content = await file.read()
            await f_obj.write(content)
        LOGGER.info(
            f"Temp audio for transcription: '{tmp_uploaded_audio_loc}'")

        # 2. Optional Pre-processing
        if do_clean_audio:
            # Filter with AudioTools.filter_audio
            audio_tools = AudioTools(working_dir=op_tmp_dir)
            cleaned_audio_name = f"cleaned_{op_id}_{original_filename}.wav"
            cleaned_audio_tmp_loc = op_tmp_dir / cleaned_audio_name

            cleaned_path_str = await asyncio.to_thread(
                audio_tools.filter_audio,
                input_path=str(tmp_uploaded_audio_loc),
                output_wav=str(cleaned_audio_tmp_loc),
            )
            if not cleaned_path_str or not Path(cleaned_path_str).exists():
                LOGGER.error((f"Audio cleaning failed for"
                              f"'{tmp_uploaded_audio_loc}'"))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Audio cleaning process failed.",
                )
            audio_to_process_loc = Path(cleaned_path_str)
            LOGGER.info(f"Audio cleaned: '{audio_to_process_loc}'")

        shutil.copyfile(audio_to_process_loc, final_audio_storage_loc)
        LOGGER.info(
            f"Audio ({'cleaned' if do_clean_audio else 'original'}) "
            f"copied to persistent: '{final_audio_storage_loc}'"
        )
        # 3. Transcribe audio
        # When MODAL env variables are available use MODAL
        if USING_MODAL:
            LOGGER.info("Conversion sent to Modal")
            LOGGER.info(f"Audio Filepath: '{final_audio_storage_loc}'")
            transcription_data = await processor.modal_transcribe_to_str(
                audio_fp=str(final_audio_storage_loc)
            )
        # Run locally
        # processor will have fwhisper attribute.
        else:
            LOGGER.info("Running Locally")
            LOGGER.info(f"Audio Filepath: '{final_audio_storage_loc}'")
            transcription_data = await asyncio.to_thread(
                processor.fwhisper.transcribe_to_str,
                audio_path=str(final_audio_storage_loc)
            )
        if not transcription_data or "text" not in transcription_data:
            LOGGER.error((
                f"Transcription (to_str) failed or gave invalid"
                f"result for '{final_audio_storage_loc}'"
            ))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio transcription failed to produce text.",
            )
        # 4. Optinal GPT Explanation
        # The plain_text_transcript is what will be returned in the API
        plain_text_transcript = transcription_data["text"]
        LOGGER.info(f"Transcripted generated for profile '{profile_id}'")
        gpt_explanation_text = None
        if do_gpt_explain:
            if not plain_text_transcript.strip():
                LOGGER.warning((f"Skipping GPT for empty transcript"
                               f"(Profile: '{profile_id}')"))
                gpt_explanation_text = (
                    "Transcript content empty, no explanation.")
            else:
                gpt_explainer = (
                    processor.sentence_breakdown_service.gpt_explainer
                    )
                try:
                    LOGGER.info((f"Generating GPT explanation"
                                 f"(Profile: '{profile_id}')"))
                    gpt_explanation_text = gpt_explainer.explain_sentence(
                        sentence=plain_text_transcript
                    )
                    LOGGER.info(f"GPT explanation\
                        generated (Profile: '{profile_id}')")
                except Exception as e_gpt:
                    LOGGER.error(f"GPT explanation failed: '{e_gpt}'")
                    gpt_explanation_text = (
                        "Failed to generate GPT explanation.")

        # 5. Save Data to Database
        transcript_id = str(uuid.uuid4())
        values = {
            "id": transcript_id,
            "profile_id": profile_id,
            "original_file_name": original_filename,
            "transcript": plain_text_transcript,
            "gpt_explanation": gpt_explanation_text,
            "audio_file_path": str(rel_audio_path_db)
        }
        await db_manager.create("profile_transcripts", values)
        LOGGER.info((f"Transcript '{transcript_id}' saved"
                     f"(Profile: '{profile_id}')"))
        # Also insert into Files table.
        audio_file_rec_id = str(uuid.uuid4())
        file_values = {
            "id": audio_file_rec_id,
            "profile_id": profile_id,
            "file_name": original_filename,
            "file_path": str(rel_audio_path_db),
            "file_type": "audio_source",
            "related_transcript_id": transcript_id
        }
        await db_manager.create("profile_files", file_values)
        LOGGER.info((f"Audio source record '{audio_file_rec_id}'"
                    f"saved (Profile: '{profile_id}')"))

        return {
            "transcript": plain_text_transcript,
            "gpt_explanation": gpt_explanation_text,
        }

    except HTTPException:
        # Propagate Exceptions
        raise
    except Exception as e:
        LOGGER.exception((
            f"Error in transcribe_from_audio"
            f"(Profile: '{profile_id}', File: '{original_filename}')"
        ))
        if final_audio_storage_loc.exists():
            try:
                final_audio_storage_loc.unlink()
            except OSError as ose:
                LOGGER.error((f"Could not remove"
                              f"'{final_audio_storage_loc}': '{ose}'"
                              ))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe audio: '{str(e)}'",
        )
    finally:
        # 6. Delete temp data
        if op_tmp_dir.exists():
            try:
                shutil.rmtree(op_tmp_dir)
            except OSError as e_os:
                LOGGER.error(
                    f"Error cleaning temp dir '{op_tmp_dir}': '{e_os}'")
