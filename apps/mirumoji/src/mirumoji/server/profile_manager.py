"""
Defines FastAPI dependencies for managing Mirumoji `Profile` access

Attributes:
    LOGGER (logging.Logger): Module's logging object
"""

import logging

from fastapi import Depends, Header, HTTPException, status

from .db import UnitOfWork

LOGGER = logging.getLogger(__name__)


async def get_profile_id_from_header(
    x_profile_id: str = Header(None),
) -> str | None:
    """
    Extracts the `X-Profile-ID` header, if present

    Args:
        x_profile_id (str): The `X-Profile-ID` header

    Returns:
        The header value, or `None` when absent
    """
    return x_profile_id


async def ensure_profile_exists(
    profile_id: str = Depends(get_profile_id_from_header),
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
            detail="X-Profile-ID header is required for this operation.",
        )
    async with UnitOfWork() as uow:
        await uow.profiles.ensure(profile_id)
        await uow.commit()
    return profile_id


async def get_profile_id_optional(
    profile_id: str = Depends(get_profile_id_from_header),
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
