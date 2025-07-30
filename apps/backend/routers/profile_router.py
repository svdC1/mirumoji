"""
This module defines the `profile_router` of the Mirumoji API.

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
  profile_router (APIRouter): The FastAPI Router Object.
"""

import logging
import uuid
import asyncio
import json
from fastapi import (APIRouter,
                     Depends,
                     HTTPException,
                     status,
                     UploadFile,
                     Form,
                     Path
                     )
from models.GptTemplateResponse import GptTemplateResponse
from models.GptTemplateBase import GptTemplateBase
from models.ClipResponse import ClipResponse
from models.ProfileFileResponse import ProfileFileResponse
from models.ProfileTranscriptResponse import ProfileTranscriptResponse
from models.AnkiExportResponse import AnkiExportResponse
from processing.audio_processing import AudioTools
from typing import Optional, List
import pathlib
from db.db import DbManager
from profile_manager import ensure_profile_exists
from utils.anki_utils import AnkiExporter
from utils.file_utils import save_upload_file

LOGGER = logging.getLogger(__name__)

profile_router = APIRouter(prefix='/profiles',
                           dependencies=[Depends(ensure_profile_exists)]
                           )

BASE_MEDIA_PATH = pathlib.Path("media_files")
TEMP_MEDIA_PATH = BASE_MEDIA_PATH / "temp"
TEMP_MEDIA_PATH.mkdir(parents=True, exist_ok=True)

db_manager = DbManager()


# --- GPT Template Management ---
@profile_router.get("/gpt_template",
                    response_model=GptTemplateResponse
                    )
async def get_gpt_template(
    profile_id: str = Depends(ensure_profile_exists)
) -> GptTemplateResponse:
    """
    GET endpoint for retrieving the active profile's GPT Template.

    Args:
      profile_id (str): Profile ID from Header.

    Returns:
      GptTemplateResponse: `GptTemplateResponse` model with fetched info.

    Raises:
      HTTPException: If no profile ID was provided or no record was found.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    rec = await db_manager.read("gpt_templates",
                                {"profile_id": profile_id},
                                fetch_one=True
                                )
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="GPT template not found.")
    return GptTemplateResponse(id=rec.id,
                               sysMsg=rec.sys_msg,
                               prompt=rec.prompt,
                               version=rec.version
                               )


@profile_router.post("/gpt_template",
                     response_model=GptTemplateResponse
                     )
async def upsert_gpt_template(
    template_data: GptTemplateBase,
    profile_id: str = Depends(ensure_profile_exists)
) -> GptTemplateResponse:
    """
    POST endpoint for creating or updating the active profile's GPT Template.

    Args:
      profile_id (str): Profile ID from Header.
      template_data (GptTemplateBase): Data to insert into template.

    Returns:
      GptTemplateResponse: `GptTemplateResponse` model with fetched info.

    Raises:
      HTTPException: If no profile ID was provided.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required.")
    values = {
        "profile_id": profile_id,
        "sys_msg": template_data.sys_msg,
        "prompt": template_data.prompt,
        "version": template_data.version
        }
    ex = await db_manager.read("gpt_templates",
                               {"profile_id": profile_id},
                               fetch_one=True
                               )
    if ex:
        # Update current template
        await db_manager.update("gpt_templates", {"id": ex.id}, values)
        tid = ex.id
    else:
        # Create new template
        tid = str(uuid.uuid4())
        values["id"] = tid
        await db_manager.create("gpt_templates", values)
    return GptTemplateResponse(id=tid,
                               sysMsg=values["sys_msg"],
                               prompt=values["prompt"],
                               version=values["version"]
                               )


@profile_router.delete("/gpt_template",
                       status_code=status.HTTP_200_OK
                       )
