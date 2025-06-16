import logging
import shutil
import uuid
from pathlib import Path

# FastAPI and Pydantic
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
    status,
)

# Project-specific modules
from processing.audio_processing import AudioTools
from processing.text_processing import GptExplainService
from profile_manager import ensure_profile_exists
from db.db import get_db
from db.Tables import profile_transcripts, profile_files
from processing.Processor import Processor
from utils.env_utils import using_modal
import asyncio
USING_MODAL = using_modal()

if not USING_MODAL:
    from processing.whisper_wrapper import FWhisperWrapper
    fwhisper = FWhisperWrapper()

logger = logging.getLogger(__name__)
audio_router = APIRouter(prefix="/audio")

BASE_MEDIA_DIR = Path("media_files")
PROFILES_DIR = BASE_MEDIA_DIR / "profiles"
TEMP_DIR = BASE_MEDIA_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
if USING_MODAL:
    processor = Processor(save_path=TEMP_DIR, use_modal=True)


@audio_router.post("/transcribe_from_audio")
async def transcribe_from_audio(
    file: UploadFile = File(...),
    clean_audio_str: str = Form("false", alias="clean_audio"),
    gpt_explain_str: str = Form("false", alias="gpt_explain"),
    profile_id: str = Depends(ensure_profile_exists),
):
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required.",
        )

    do_clean_audio = clean_audio_str.lower() == "true"
    do_gpt_explain = gpt_explain_str.lower() == "true"

    op_id = str(uuid.uuid4())
    op_tmp_dir = TEMP_DIR / f"transcribe_audio_{profile_id}_{op_id}"
    op_tmp_dir.mkdir(parents=True, exist_ok=True)

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
        with open(tmp_uploaded_audio_loc, "wb+") as f_obj:
            shutil.copyfileobj(file.file, f_obj)
        logger.info(f"Temp audio for transcription: {tmp_uploaded_audio_loc}")

        if do_clean_audio:
            audio_tools = AudioTools(working_dir=op_tmp_dir)
            cleaned_audio_name = f"cleaned_{op_id}_{original_filename}.wav"
            cleaned_audio_tmp_loc = op_tmp_dir / cleaned_audio_name

            cleaned_path_str = audio_tools.filter_audio(
                input_path=str(tmp_uploaded_audio_loc),
                output_wav=str(cleaned_audio_tmp_loc),
            )
            if not cleaned_path_str or not Path(cleaned_path_str).exists():
                logger.error(f"Audio cleaning failed for \
                    {tmp_uploaded_audio_loc}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Audio cleaning process failed.",
                )
            audio_to_process_loc = Path(cleaned_path_str)
            logger.info(f"Audio cleaned: {audio_to_process_loc}")

        shutil.copyfile(audio_to_process_loc, final_audio_storage_loc)
        logger.info(
            f"Audio ({'cleaned' if do_clean_audio else 'original'}) "
            f"copied to persistent: {final_audio_storage_loc}"
        )
        # When MODAL env variables are available use MODAL
        if USING_MODAL:
            logger.info("Conversion sent to Modal")
            logger.info(f"Audio Filepath: {final_audio_storage_loc}")
            transcription_data = await processor.modal_transcribe_to_str(
                audio_fp=str(final_audio_storage_loc)
            )
        # Run locally
        else:
            logger.info("Running Locally")
            logger.info(f"Audio Filepath: {final_audio_storage_loc}")
            transcription_data = await asyncio.to_thread(
                fwhisper.transcribe_to_str,
                audio_path=str(final_audio_storage_loc)
            )
        if not transcription_data or "text" not in transcription_data:
            logger.error(
                f"Transcription (to_str) failed or gave invalid\
                    result for {final_audio_storage_loc}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio transcription failed to produce text.",
            )

        # The plain_text_transcript is what will be returned in the API
        plain_text_transcript = transcription_data["text"]
        logger.info(f"Plain text transcript \
            generated for profile {profile_id}")
        gpt_explanation_text = None
        if do_gpt_explain:
            if not plain_text_transcript.strip():
                logger.warning(f"Skipping GPT for\
                    empty transcript (Profile: {profile_id})")
                gpt_explanation_text = "Transcript content empty,\
                    no explanation."
            else:
                gpt_explainer = GptExplainService()
                try:
                    logger.info(f"Generating GPT \
                        explanation (Profile: {profile_id})")
                    gpt_explanation_text = gpt_explainer.explain_sentence(
                        sentence=plain_text_transcript
                    )
                    logger.info(f"GPT explanation\
                        generated (Profile: {profile_id})")
                except Exception as e_gpt:
                    logger.error(f"GPT explanation failed: {e_gpt}")
                    gpt_explanation_text = "Failed to generate GPT \
                        explanation."
        db = await get_db()
        transcript_id = str(uuid.uuid4())

        ins_transcript_q = profile_transcripts.insert().values(
            id=transcript_id,
            profile_id=profile_id,
            original_file_name=original_filename,
            transcript=plain_text_transcript,
            gpt_explanation=gpt_explanation_text,
            audio_file_path=str(rel_audio_path_db),
        )
        await db.execute(ins_transcript_q)
        logger.info(f"Transcript {transcript_id} (plain text) \
            saved (Profile: {profile_id})")

        audio_file_rec_id = str(uuid.uuid4())
        ins_audio_file_q = profile_files.insert().values(
            id=audio_file_rec_id,
            profile_id=profile_id,
            file_name=original_filename,
            file_path=str(rel_audio_path_db),
            file_type="audio_source",
            related_transcript_id=transcript_id,
        )
        await db.execute(ins_audio_file_q)
        logger.info(f"Audio source record {audio_file_rec_id}\
            saved (Profile: {profile_id})")

        return {
            "transcript": plain_text_transcript,
            "gpt_explanation": gpt_explanation_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Error in transcribe_from_audio (Profile: {profile_id}, \
                File: {original_filename})"
        )
        if final_audio_storage_loc.exists():
            try:
                final_audio_storage_loc.unlink()
            except OSError as ose:
                logger.error(f"Could not remove\
                {final_audio_storage_loc}: {ose}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe audio: {str(e)}",
        )
    finally:
        if op_tmp_dir.exists():
            try:
                shutil.rmtree(op_tmp_dir)
            except OSError as e_os:
                logger.error(f"Error cleaning temp dir {op_tmp_dir}: {e_os}")
