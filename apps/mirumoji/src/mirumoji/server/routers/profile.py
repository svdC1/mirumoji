"""
This module defines the `profile_router` of the Mirumoji API

Covers a profile's LLM template, saved clips, files, transcripts, and Anki
deck export, all scoped to the active profile via `X-Profile-ID`

Attributes:
    LOGGER (logging.Logger): Module's logging object
    profile_router (APIRouter): The FastAPI router object
"""

import asyncio
import json
import logging
import urllib.parse
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, status

from ...exceptions import RecordNotFoundError
from .. import media
from ..db import UnitOfWork
from ..dependencies import ensure_profile_exists, get_stream_file
from ..models.requests import LlmTemplateRequest
from ..models.responses import (
    AnkiExportResponse,
    ClipResponse,
    LlmTemplateResponse,
    ProfileFileResponse,
    ProfileTranscriptResponse,
    SaveClipResponse,
)
from ..processing import anki, audio

LOGGER = logging.getLogger(__name__)

profile_router = APIRouter(
    prefix="/profiles",
    dependencies=[Depends(ensure_profile_exists)],
)


# --- LLM Template ---


@profile_router.get("/template", response_model=LlmTemplateResponse)
async def get_template(
    profile_id: str = Depends(ensure_profile_exists),
) -> LlmTemplateResponse:
    """
    Retrieves the active profile's LLM template

    Args:
        profile_id (str): Validated profile id

    Returns:
        The profile's saved LLM template

    Raises:
        RecordNotFoundError: If the profile has no template
        DatabaseError: If the lookup fails
    """
    async with UnitOfWork() as uow:
        template = await uow.templates.get_for_profile(profile_id)
    if template is None:
        raise RecordNotFoundError(
            f"No LLM template for profile '{profile_id}'",
            details={"profile_id": profile_id},
        )
    return LlmTemplateResponse(
        id=str(template.id),
        sys_msg=template.sys_msg,
        prompt=template.prompt,
        model=template.model,
    )


@profile_router.post("/template", response_model=LlmTemplateResponse)
async def upsert_template(
    req: LlmTemplateRequest,
    profile_id: str = Depends(ensure_profile_exists),
) -> LlmTemplateResponse:
    """
    Creates or updates the active profile's LLM template

    Args:
        req (LlmTemplateRequest): The template data
        profile_id (str): Validated profile id

    Returns:
        The created or updated LLM template

    Raises:
        DatabaseError: If the upsert fails
    """
    async with UnitOfWork() as uow:
        template = await uow.templates.upsert(
            profile_id=profile_id,
            sys_msg=req.sys_msg,
            prompt=req.prompt,
            model=req.model,
        )
        await uow.commit()
    return LlmTemplateResponse(
        id=str(template.id),
        sys_msg=template.sys_msg,
        prompt=template.prompt,
        model=template.model,
    )


@profile_router.delete("/template", status_code=status.HTTP_200_OK)
async def delete_template(
    profile_id: str = Depends(ensure_profile_exists),
) -> dict:
    """
    Deletes the active profile's LLM template

    Args:
        profile_id (str): Validated profile id

    Returns:
        A confirmation payload

    Raises:
        RecordNotFoundError: If the profile has no template
        DatabaseError: If the deletion fails
    """
    async with UnitOfWork() as uow:
        await uow.templates.delete(profile_id)
        await uow.commit()
    return {"success": True, "message": "Template deleted successfully."}


# --- Clips ---