async def delete_gpt_template(
    profile_id: str = Depends(ensure_profile_exists)
) -> dict:
    """
    DELETE endpoint for deleting the active profile's GPT Template.

    Args:
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Conirmation response with keys `success` and `message`.

    Raises:
      HTTPException: If no profile ID was provided or no template was found.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required.")
    res = await db_manager.delete("gpt_templates", {"profile_id": profile_id})
    if res == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="GPT template not found.")
    return {"success": True,
            "message": "Template deleted successfully."
            }


# --- Clip Management ---
@profile_router.post("/clips/save",
                     status_code=status.HTTP_201_CREATED
                     )
async def save_video_clip(
    video_clip: UploadFile,
    profile_id: str = Depends(ensure_profile_exists),
    clip_start_time: str = Form(...),
    clip_end_time: str = Form(...),
    gpt_breakdown_response: str = Form(...),
    original_video_file_name: Optional[str] = Form(None),
    original_video_url: Optional[str] = Form(None)
) -> dict:
    """
    POST endpoint for saving a new clip for the active profile

    Args:
      profile_id (str): Profile ID from Header.
      clip_start_time (str): Original video clip start time.
      clip_end_time (str): Original video clip end time.
      gpt_breakdown_response (str): JSON string of `BreakdownResponse` model.
      video_clip (UploadFile): Clip file sent through endpoint.
      original_video_file_name (str, optional): Original video's name
      original_video_url (str, optional): URL where FastAPI is serving the
                                          original video's static file.

    Returns:
      dict: Conirmation response with keys `success` and `message` and `c_id`

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     saving the clip.
    """

    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    # Create directory in media_files
    p_path = BASE_MEDIA_PATH / "profiles" / profile_id / "clips"
    p_path.mkdir(parents=True, exist_ok=True)

    # Copy file to directory
    fname = f"{uuid.uuid4()}_{video_clip.filename}"
    webm_fname = pathlib.Path(fname).with_suffix(".webm")
    loc = p_path / fname
    webm_loc = loc.with_suffix(".webm")
    rel_path = pathlib.Path("profiles") / profile_id / "clips" / fname
    try:
        await save_upload_file(video_clip, loc)

        # Convert to WebM for Anki Compatibility
        try:
            LOGGER.info(f"Converting Clip to WEBM '{loc}' -> '{webm_loc}'")
            audio_tools = AudioTools(working_dir=p_path)
            await asyncio.to_thread(
                audio_tools.to_webm,
                input_path=str(loc),
                output_path=str(webm_loc),
                use_nvenc=True
                )
        except Exception as e:
            LOGGER.exception((
                f"Failed to convert '{loc}' to WEBM : '{e}';"
                f"Falling back to original format"))
        if webm_loc.exists():
            rel_path = (
                pathlib.Path("profiles") / profile_id / "clips" / webm_fname
                    )
            fname = webm_fname

        # Save info in Database
        gpt_j = json.loads(gpt_breakdown_response)
        s_time = float(clip_start_time)
        e_time = float(clip_end_time)
        c_id = str(uuid.uuid4())
        values = {
            "id": c_id,
            "profile_id": profile_id,
            "clip_start_time": s_time,
            "clip_end_time": e_time,
            "gpt_breakdown_response": gpt_j,
            "video_clip_path": str(rel_path),
            "original_video_file_name": original_video_file_name,
            "original_video_url": original_video_url
        }
        await db_manager.create("clips", values)

        # Also save to files
        files_values = {
            "id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "file_name": video_clip.filename,
            "file_path": str(rel_path),
            "file_type": "video_clip"
        }
        await db_manager.create("profile_files", files_values)

        return {"success": True,
                "message": "Clip saved successfully.",
                "clip_id": c_id
                }

    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid JSON.")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid time format.")
    except HTTPException:
        # Propagate Exceptions
        raise
    except Exception as e:
        LOGGER.exception("Error saving clip")
        loc.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to save clip: '{e}'"
                            )


@profile_router.get("/clips",
                    response_model=List[ClipResponse]
                    )
async def get_saved_clips(
    profile_id: str = Depends(ensure_profile_exists)
) -> List[ClipResponse]:
    """
    GET endpoint for getting a profile's saved clips.

    Args:
      profile_id (str): Profile ID from Header.

    Returns:
      List[ClipResponse]: List of `ClipResponse` models

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     getting saved clips.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    c_lst = await db_manager.read("clips", {"profile_id": profile_id})
    return [
        ClipResponse(id=c.id,
                     get_url=f"/media/{c.video_clip_path}",
                     breakdown_response=json.dumps(c.gpt_breakdown_response)
                     ) for c in c_lst
        ]


@profile_router.delete("/clips/{clipId}",
                       status_code=status.HTTP_200_OK
                       )
