"""
FastAPI request-scoped dependencies that bridge transport concerns (headers)
to the domain layer
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, cast

from fastapi import Depends, Header, HTTPException, Request, status

from .db import UnitOfWork

if TYPE_CHECKING:
    from .jobs import JobQueueManager
    from .processing.processor import Processor

LOGGER = logging.getLogger(__name__)


def get_processor(request: Request) -> Processor:
    """
    Endpoint dependency returning the lifespan-scoped `Processor`

    Args:
        request (Request): The `FastAPI.Request` object

    Returns:
        The single `Processor` instance built during application startup
    """
    return cast("Processor", request.app.state.processor)


def get_job_manager(request: Request) -> JobQueueManager:
    """
    Endpoint dependency returning the lifespan-scoped `JobQueueManager`

    Args:
        request (Request): The `FastAPI.Request` object

    Returns:
        The single `JobQueueManager` built during application startup
    """
    return cast("JobQueueManager", request.app.state.job_manager)


async def get_profile_id_from_header(
    x_profile_id: Annotated[str | None, Header()] = None,
) -> str | None:
    """
    Extracts the `X-Profile-ID` header, returning `None` when it's not present

    Args:
        x_profile_id (str | None): The `X-Profile-ID` Header

    Returns:
        The Header value, or `None` when absent
    """
    return x_profile_id


async def ensure_profile_exists(
    profile_id: Annotated[
        str | None,
        Depends(get_profile_id_from_header),
    ],
) -> str:
    """
    Dependency that requires `X-Profile-ID` and ensures the profile exists

    Implicitly creates the profile when it doesn't exist yet

    Args:
        profile_id (str): Profile id from the header

    Returns:
        The validated profile id

    Raises:
        HTTPException: If the `X-Profile-ID` header is missing
        DatabaseError: If the profile can't be read or created
    """
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID Header Is Required For This Operation",
        )
    async with UnitOfWork() as uow:
        await uow.profiles.ensure(profile_id)
        await uow.commit()
    return profile_id


async def get_profile_id_optional(
    profile_id: Annotated[
        str | None,
        Depends(get_profile_id_from_header),
    ],
) -> str | None:
    """
    Dependency that returns the profile id when present, ensuring it exists

    Args:
        profile_id (str): Profile id from the header

    Returns:
        The validated profile id, or `None` when the header is absent

    Raises:
        DatabaseError: If the profile can't be read or created
    """
    if not profile_id:
        return None
    async with UnitOfWork() as uow:
        await uow.profiles.ensure(profile_id)
        await uow.commit()
    return profile_id