@profile_router.post(
    "/clips",
    response_model=SaveClipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_clip(
    clip_file: Path = Depends(get_stream_file),
    profile_id: str = Depends(ensure_profile_exists),
    start_time: str = Header(..., alias="X-Clip-Start-Time"),
    end_time: str = Header(..., alias="X-Clip-End-Time"),
    breakdown: str = Header(..., alias="X-Breakdown"),
) -> SaveClipResponse:
    """
    Saves a streamed video clip for the active profile

    Streams the upload, converts it to WebM for Anki compatibility, stores it
    under the profile, and persists a file + clip record. Clip metadata is
    carried via headers, since the request body is the streamed file

    Args:
        clip_file (Path): Path to the streamed upload
        profile_id (str): Validated profile id
        start_time (str): Clip start time in seconds (`X-Clip-Start-Time`)
        end_time (str): Clip end time in seconds (`X-Clip-End-Time`)
        breakdown (str): URL-encoded JSON breakdown payload (`X-Breakdown`)

    Returns:
        The saved clip's id, its file id, and its media URL

    Raises:
        HTTPException: If the clip metadata headers are malformed
        FFmpegError: If the WebM conversion fails
        StorageError: If storing the clip fails
        DatabaseError: If persistence fails
    """
    try:
        s_time = float(start_time)
        e_time = float(end_time)
        breakdown_data = json.loads(urllib.parse.unquote(breakdown))
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid clip metadata headers: {e}",
        ) from e

    op_id = uuid.uuid4().hex
    clips_dir = media.get_profile_dir(profile_id, "clips")
    webm_loc = clips_dir / f"{op_id}_{Path(clip_file.name).stem}.webm"
    rel_path = media.get_relative_path(webm_loc)

    try:
        # Convert to WebM for Anki Compatibility (NVENC w/ CPU fallback)
        ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
        await asyncio.to_thread(
            audio.to_webm,
            ffmpeg_path=ffmpeg,
            input_path=str(clip_file),
            output_path=str(webm_loc),
            use_nvenc=True,
        )

        async with UnitOfWork() as uow:
            file_rec = await uow.files.add(
                profile_id=profile_id,
                name=webm_loc.name,
                path=str(rel_path),
                type="clip",
            )
            clip_rec = await uow.clips.add(
                profile_id=profile_id,
                file_id=file_rec.id,
                start_time=s_time,
                end_time=e_time,
                llm_breakdown_response=breakdown_data,
            )
            await uow.commit()

        return SaveClipResponse(
            clip_id=str(clip_rec.id),
            file_id=str(file_rec.id),
            clip_url=f"/media/{rel_path.as_posix()}",
        )
    finally:
        try:
            await media.delete_dir(media.get_relative_path(clip_file.parent))
        except Exception:
            LOGGER.warning(
                f"Failed to clean temp dir '{clip_file.parent}'",
                exc_info=True,
            )


@profile_router.get("/clips", response_model=list[ClipResponse])
async def list_clips(
    profile_id: str = Depends(ensure_profile_exists),
) -> list[ClipResponse]:
    """
    Lists the active profile's saved clips

    Args:
        profile_id (str): Validated profile id

    Returns:
        The profile's saved clips, newest first

    Raises:
        DatabaseError: If the query fails
    """
    async with UnitOfWork() as uow:
        clips = await uow.clips.list_for_profile(profile_id, load_file=True)
    return [
        ClipResponse(
            id=str(c.id),
            file_id=str(c.file_id),
            clip_url=(
                f"/media/{Path(c.file.path).as_posix()}" if c.file else ""
            ),
            start_time=c.start_time,
            end_time=c.end_time,
            breakdown=c.llm_breakdown_response,
        )
        for c in clips
    ]