async def delete_saved_clip(
    clipId: str = Path(...),
    profile_id: str = Depends(ensure_profile_exists)
) -> dict:
    """
    DELETE endpoint for deleting a profile's specific saved clip.

    Args:
      clipId (str): The ID of the clip to delete.
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Confirmation response with keys `success` and `message`

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     deleting the clip.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    filter = {"id": clipId, "profile_id": profile_id}
    clip_r = await db_manager.read("clips",
                                   filter,
                                   fetch_one=True
                                   )

    if not clip_r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clip not found."
                            )
    await db_manager.delete("clips", filter)

    files_filter = {"file_path": clip_r.video_clip_path,
                    "profile_id": profile_id}

    await db_manager.delete("profile_files", files_filter)
    fp = BASE_MEDIA_PATH / clip_r.video_clip_path

    if isinstance(fp, pathlib.Path) and fp.exists():
        try:
            fp.unlink()
            LOGGER.info(f"Deleted: '{fp}'")
        except OSError as e:
            LOGGER.error(f"Error deleting '{fp}': '{e}'")
    else:
        LOGGER.warning(f"Not found for del: '{fp}'")
    return {"success": True,
            "message": "Clip deleted successfully."
            }


# --- Profile File Management ---
@profile_router.get("/files",
                    response_model=List[ProfileFileResponse]
                    )
async def get_profile_files(
    profile_id: str = Depends(ensure_profile_exists)
) -> List[ProfileFileResponse]:
    """
    GET endpoint for getting a profile's saved files.

    Args:
      profile_id (str): Profile ID from Header.

    Returns:
      List[ProfileFileResponse]: List of `ProfileFileResponse` models

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     getting files.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    f_lst = await db_manager.read("profile_files", {"profile_id": profile_id})
    return [
        ProfileFileResponse(id=f.id,
                            file_name=f.file_name,
                            get_url=f"/media/{f.file_path}",
                            file_type=f.file_type,
                            created_at=f.created_at.isoformat() if
                            f.created_at else None
                            ) for f in f_lst
            ]


@profile_router.delete("/files/{fileId}",
                       status_code=status.HTTP_200_OK
                       )
async def delete_profile_file(
    fileId: str = Path(...),
    profile_id: str = Depends(ensure_profile_exists)
) -> dict:
    """
    DELETE endpoint for deleting a specific saved file for a profile.

    Args:
      fileId (str): ID of the file to be deleted.
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Confirmation response with keys `success` and `message`.

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     deleting the file
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    filter = {"id": fileId, "profile_id": profile_id}
    file_r = await db_manager.read("profile_files", filter, fetch_one=True)
    if not file_r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="File record not found."
                            )
    await db_manager.delete("profile_files", filter)
    fp = BASE_MEDIA_PATH / file_r.file_path
    if isinstance(fp, pathlib.Path) and fp.exists():
        try:
            fp.unlink()
            LOGGER.info(f"Deleted file: '{fp}'")
        except OSError as e:
            LOGGER.error(f"Error deleting '{fp}': '{e}'")
    else:
        LOGGER.warning(f"File not found for del: '{fp}'")

    if file_r.file_type == "video_clip":
        # Delete related saved clip
        filter_clip = {"video_clip_path": file_r.file_path}

        res = await db_manager.delete("clips", filter_clip)
        if res > 0:
            LOGGER.info(f"Del assoc. clip for '{file_r.file_path}'")
    elif file_r.file_type == "audio_source":
        # Delete related transcript
        transcript_filter = {"audio_file_path": file_r.file_path}
        res = await db_manager.update("profile_transcripts",
                                      transcript_filter,
                                      values={"audio_file_path": None}
                                      )
        if res > 0:
            LOGGER.info(
                f"Cleared path in transcripts for '{file_r.file_path}'")
    return {"success": True,
            "message": "File deleted successfully."
            }


# --- Profile Transcript Management ---
@profile_router.get("/transcripts",
                    response_model=List[ProfileTranscriptResponse]
                    )
async def get_profile_transcripts(
    profile_id: str = Depends(ensure_profile_exists)
) -> List[ProfileTranscriptResponse]:
    """
    GET endpoint for retrieving profile transcripts.

    Args:
      profile_id (str): Profile ID from Header.

    Returns:
      List[ProfileTranscriptResponse]: List of `ProfileTranscriptResponse`
                                       models.

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     retrieving transcripts
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    res_trans = []
    for t in await db_manager.read("profile_transcripts",
                                   {"profile_id": profile_id}
                                   ):
        url = f"/media/{t.audio_file_path}" if t.audio_file_path else None
        res_trans.append(
            ProfileTranscriptResponse(
                id=t.id,
                original_file_name=t.original_file_name,
                transcript=t.transcript,
                gpt_explanation=t.gpt_explanation,
                get_url=url,
                created_at=t.created_at.isoformat() if t.created_at else None
                )
            )
    return res_trans


