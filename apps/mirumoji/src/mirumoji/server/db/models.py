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

LOGGER = logging.getLogger("mirumoji")


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

    llm_breakdown_response: Mapped[dict] = mapped_column(
        JSON,
    )

    created_at: Mapped[datetime] = mapped_column(default=get_now_utc)


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
        created_at (datetime): UTC creation timestamp
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    name: str
    path: str
    type: str | None
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
    """

    id: uuid.UUID
    profile_id: str
    profile: ProfileDTO | None
    sys_msg: str
    prompt: str
    model: str


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
    llm_breakdown_response: dict
    created_at: datetime
