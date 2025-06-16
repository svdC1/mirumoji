import logging
from pathlib import Path
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    Depends,
    HTTPException,
    status,
)
import asyncio
from profile_manager import ensure_profile_exists
import shutil
from db.db import get_db
from db.Tables import profile_files
import uuid
from utils.env_utils import using_modal
from processing.audio_processing import AudioTools
from processing.Processor import Processor
USING_MODAL = using_modal()
if not USING_MODAL:
    from processing.whisper_wrapper import FWhisperWrapper
    fwhisper = FWhisperWrapper()


logger = logging.getLogger(__name__)
video_router = APIRouter(prefix="/video")
BASE_MEDIA_DIR = Path("media_files")
PROFILES_DIR = BASE_MEDIA_DIR / "profiles"
TEMP_DIR = BASE_MEDIA_DIR / "temp"
if USING_MODAL:
    processor = Processor(save_path=BASE_MEDIA_DIR,
                          use_modal=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@video_router.post("/generate_srt")
async def generate_srt(
    video_file: UploadFile = File(...),
    profile_id: str = Depends(ensure_profile_exists),
):
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required.",
        )

    op_id = str(uuid.uuid4())
    op_tmp_dir = Path(TEMP_DIR / f"gen_srt_{profile_id}_{op_id}")
    srt_dir = PROFILES_DIR / profile_id / "subtitles"
    srt_dir.mkdir(parents=True, exist_ok=True)
    srt_fp = (srt_dir / f"{op_id}.srt")
    relative_srt_fp = (
        Path("profiles") / profile_id / "subtitles" / f"{op_id}.srt"
        )
    op_tmp_dir.mkdir(parents=True, exist_ok=True)

    # Temporary location for the uploaded video within the operation's temp dir
    tmp_vid_upload_loc = op_tmp_dir / video_file.filename

    try:
        # 1. Save uploaded video to operation's temp dir
        with open(tmp_vid_upload_loc, "wb+") as f_obj:
            shutil.copyfileobj(video_file.file, f_obj)
        logger.info(f"Temp video for SRT: {tmp_vid_upload_loc}")

        # 2. Init AudioTools with operation's temp dir
        audio_tools = AudioTools(working_dir=op_tmp_dir)

        # 3. Extract audio
        extracted_audio_fpath = audio_tools.extract_audio(
            input_path=str(tmp_vid_upload_loc)
        )
        if not extracted_audio_fpath or not Path(extracted_audio_fpath
                                                 ).exists():
            logger.error(f"Audio extraction failed for {tmp_vid_upload_loc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract audio from video.",
            )
        logger.info(f"Audio extracted to {extracted_audio_fpath}")

        # 4. Transcribe extracted audio to SRT string
        # If Modal env variables are available use MODAL
        if USING_MODAL:
            logger.info("Conversion sent to Modal")
            logger.info(f"Local Filepath: {extracted_audio_fpath}")
            # Fix path for Internal Mounted Modal Container
            parts = Path(extracted_audio_fpath).parts
            extracted_audio_fpath = Path(*parts[-4:])
            logger.info(
                f"Media Filepath Adapted for Modal: {extracted_audio_fpath}")
            srt_result = await processor.modal_transcribe_to_srt(
                    media_fp=str(extracted_audio_fpath),
                    )
        # Run locally
        else:
            logger.info("Running Locally")
            logger.info(f"Local Filepath: {extracted_audio_fpath}")
            srt_result = await asyncio.to_thread(
                fwhisper.transcribe_to_srt,
                audio_path=str(extracted_audio_fpath),
                output_path=" ",
                string_result=True,
                fix_with_chat_gpt=True
            )

        if not srt_result:
            logger.error(
                f"SRT transcription failed for {extracted_audio_fpath}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate SRT from audio.",
            )
        with open(srt_fp, "w", encoding="utf-8") as f:
            f.write(srt_result)
        logger.info(f"SRT content generated for profile {profile_id}")

        # 5. Save metadata
        db = await get_db()
        vid_rec_id = str(uuid.uuid4())
        ins_vid_query = profile_files.insert().values(
            id=vid_rec_id,
            profile_id=profile_id,
            file_name=srt_fp.name,
            file_path=str(relative_srt_fp),
            file_type="srt",
        )
        await db.execute(ins_vid_query)
        logger.info(
            f"SRT record saved for profile {profile_id}"
        )

        return {"srt_content": srt_result}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Error generating SRT for {video_file.filename},prof {profile_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during SRT generation: {str(e)}",
        )
    finally:
        # 6. Clean up temp operation directory
        if op_tmp_dir.exists():
            try:
                shutil.rmtree(op_tmp_dir)
                logger.info(f"Cleaned temp dir: {op_tmp_dir}")
            except OSError as e_os:
                logger.error(f"Error cleaning temp dir {op_tmp_dir}: {e_os}")