@profile_router.delete("/transcripts/{transcriptId}",
                       status_code=status.HTTP_200_OK
                       )
async def delete_profile_transcript(
    transcriptId: str = Path(...),
    profile_id: str = Depends(ensure_profile_exists)
) -> dict:
    """
    DELETE endpoint for deleting a specific transcript for a profile.

    Args:
      transcriptId (str): ID of the transcript to delete.
      profile_id (str): Profile ID from Header.

    Returns:
      dict: Confirmation response with keys `success` and `message`.

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     deleting the transcript.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    filter = {"id": transcriptId, "profile_id": profile_id}
    trans_r = await db_manager.read("profile_transcripts",
                                    filter,
                                    fetch_one=True
                                    )
    if not trans_r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Transcript not found."
                            )

    await db_manager.delete("profile_transcripts", filter)

    LOGGER.info(f"Deleted transcript '{transcriptId}'")
    if trans_r.audio_file_path:
        # Delete file if it exists
        aud_path = trans_r.audio_file_path
        file_filter = {"file_path": aud_path, "profile_id": profile_id}
        res = await db_manager.delete("profile_files", file_filter)
        if res > 0:
            LOGGER.info(f"Del assoc. profile_files for: '{aud_path}'")
            fp_aud = BASE_MEDIA_PATH / aud_path
            if isinstance(fp_aud, pathlib.Path) and fp_aud.exists():
                try:
                    fp_aud.unlink()
                    LOGGER.info(f"Del audio file: '{fp_aud}'")
                except OSError as e:
                    LOGGER.error(f"Err del audio '{fp_aud}': '{e}'")
            else:
                LOGGER.warning(f"Audio file not found for del: '{fp_aud}'")
        else:
            LOGGER.warning(f"No profile_files entry for '{aud_path}' with \
                transcript '{transcriptId}'")
    return {"success": True,
            "message": "Transcript deleted successfully."
            }


# --- Anki Export ---
@profile_router.get("/anki_export",
                    response_model=AnkiExportResponse
                    )
async def export_anki_deck(
    profile_id: str = Depends(ensure_profile_exists)
) -> AnkiExportResponse:
    """
    GET endpoint for exporting profile's saved clips as an Anki Deck.

    Args:
      profile_id (str): Profile ID from Header.

    Returns:
      AnkiExportResponse: `AnkiExportResponse` model.

    Raises:
      HTTPException: If no profile ID was provided or there was an error
                     generating the Anki deck.
    """
    if not profile_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="X-Profile-ID header is required."
                            )
    # Get Clips
    clip_lst = [
        c for c in await db_manager.read("clips", {"profile_id": profile_id})
        ]
    anki = AnkiExporter()
    for c in clip_lst:
        breakdown = c.gpt_breakdown_response
        explanation = breakdown["gpt_explanation"]
        sentence = breakdown['sentence']
        path = str(BASE_MEDIA_PATH / c.video_clip_path)
        LOGGER.info(f"Clip Path: {path}")
        focus = breakdown["focus"]['word']
        meanings = ','.join(breakdown['focus']['meanings'])
        anki.add_card(clip_path=path,
                      word=focus,
                      meanings=meanings,
                      sentence=sentence,
                      explanation=explanation
                      )
    anki_dir = TEMP_MEDIA_PATH / 'profiles' / profile_id / 'anki'
    anki_dir.mkdir(parents=True, exist_ok=True)
    pkg_fn = f"{uuid.uuid4()}_saved_deck.apkg"
    outpath = anki_dir / pkg_fn
    anki.export(str(outpath))
    media_path = f"/media/temp/profiles/{profile_id}/anki/{pkg_fn}"
    return AnkiExportResponse(anki_deck_url=media_path)
