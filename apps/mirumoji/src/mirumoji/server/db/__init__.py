"""
Deines the Mirumoji Database layer

Configures the SQLAlchemy AsyncEngine + Session Factory lazily so that
importing the package has no side effects and tests can point elsewhere.
In addition, defines the  `UnitOfWork` that bundles the entity repositories
behind a single transaction boundary
"""

from __future__ import annotations

import logging
from functools import lru_cache
from types import TracebackType
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool.base import _ConnectionRecord

from ..constants import DB_URL, HOST_DB_PATH
from .models import Base
from .repos import (
    ClipRepository,
    FileRepository,
    LlmTemplateRepository,
    ProfileRepository,
    TranscriptRepository,
)

LOGGER = logging.getLogger("mirumoji")


def _set_sqlite_pragma(
    dbapi_connection: Any,
    connection_record: _ConnectionRecord,
) -> None:
    """
    Enforces SQLite pragmas on every new connection

    Enables foreign keys, Write-Ahead Logging, and normal synchronous mode for
    better concurrency and performance

    Args:
        dbapi_connection (Any): The raw DBAPI connection passed by SQLAlchemy's
            sync `connect` event (the aiosqlite DBAPI adapter)
        connection_record (_ConnectionRecord): The connection record
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """
    Builds the `AsyncEngine` bound to `DB_URL` or returns a cached engine if
    the function has already been called once during the application's lifetime

    info: Additional Information
        - The PRAGMA listener (`_set_sqlite_pragma`) is attached on creation

        - This funcion is cached so that the whole process shares a single
          engine

    Returns:
        The async SQLAlchemy engine
    """
    engine = create_async_engine(DB_URL)
    event.listen(engine.sync_engine, "connect", _set_sqlite_pragma)
    return engine


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Builds an `SQLAlchemy` `AsyncSession` factory bound to the engine returned
    by `get_engine`, or returns a cached factory object if the function has
    already been called once during the application's lifetime

    Returns:
        The async session factory bound to the engine
    """
    return async_sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


class UnitOfWork:
    """
    Async transaction boundary bundling the entity repositories

    tip: Usage
        - Enter the async context to open a session and access the mirumoji
          database repositories (`profiles`, `files`, `transcripts`,
          `templates`, `clips`)

        - Call `commit` to persist any changes

        - On exit, any open transaction is rolled back if an exception
          propagated, and the session is always closed

    Args:
        session_factory (async_sessionmaker[AsyncSession]): The `AsyncSession`
            factory to use for creating a new session when entering the async
            context

    Attributes:
        session_factory (async_sessionmaker[AsyncSession]): Factory for new
            sessions
        session (AsyncSession): The active session (within the context)
        profiles (ProfileRepository): Profile data access
        files (FileRepository): File data access
        transcripts (TranscriptRepository): Transcript data access
        templates (LlmTemplateRepository): LLM-template data access
        clips (ClipRepository): Clip data access
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.session_factory = session_factory or get_sessionmaker()

    async def __aenter__(self) -> UnitOfWork:
        """
        Enters the asynchronous runtime context

        Initializes the database session and the associated repositories

        Returns:
            The current UnitOfWork instance
        """

        self.session = self.session_factory()
        self.profiles = ProfileRepository(self.session)
        self.files = FileRepository(self.session)
        self.transcripts = TranscriptRepository(self.session)
        self.templates = LlmTemplateRepository(self.session)
        self.clips = ClipRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Exits the asynchronous runtime context

        Automatically rolls back the transaction and logs the crash if
        an exception occurred within the context block. Always closes the
        active database session

        Args:
            exc_type: The exception class, if an error was raised
            exc_val: The exception instance, if an error was raised
            traceback: The traceback object
        """

        if exc_type is not None:
            LOGGER.exception(
                "Database Transaction Failed - Rolling Back",
            )
            await self.session.rollback()
        await self.session.close()

    async def commit(self) -> None:
        """
        Commits the active database transaction
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """
        Rolls back the active database transaction
        """
        await self.session.rollback()


async def init_db() -> None:
    """
    Creates all database tables on startup if they don't already exist

    Ensures the database's parent directory exists (the platform data dir
    isn't auto-created), then runs the synchronous schema-creation step
    """
    HOST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    LOGGER.info(f"Initialised Mirumoji SQLite Database at {DB_URL}")