@video_router.post("/convert_to_mp4")
async def convert_to_mp4(
    video_file: UploadFile = File(...),
    profile_id: str = Depends(ensure_profile_exists),
):
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required.",
        )

    op_id = str(uuid.uuid4())
    op_tmp_dir = TEMP_DIR / f"convert_mp4_{profile_id}_{op_id}"
    op_tmp_dir.mkdir(parents=True, exist_ok=True)

    # Temp location for the initially uploaded file
    tmp_uploaded_vid_loc = op_tmp_dir / video_file.filename

    # Final storage paths
    prof_conv_dir = PROFILES_DIR / profile_id / "converted"
    prof_conv_dir.mkdir(parents=True, exist_ok=True)

    # Using unique names for stored files
    conv_fname_stem = Path(video_file.filename).stem
    conv_stored_fname = f"{conv_fname_stem}_{op_id[:8]}_converted.mp4"

    final_conv_stored_loc = prof_conv_dir / conv_stored_fname

    rel_conv_db_path = (
       Path("profiles") / profile_id / "converted" / conv_stored_fname
    )

    try:
        # 1. Save uploaded video to temp location
        with open(tmp_uploaded_vid_loc, "wb+") as f_obj:
            shutil.copyfileobj(video_file.file, f_obj)
        logger.info(f"Temp video for conversion: {tmp_uploaded_vid_loc}")

        # 3. Convert video, saving to final converted location
        # If MODAL env variables are available use MODAL
        if USING_MODAL:
            logger.info("Conversion sent to Modal")
            logger.info(f"Video Filepath:{tmp_uploaded_vid_loc}")
            logger.info(f"Output Path: {final_conv_stored_loc}")
            conv_path_obj = await processor.modal_convert_to_mp4(
                video_fp=str(tmp_uploaded_vid_loc),
                outpath=str(final_conv_stored_loc)
            )
        # Run Locally
        else:
            logger.info("Running Locally")
            logger.info(f"Video Filepath:{tmp_uploaded_vid_loc}")
            logger.info(f"Output Path: {final_conv_stored_loc}")
            audio_tools = AudioTools(working_dir=op_tmp_dir)
            conv_path_obj = await asyncio.to_thread(
                audio_tools.to_mp4,
                input_path=str(tmp_uploaded_vid_loc),
                output_path=str(final_conv_stored_loc),
                use_nvenc=True
            )

        if not conv_path_obj or not final_conv_stored_loc.exists():
            logger.error(f"MP4 conversion failed for {tmp_uploaded_vid_loc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Video conversion to MP4 failed.",
            )
        logger.info(f"Video converted to {final_conv_stored_loc}")

        # 5. Save metadata for converted files to DB
        db = await get_db()
        conv_rec_id = str(uuid.uuid4())

        ins_conv_q = profile_files.insert().values(
            id=conv_rec_id,
            profile_id=profile_id,
            file_name=conv_stored_fname,
            file_path=str(rel_conv_db_path),
            file_type="mp4",
        )
        await db.execute(ins_conv_q)
        logger.info(
            f"Converted video records saved for profile:{profile_id}"
        )

        # 6. Construct URL for frontend
        converted_video_url = f"/media/{str(rel_conv_db_path)}"

        return {"converted_video_url": converted_video_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Error converting {video_file.filename} for profile {profile_id}"
        )
        # Attempt to clean up partially created files
        for loc in [final_conv_stored_loc]:
            if loc.exists():
                try:
                    loc.unlink()
                except OSError:
                    logger.error(f"Could not remove {loc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during video conversion: {str(e)}",
        )
    finally:
        # 7. Clean up temp operation directory
        if op_tmp_dir.exists():
            try:
                shutil.rmtree(op_tmp_dir)
                logger.info(f"Cleaned temp dir: {op_tmp_dir}")
            except OSError as e_os:
                logger.error(f"Error cleaning temp dir {op_tmp_dir}: {e_os}")
