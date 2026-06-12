"""
Repository pattern for mirumoji's database entities

info: Additional Information
    - Each repository wraps an `AsyncSession` and exposes typed async
      operations that return Pydantic DTOs

    - Mutating operations stage changes on the session and flush to populate
      server-side defaults (ids, timestamps)

    - The surrounding `UnitOfWork` owns the commit/rollback boundary

    - Failures raise domain exceptions (`RecordNotFoundError`, `DatabaseError`)
      that the server maps to HTTP responses
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...exceptions import DatabaseError, RecordNotFoundError
from .models import (
    Clip,
    ClipDTO,
    File,
    FileDTO,
    LlmTemplate,
    LlmTemplateDTO,
    Profile,
    ProfileDTO,
    Transcript,
    TranscriptDTO,
)

LOGGER = logging.getLogger("mirumoji")

_Uuid = uuid.UUID | str


class ProfileRepository:
    """
    Data access for `Profile` records

    Attributes:
        session (AsyncSession): The active asynchronous database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, profile_id: str) -> ProfileDTO:
        """
        Fetches a profile by id

        Args:
            profile_id (str): The profile id

        Returns:
            The matching `ProfileDTO`

        Raises:
            RecordNotFoundError: If the profile does not exist
            DatabaseError: If the lookup fails
        """
        try:
            profile = await self.session.get(Profile, profile_id)
        except Exception as e:
            raise DatabaseError(f"Failed To Fetch Profile : {e}") from e
        if profile is None:
            raise RecordNotFoundError(
                f"Profile '{profile_id}' Not Found",
                details={"profile_id": profile_id},
            )
        return ProfileDTO.model_validate(profile)

    async def exists(self, profile_id: str) -> bool:
        """
        Checks whether a profile exists

        Args:
            profile_id (str): The profile id

        Returns:
            `True` if the profile exists

        Raises:
            DatabaseError: If the lookup fails
        """
        try:
            return await self.session.get(Profile, profile_id) is not None
        except Exception as e:
            raise DatabaseError(f"Failed To Check Profile : {e}") from e

    async def ensure(self, profile_id: str) -> ProfileDTO:
        """
        Returns a profile, creating it if it doesn't exist

        Args:
            profile_id (str): The profile id

        Returns:
            The existing or newly-created `ProfileDTO`

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            profile = await self.session.get(Profile, profile_id)
            if profile is None:
                profile = Profile(id=profile_id)
                self.session.add(profile)
                await self.session.flush()
            return ProfileDTO.model_validate(profile)
        except Exception as e:
            raise DatabaseError(f"Failed To Ensure Profile : {e}") from e

    async def delete(self, profile_id: str) -> None:
        """
        Deletes a profile and cascades to its related records

        Args:
            profile_id (str): The profile id

        Raises:
            RecordNotFoundError: If the profile does not exist
            DatabaseError: If the deletion fails
        """
        profile = await self.session.get(Profile, profile_id)
        if profile is None:
            raise RecordNotFoundError(
                f"Profile '{profile_id}' Not Found",
                details={"profile_id": profile_id},
            )
        try:
            await self.session.delete(profile)
        except Exception as e:
            raise DatabaseError(f"Failed To Delete Profile : {e}") from e


class FileRepository:
    """
    Data access for `File` records

    Attributes:
        session (AsyncSession): The active asynchronous database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        profile_id: str,
        name: str,
        path: str,
        type: str | None = None,
    ) -> FileDTO:
        """
        Adds a file record

        Args:
            profile_id (str): Owning profile id
            name (str): Base file name
            path (str): Media-relative path to the file
            type (str | None): Optional file-type tag

        Returns:
            The created `FileDTO`

        Raises:
            DatabaseError: If the insert fails
        """
        try:
            file = File(
                profile_id=profile_id,
                name=name,
                path=path,
                type=type,
            )
            self.session.add(file)
            await self.session.flush()
            return FileDTO.model_validate(file)
        except Exception as e:
            raise DatabaseError(f"Failed To Add File : {e}") from e

    async def get(self, file_id: _Uuid) -> FileDTO:
        """
        Fetches a file by id

        Args:
            file_id (uuid.UUID | str): The file id

        Returns:
            The matching `FileDTO`

        Raises:
            RecordNotFoundError: If the file does not exist
            DatabaseError: If the lookup fails
        """
        try:
            file = await self.session.get(File, file_id)
        except Exception as e:
            raise DatabaseError(f"Failed To Fetch File: {e}") from e
        if file is None:
            raise RecordNotFoundError(
                f"File '{file_id}' Not Found",
                details={"file_id": str(file_id)},
            )
        return FileDTO.model_validate(file)

    async def list_for_profile(self, profile_id: str) -> list[FileDTO]:
        """
        Lists all files belonging to a profile

        Args:
            profile_id (str): Owning profile id

        Returns:
            A list of `FileDTO`, newest first

        Raises:
            DatabaseError: If the query fails
        """
        try:
            stmt = (
                select(File)
                .where(File.profile_id == profile_id)
                .order_by(File.created_at.desc())
            )
            rows = (await self.session.scalars(stmt)).all()
            return [FileDTO.model_validate(r) for r in rows]
        except Exception as e:
            raise DatabaseError(f"Failed To List Files : {e}") from e

    async def delete(self, file_id: _Uuid) -> None:
        """
        Deletes a file record

        Args:
            file_id (uuid.UUID | str): The file id

        Raises:
            RecordNotFoundError: If the file does not exist
            DatabaseError: If the deletion fails
        """
        file = await self.session.get(File, file_id)
        if file is None:
            raise RecordNotFoundError(
                f"File '{file_id}' Not Found",
                details={"file_id": str(file_id)},
            )
        try:
            await self.session.delete(file)
        except Exception as e:
            raise DatabaseError(f"Failed To Delete File : {e}") from e


