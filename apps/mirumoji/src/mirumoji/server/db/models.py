"""Defines the database models and data transfer objects

Defines the schema for the miurmoji database and `pydantic` DTOs for all
tables. DTOs share a common base `pydantic` model to handle instantiation
directly from ORM objects without running into async lazy-loading errors
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import (
    JSON,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    inspect,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    base,
    mapped_column,
    relationship,
)

LOGGER = logging.getLogger(__name__)


# --- HELPERS ---


def get_now_utc() -> datetime:
    """
    Generates the current datetime in UTC

    Returns:
        The current UTC time
    """
    return datetime.now(timezone.utc)


class SafeORMModel(BaseModel):
    """
    Pydantic base for ORM-backed DTOs that tolerates unloaded relationships

    Validates directly from SQLAlchemy instances (`from_attributes`), but
    first replaces any relationship field that wasn't eagerly loaded with
    `None` instead of triggering a lazy load, which would fail under async
    """

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def check_sqlalchemy_state(cls, data: Any) -> Any:
        """
        Builds a validation-safe mapping from a SQLAlchemy instance

        Maps unloaded relationship fields to `None` so that validation never
        triggers an async-unsafe lazy load. Inputs that aren't SQLAlchemy
        instances are returned unchanged

        Args:
            data (Any): The value being validated (ORM instance or mapping)

        Returns:
            A mapping safe for Pydantic validation, or `data` unchanged when
                it isn't a SQLAlchemy instance
        """

        # Check If The Object is an SQLAlchemy Instance
        state = inspect(data, raiseerr=False)
        if state is None:
            # Return Input Object Unchanged
            return data

        # Get Fields That Have NOT Been Eagerly-Loaded
        # joinedloaded / selectinloaded)
        unloaded_fields = state.unloaded

        # Get Fields That Are Already Locally Populated In Python Memory
        loaded_data = base.instance_dict(data)

        # Build A Safe Dictionary For Pydantic
        safe_dict: dict[str, Any] = {}
        for field_name in cls.model_fields:
            if field_name in unloaded_fields:
                # Set relationship fields that haven't been laoded to None
                safe_dict[field_name] = None

            elif field_name in loaded_data:
                safe_dict[field_name] = loaded_data[field_name]

            else:
                # Fallback for calculated fields, hybrid properties, or custom
                # Python properties that don't show up in instance_dict
                safe_dict[field_name] = getattr(data, field_name, None)

        return safe_dict


# --- SCHEMA ---


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy declarative models

    Inherits from SQLAlchemy's DeclarativeBase to provide a unified
    metadata registry for the mirumoji's ORM models
    """

    pass


class Profile(Base):
    """
    SQLAlchemy model representing a mirumoji profile

    Attributes:
        id (str): Client-supplied profile identifier (primary key)
        created_at (datetime): UTC creation timestamp
    """

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=get_now_utc)


class File(Base):
    """
    SQLAlchemy model representing a single file tied to a profile

    Attributes:
        id (uuid.UUID): File identifier (primary key)
        profile_id (str): Owning profile id (foreign key, cascade delete)
        profile (Profile): The owning profile relationship
        name (str): Base file name
        path (str): Media-relative path to the file
        type (str | None): Optional file-type tag
        folder (str | None): Optional group label for files uploaded together
            (e.g. a picked directory's name), used to group the file list
        source_file_id (uuid.UUID | None): The root media this file derives
            from (a generated / fixed SRT or a converted MP4 points at its
            source video). NULL means the file is itself a root. ON DELETE SET
            NULL, so deleting a source orphans its derivatives rather than
            removing them
        origin (str | None): How the file came to be (`upload`, `generated`,
            `fixed`, `converted`, `subtitle`, or `clip`), used for the UI's
            variant label
        created_at (datetime): UTC creation timestamp
    """

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
    )

    profile: Mapped[Profile] = relationship(passive_deletes="all")

    name: Mapped[str] = mapped_column(
        String(500),
    )

    path: Mapped[str] = mapped_column(
        String(500),
    )

    type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    folder: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    source_file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    origin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=get_now_utc)