@profile_router.delete("/clips/{clip_id}", status_code=status.HTTP_200_OK)
async def delete_clip(
    clip_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> dict:
    """
    Deletes one of the active profile's saved clips and its file

    Args:
        clip_id (uuid.UUID): Id of the clip to delete
        profile_id (str): Validated profile id

    Returns:
        A confirmation payload

    Raises:
        RecordNotFoundError: If the clip doesn't exist or isn't owned by the
            profile
        StorageError: If deleting the clip file fails
        DatabaseError: If the deletion fails
    """
    async with UnitOfWork() as uow:
        clip = await uow.clips.get(clip_id)
        if clip.profile_id != profile_id:
            raise RecordNotFoundError(
                f"Clip '{clip_id}' Not Found",
                details={"clip_id": str(clip_id)},
            )
        file = await uow.files.get(clip.file_id)
        await uow.clips.delete(clip_id)
        await uow.files.delete(clip.file_id)
        await uow.commit()
    await media.delete_file(file.path)
    return {"success": True, "message": "Clip Deleted Successfully"}


# --- Files ---


@profile_router.get("/files", response_model=list[ProfileFileResponse])
async def list_files(
    profile_id: str = Depends(ensure_profile_exists),
) -> list[ProfileFileResponse]:
    """
    Lists the active profile's saved files

    Args:
        profile_id (str): Validated profile id

    Returns:
        The profile's saved files, newest first

    Raises:
        DatabaseError: If the query fails
    """
    async with UnitOfWork() as uow:
        files = await uow.files.list_for_profile(profile_id)
    return [
        ProfileFileResponse(
            id=str(f.id),
            name=f.name,
            url=f"/media/{Path(f.path).as_posix()}",
            type=f.type,
            created_at=f.created_at.isoformat() if f.created_at else None,
        )
        for f in files
    ]


@profile_router.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(
    file_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> dict:
    """
    Deletes one of the active profile's files

    Deleting a file cascades (via foreign keys) to any transcripts or clips
    that reference it

    Args:
        file_id (uuid.UUID): Id of the file to delete
        profile_id (str): Validated profile id

    Returns:
        A confirmation payload

    Raises:
        RecordNotFoundError: If the file doesn't exist or isn't owned by the
            profile
        StorageError: If deleting the file fails
        DatabaseError: If the deletion fails
    """
    async with UnitOfWork() as uow:
        file = await uow.files.get(file_id)
        if file.profile_id != profile_id:
            raise RecordNotFoundError(
                f"File '{file_id}' Not Found",
                details={"file_id": str(file_id)},
            )
        await uow.files.delete(file_id)
        await uow.commit()
    await media.delete_file(file.path)
    return {"success": True, "message": "File deleted successfully."}


# --- Transcripts ---


@profile_router.get(
    "/transcripts",
    response_model=list[ProfileTranscriptResponse],
)
async def list_transcripts(
    profile_id: str = Depends(ensure_profile_exists),
) -> list[ProfileTranscriptResponse]:
    """
    Lists the active profile's transcripts

    Args:
        profile_id (str): Validated profile id

    Returns:
        The profile's transcripts, newest first

    Raises:
        DatabaseError: If the query fails
    """
    async with UnitOfWork() as uow:
        transcripts = await uow.transcripts.list_for_profile(
            profile_id,
            load_file=True,
        )
    return [
        ProfileTranscriptResponse(
            id=str(t.id),
            file_id=str(t.file_id),
            text=t.text,
            llm_explanation=t.llm_explanation,
            url=(f"/media/{Path(t.file.path).as_posix()}" if t.file else None),
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in transcripts
    ]


@profile_router.delete(
    "/transcripts/{transcript_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_transcript(
    transcript_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> dict:
    """
    Deletes one of the active profile's transcripts

    Args:
        transcript_id (uuid.UUID): Id of the transcript to delete
        profile_id (str): Validated profile id

    Returns:
        A confirmation payload

    Raises:
        RecordNotFoundError: If the transcript doesn't exist or isn't owned by
            the profile
        DatabaseError: If the deletion fails
    """
    async with UnitOfWork() as uow:
        transcript = await uow.transcripts.get(transcript_id)
        if transcript.profile_id != profile_id:
            raise RecordNotFoundError(
                f"Transcript '{transcript_id}' Not Found",
                details={"transcript_id": str(transcript_id)},
            )
        await uow.transcripts.delete(transcript_id)
        await uow.commit()
    return {"success": True, "message": "Transcript deleted successfully."}


# --- Anki Export ---


@profile_router.get("/anki_export", response_model=AnkiExportResponse)
async def export_anki_deck(
    profile_id: str = Depends(ensure_profile_exists),
) -> AnkiExportResponse:
    """
    Exports the active profile's saved clips as an Anki deck

    Builds one card per saved clip from its stored breakdown payload (focus
    word, meanings, sentence, and explanation), bundles the clip media, and
    writes the `.apkg` under the profile

    Args:
        profile_id (str): Validated profile id

    Returns:
        The media URL serving the exported Anki deck

    Raises:
        DatabaseError: If reading the clips fails
        StorageError: If writing the deck fails
    """
    async with UnitOfWork() as uow:
        clips = await uow.clips.list_for_profile(profile_id, load_file=True)

    cards: list[anki.AnkiCard] = []
    for clip in clips:
        if clip.file is None:
            continue
        breakdown = clip.llm_breakdown_response or {}
        focus = breakdown.get("focus") or {}
        word = focus.get("word") or {}
        kotobase = focus.get("kotobase_data") or {}
        cards.append(
            anki.AnkiCard(
                clip_path=str(media.BASE_PATH / clip.file.path),
                word=word.get("surface", ""),
                meanings=", ".join(kotobase.get("meanings") or []),
                sentence=breakdown.get("sentence", ""),
                explanation=breakdown.get("explanation", ""),
            ),
        )

    anki_dir = media.get_profile_dir(profile_id, "anki")
    out_loc = anki_dir / f"{uuid.uuid4().hex}_saved_deck.apkg"
    await asyncio.to_thread(anki.export_deck, cards, str(out_loc))

    rel_out = media.get_relative_path(out_loc)
    return AnkiExportResponse(anki_deck_url=f"/media/{rel_out.as_posix()}")