class TranscriptRepository:
    """
    Data access for `Transcript` records

    Attributes:
        session (AsyncSession): The active asynchronous database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        profile_id: str,
        file_id: _Uuid,
        text: str,
        llm_explanation: str | None = None,
    ) -> TranscriptDTO:
        """
        Adds a transcript record

        Args:
            profile_id (str): Owning profile id
            file_id (uuid.UUID | str): Source file id
            text (str): The transcription text
            llm_explanation (str | None): Optional saved explanation

        Returns:
            The created `TranscriptDTO`

        Raises:
            DatabaseError: If the insert fails
        """
        try:
            transcript = Transcript(
                profile_id=profile_id,
                file_id=file_id,
                text=text,
                llm_explanation=llm_explanation,
            )
            self.session.add(transcript)
            await self.session.flush()
            return TranscriptDTO.model_validate(transcript)
        except Exception as e:
            raise DatabaseError(f"Failed To Add Transcript : {e}") from e

    async def get(self, transcript_id: _Uuid) -> TranscriptDTO:
        """
        Fetches a transcript by id

        Args:
            transcript_id (uuid.UUID | str): The transcript id

        Returns:
            The matching `TranscriptDTO`

        Raises:
            RecordNotFoundError: If the transcript does not exist
            DatabaseError: If the lookup fails
        """
        try:
            transcript = await self.session.get(Transcript, transcript_id)
        except Exception as e:
            raise DatabaseError(f"Failed To Fetch Transcript : {e}") from e
        if transcript is None:
            raise RecordNotFoundError(
                f"Transcript '{transcript_id}' Not Found",
                details={"transcript_id": str(transcript_id)},
            )
        return TranscriptDTO.model_validate(transcript)

    async def list_for_profile(
        self,
        profile_id: str,
        load_file: bool = False,
    ) -> list[TranscriptDTO]:
        """
        Lists all transcripts belonging to a profile

        Args:
            profile_id (str): Owning profile id
            load_file (bool): Eagerly load the related file

        Returns:
            A list of `TranscriptDTO`, newest first

        Raises:
            DatabaseError: If the query fails
        """
        try:
            stmt = (
                select(Transcript)
                .where(Transcript.profile_id == profile_id)
                .order_by(Transcript.created_at.desc())
            )
            if load_file:
                stmt = stmt.options(joinedload(Transcript.file))
            rows = (await self.session.scalars(stmt)).all()
            return [TranscriptDTO.model_validate(r) for r in rows]
        except Exception as e:
            raise DatabaseError(f"Failed To List Transcripts : {e}") from e

    async def delete(self, transcript_id: _Uuid) -> None:
        """
        Deletes a transcript record

        Args:
            transcript_id (uuid.UUID | str): The transcript id

        Raises:
            RecordNotFoundError: If the transcript does not exist
            DatabaseError: If the deletion fails
        """
        transcript = await self.session.get(Transcript, transcript_id)
        if transcript is None:
            raise RecordNotFoundError(
                f"Transcript '{transcript_id}' Not Found",
                details={"transcript_id": str(transcript_id)},
            )
        try:
            await self.session.delete(transcript)
        except Exception as e:
            raise DatabaseError(f"Failed To Delete Transcript : {e}") from e


class LlmTemplateRepository:
    """
    Data access for a profile's unique `LlmTemplate`

    Attributes:
        session (AsyncSession): The active asynchronous database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_profile(
        self,
        profile_id: str,
    ) -> LlmTemplateDTO | None:
        """
        Fetches the template for a profile, if any

        Args:
            profile_id (str): Owning profile id

        Returns:
            The `LlmTemplateDTO`, or `None` when the profile has no template

        Raises:
            DatabaseError: If the lookup fails
        """
        try:
            stmt = select(LlmTemplate).where(
                LlmTemplate.profile_id == profile_id,
            )
            template = (await self.session.scalars(stmt)).first()
        except Exception as e:
            raise DatabaseError(f"Failed To Fetch Template : {e}") from e
        if template is None:
            return None
        return LlmTemplateDTO.model_validate(template)

    async def upsert(
        self,
        profile_id: str,
        sys_msg: str,
        prompt: str,
        model: str,
        srt_sys_msg: str = "",
        srt_model: str = "",
    ) -> LlmTemplateDTO:
        """
        Creates or updates the unique template for a profile

        Args:
            profile_id (str): Owning profile id
            sys_msg (str): System message
            prompt (str): Prompt template
            model (str): Model selector in `provider:model` form
            srt_sys_msg (str): Subtitle-fix system message (empty = default)
            srt_model (str): Subtitle-fix model override (empty = use `model`)

        Returns:
            The created or updated `LlmTemplateDTO`

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            stmt = select(LlmTemplate).where(
                LlmTemplate.profile_id == profile_id,
            )
            template = (await self.session.scalars(stmt)).first()
            if template is None:
                template = LlmTemplate(
                    profile_id=profile_id,
                    sys_msg=sys_msg,
                    prompt=prompt,
                    model=model,
                    srt_sys_msg=srt_sys_msg,
                    srt_model=srt_model,
                )
                self.session.add(template)
            else:
                template.sys_msg = sys_msg
                template.prompt = prompt
                template.model = model
                template.srt_sys_msg = srt_sys_msg
                template.srt_model = srt_model
            await self.session.flush()
            return LlmTemplateDTO.model_validate(template)
        except Exception as e:
            raise DatabaseError(f"Failed to Upsert Template : {e}") from e

    async def delete(self, profile_id: str) -> None:
        """
        Deletes a profile's template

        Args:
            profile_id (str): Owning profile id

        Raises:
            RecordNotFoundError: If the profile has no template
            DatabaseError: If the deletion fails
        """
        stmt = select(LlmTemplate).where(
            LlmTemplate.profile_id == profile_id,
        )
        template = (await self.session.scalars(stmt)).first()
        if template is None:
            raise RecordNotFoundError(
                f"Template For Profile '{profile_id}' Not Found",
                details={"profile_id": profile_id},
            )
        try:
            await self.session.delete(template)
        except Exception as e:
            raise DatabaseError(f"Failed To Delete Template : {e}") from e


class ClipRepository:
    """
    Data access for `Clip` records

    Attributes:
        session (AsyncSession): The active asynchronous database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        profile_id: str,
        file_id: _Uuid,
        start_time: float,
        end_time: float,
        llm_breakdown_response: dict[str, Any],
    ) -> ClipDTO:
        """
        Adds a clip record

        Args:
            profile_id (str): Owning profile id
            file_id (uuid.UUID | str): Source file id
            start_time (float): Clip start time in seconds
            end_time (float): Clip end time in seconds
            llm_breakdown_response (dict): Serialized breakdown payload

        Returns:
            The created `ClipDTO`

        Raises:
            DatabaseError: If the insert fails
        """
        try:
            clip = Clip(
                profile_id=profile_id,
                file_id=file_id,
                start_time=start_time,
                end_time=end_time,
                llm_breakdown_response=llm_breakdown_response,
            )
            self.session.add(clip)
            await self.session.flush()
            return ClipDTO.model_validate(clip)
        except Exception as e:
            raise DatabaseError(f"Failed To Add Clip : {e}") from e

    async def get(self, clip_id: _Uuid) -> ClipDTO:
        """
        Fetches a clip by id

        Args:
            clip_id (uuid.UUID | str): The clip id

        Returns:
            The matching `ClipDTO`

        Raises:
            RecordNotFoundError: If the clip does not exist
            DatabaseError: If the lookup fails
        """
        try:
            clip = await self.session.get(Clip, clip_id)
        except Exception as e:
            raise DatabaseError(f"Failed To Fetch Clip : {e}") from e
        if clip is None:
            raise RecordNotFoundError(
                f"Clip '{clip_id}' Not Found",
                details={"clip_id": str(clip_id)},
            )
        return ClipDTO.model_validate(clip)

    async def list_for_profile(
        self,
        profile_id: str,
        load_file: bool = False,
    ) -> list[ClipDTO]:
        """
        Lists all clips belonging to a profile

        Args:
            profile_id (str): Owning profile id
            load_file (bool): Eagerly load the related file

        Returns:
            A list of `ClipDTO`, newest first

        Raises:
            DatabaseError: If the query fails
        """
        try:
            stmt = (
                select(Clip)
                .where(Clip.profile_id == profile_id)
                .order_by(Clip.created_at.desc())
            )
            if load_file:
                stmt = stmt.options(joinedload(Clip.file))
            rows = (await self.session.scalars(stmt)).all()
            return [ClipDTO.model_validate(r) for r in rows]
        except Exception as e:
            raise DatabaseError(f"Failed To List Clips: {e}") from e

    async def delete(self, clip_id: _Uuid) -> None:
        """
        Deletes a clip record

        Args:
            clip_id (uuid.UUID | str): The clip id

        Raises:
            RecordNotFoundError: If the clip does not exist
            DatabaseError: If the deletion fails
        """
        clip = await self.session.get(Clip, clip_id)
        if clip is None:
            raise RecordNotFoundError(
                f"Clip '{clip_id}' Not Found",
                details={"clip_id": str(clip_id)},
            )
        try:
            await self.session.delete(clip)
        except Exception as e:
            raise DatabaseError(f"Failed To Delete Clip : {e}") from e