class Transcript(Base):
    """
    SQLAlchemy model representing a transcript tied to a profile and a file

    Attributes:
        id (uuid.UUID): Transcript identifier (primary key)
        profile_id (str): Owning profile id (foreign key, cascade delete)
        profile (Profile): The owning profile relationship
        file_id (uuid.UUID): Source file id (foreign key, cascade delete)
        file (File): The source file relationship
        text (str): The transcription text
        llm_explanation (str | None): Optional saved LLM explanation
        created_at (datetime): UTC creation timestamp
    """

    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
    )

    profile: Mapped[Profile] = relationship(passive_deletes="all")

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
    )

    file: Mapped[File] = relationship(passive_deletes="all")

    text: Mapped[str] = mapped_column(
        Text,
    )

    llm_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=get_now_utc)


class LlmTemplate(Base):
    """
    SQLAlchemy model representing a profile's unique LLM template

    Attributes:
        id (uuid.UUID): Template identifier (primary key)
        profile_id (str): Owning profile id (foreign key, unique, cascade
            delete)
        profile (Profile): The owning profile relationship
        sys_msg (str): System message
        prompt (str): Prompt template
        model (str): Model selector in `provider:model` form
        srt_sys_msg (str): Subtitle-fix system message (empty = default)
        srt_model (str): Subtitle-fix model override (empty = use `model`)
    """

    __tablename__ = "llm_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), unique=True
    )

    profile: Mapped[Profile] = relationship(passive_deletes="all")

    sys_msg: Mapped[str] = mapped_column(
        Text,
    )

    prompt: Mapped[str] = mapped_column(
        Text,
    )

    model: Mapped[str] = mapped_column(
        String(100),
    )

    # Subtitle-Fix (LLM `/llm/fix_srt`) Overrides
    # Falls back to `model` and Server Default SRT SysMsg
    srt_sys_msg: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    srt_model: Mapped[str] = mapped_column(
        String(100),
        default="",
    )


class Clip(Base):
    """
    SQLAlchemy model representing a clip tied to a profile and a file

    Attributes:
        id (uuid.UUID): Clip identifier (primary key)
        profile_id (str): Owning profile id (foreign key, cascade delete)
        profile (Profile): The owning profile relationship
        file_id (uuid.UUID): Source file id (foreign key, cascade delete)
        file (File): The source file relationship
        start_time (float): Clip start time in seconds
        end_time (float): Clip end time in seconds
        llm_breakdown_response (dict): Serialized breakdown payload
        created_at (datetime): UTC creation timestamp
    """

    __tablename__ = "clips"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
    )

    profile: Mapped[Profile] = relationship(passive_deletes="all")

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
    )

    file: Mapped[File] = relationship(passive_deletes="all")

    start_time: Mapped[float] = mapped_column(
        Float,
    )

    end_time: Mapped[float] = mapped_column(
        Float,
    )

    llm_breakdown_response: Mapped[dict[str, Any]] = mapped_column(
        JSON,
    )

    created_at: Mapped[datetime] = mapped_column(default=get_now_utc)


class Job(Base):
    """
    SQLAlchemy model representing a long-running processing job

    abstract: Mirumoji Server Jobs
        - A job runs one operation (transcription, SRT generation, conversion,
          or LLM SRT-fixing) server-side using an existing profile file, so
          that the client can submit it and track it across navigation

        - A batch is a parent job with one child job per file (`parent_id`),
          and the parent aggregates `total` / `completed`

    Attributes:
        id (uuid.UUID): Job identifier (primary key)
        profile_id (str): Owning profile id (foreign key, cascade delete)
        profile (Profile): The owning profile relationship
        parent_id (uuid.UUID | None): Parent batch job id, when this is a child
        type (str): Operation type (e.g. `transcribe`, `generate_srt`,
            `convert`, `fix_srt`, or a `batch_*` variant)
        status (str): `queued`, `running`, `succeeded`, `failed`, or
            `cancelled`
        progress (float): Progress fraction in `[0, 1]`
        total (int): Number of work items (1 for a single job, N for a batch)
        completed (int): Number of finished work items
        params (dict): Submitted parameters (file references, options)
        result (dict | None): Produced references (file / transcript / SRT ids)
            or `None` until finished
        error (str | None): Failure message when `status` is `failed`
        error_code (str | None): Stable error code on failure (the domain
            exception's `code`, or `ServerError` for an unexpected failure)
        error_details (dict | None): Optional structured error context
        created_at (datetime): UTC creation timestamp
        updated_at (datetime): UTC last-update timestamp
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
    )

    profile: Mapped[Profile] = relationship(passive_deletes="all")

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="queued",
        index=True,
    )

    progress: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    total: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    completed: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    params: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=get_now_utc)

    updated_at: Mapped[datetime] = mapped_column(
        default=get_now_utc,
        onupdate=get_now_utc,
    )


# --- DTOs ---


class ProfileDTO(SafeORMModel):
    """
    Represents a single profile stored in the mirumoji database

    Attributes:
        id (str): Profile identifier
        created_at (datetime): UTC creation timestamp
    """

    id: str
    created_at: datetime


class FileDTO(SafeORMModel):
    """
    Represents a single profile file reference stored in the mirumoji database

    Attributes:
        id (uuid.UUID): File identifier
        profile_id (str): Owning profile id
        profile (ProfileDTO | None): Owning profile, when loaded
        name (str): Base file name
        path (str): Media-relative path to the file
        type (str | None): Optional file-type tag
        folder (str | None): Optional group label for files uploaded together
        source_file_id (uuid.UUID | None): The root media this file derives
            from, or NULL when it is itself a root
        origin (str | None): How the file came to be (`upload`, `generated`,
            `fixed`, `converted`, `subtitle`, or `clip`)
        created_at (datetime): UTC creation timestamp
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    name: str
    path: str
    type: str | None
    folder: str | None = None
    source_file_id: uuid.UUID | None = None
    origin: str | None = None
    created_at: datetime


