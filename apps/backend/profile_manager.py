"""
Module defining helper functions meant to be run inside
FastAPI endpoints for management of Mirumoji `Profiles`

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
"""

from fastapi import Header, HTTPException, Depends, status
from db.db import DbManager
import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)
db_manager = DbManager()


async def get_profile_id_from_header(
    x_profile_id: str = Header(None)
) -> Optional[str]:
    """
    Function meant to be run inside FastAPI endpoint which
    extracts X-Profile-ID header if present.

    Args:
      x_profile_id (str): The X-Profile-ID Header

    Returns:
      The X-Profile-ID Header content.
    """
    return x_profile_id


async def ensure_profile_exists(
    profile_id: str = Depends(get_profile_id_from_header)
) -> str:
    """
    Function meant to be run inside FastAPI endpoint which
    ensures a profile exists for the given ID.

    Args:
      profile_id (str): The profile ID to check.

    Returns:
      str: The profile ID from input if it exists or
           could be created.

    Raises:
      HTTPException: If ID is None or profile
                     doesn't exist and cannot be created
    """
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required for this operation."
        )

    profile = await db_manager.read("profiles",
                                    {"id": profile_id},
                                    fetch_one=True
                                    )
    if not profile:
        try:
            values = {"id": profile_id, "name": profile_id}
            await db_manager.create("profiles", values)
            LOGGER.info(f"Implicitly created profile with ID: '{profile_id}'")
        except Exception as e:
            LOGGER.exception(f"Error creating profile '{profile_id}': '{e}'")

            # Check if it was created by another request in the meantime
            profile_check_after_error = await db_manager.read(
                "profiles",
                {"id": profile_id},
                fetch_one=True
                )
            if not profile_check_after_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not create or find profile '{profile_id}'.")
    return profile_id


async def get_profile_id_optional(
    profile_id: str = Depends(get_profile_id_from_header)
) -> Optional[str]:
    """
    Function meant to be run inside FastAPI endpoint which returns the content
    of Profile ID Header.

    Args:
      profile_id (str): Profile ID from header.

    Returns:
      If X-Profile-ID is provided and the profile
        exists or could be implicitly created returns str,
        otherwise returns None.
    """
    if not profile_id:
        return None

    # If header is provided, ensure profile exists (or create it)
    profile = await db_manager.read("profiles",
                                    {"id": profile_id},
                                    fetch_one=True
                                    )
    if not profile:
        try:
            values = {"id": profile_id, "name": profile_id}
            await db_manager.create("profiles", values)
            LOGGER.info((f"Implicitly created profile with ID "
                         f"(optional context): '{profile_id}'"))
        except Exception:
            LOGGER.exception(f"Error creating profile '{profile_id}'")

            # Check again in case of race condition
            profile_check_after_error = await db_manager.read(
                "profiles",
                {"id": profile_id},
                fetch_one=True
                )
            if not profile_check_after_error:
                LOGGER.exception((f"Could not find or create profile"
                                  f" '{profile_id}' after error."))
                return None

    return profile_id