class TranscriptDTO(SafeORMModel):
    """
    Represents a single profile transcript stored in the mirumoji database

    Attributes:
        id (uuid.UUID): Transcript identifier
        profile_id (str): Owning profile id
        profile (ProfileDTO | None): Owning profile, when loaded
        file_id (uuid.UUID): Source file id
        file (FileDTO | None): Source file, when loaded
        text (str): The transcription text
        llm_explanation (str | None): Optional saved LLM explanation
        created_at (datetime): UTC creation timestamp
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    file_id: uuid.UUID
    file: FileDTO | None
    text: str
    llm_explanation: str | None
    created_at: datetime


class LlmTemplateDTO(SafeORMModel):
    """
    Represents a profile's LLM template stored in the mirumoji database

    Attributes:
        id (uuid.UUID): Template identifier
        profile_id (str): Owning profile id
        profile (ProfileDTO | None): Owning profile, when loaded
        sys_msg (str): System message
        prompt (str): Prompt template
        model (str): Model selector in `provider:model` form
        srt_sys_msg (str): Subtitle-fix system message (empty = default)
        srt_model (str): Subtitle-fix model override (empty = use `model`)
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    sys_msg: str
    prompt: str
    model: str
    srt_sys_msg: str = ""
    srt_model: str = ""


class ClipDTO(SafeORMModel):
    """
    Represents a single profile clip reference saved in the mirumoji database

    Attributes:
        id (uuid.UUID): Clip identifier
        profile_id (str): Owning profile id
        profile (ProfileDTO | None): Owning profile, when loaded
        file_id (uuid.UUID): Source file id
        file (FileDTO | None): Source file, when loaded
        start_time (float): Clip start time in seconds
        end_time (float): Clip end time in seconds
        llm_breakdown_response (dict): Serialized breakdown payload
        created_at (datetime): UTC creation timestamp
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    file_id: uuid.UUID
    file: FileDTO | None
    start_time: float
    end_time: float
    llm_breakdown_response: dict[str, Any]
    created_at: datetime


class JobDTO(SafeORMModel):
    """
    Represents a single processing job stored in the mirumoji database

    Attributes:
        id (uuid.UUID): Job identifier
        profile_id (str): Owning profile id
        profile (ProfileDTO | None): Owning profile, when loaded
        parent_id (uuid.UUID | None): Parent batch job id, when this is a child
        type (str): Operation type
        status (str): `queued`, `running`, `succeeded`, `failed`, or
            `cancelled`
        progress (float): Progress fraction in `[0, 1]`
        total (int): Number of work items
        completed (int): Number of finished work items
        params (dict): Submitted parameters
        result (dict | None): Produced references, or `None` until finished
        error (str | None): Failure message when `status` is `failed`
        error_code (str | None): Stable error code on failure
        error_details (dict | None): Optional structured error context
        created_at (datetime): UTC creation timestamp
        updated_at (datetime): UTC last-update timestamp
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    parent_id: uuid.UUID | None
    type: str
    status: str
    progress: float
    total: int
    completed: int
    params: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    error_code: str | None
    error_details: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
