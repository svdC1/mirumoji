from fastapi import Header, HTTPException, Depends, status
from db.db import get_db
from db.Tables import profiles
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def get_profile_id_from_header(x_profile_id: str = Header(None)
                                     ) -> Optional[str]:
    """
    Simply extracts X-Profile-ID header if present.
    """
    return x_profile_id


async def ensure_profile_exists(
    profile_id: str = Depends(get_profile_id_from_header)
) -> str:
    """
    Ensures a profile exists for the given ID. If ID is None or profile
    doesn't exist and cannot be created, raises HTTPException.
    """
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Profile-ID header is required for this operation."
        )

    db = await get_db()
    query = profiles.select().where(profiles.c.id == profile_id)
    profile = await db.fetch_one(query)
    if not profile:
        try:
            insert_query = profiles.insert().values(id=profile_id,
                                                    name=profile_id)
            await db.execute(insert_query)
            logger.info(f"Implicitly created profile with ID: {profile_id}")
        except Exception as e:
            logger.error(f"Error creating profile {profile_id}: {e}")
            # Check if it was created by another request in the meantime
            profile_check_after_error = await db.fetch_one(query)
            if not profile_check_after_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not create or find profile {profile_id}.")
    return profile_id


async def get_profile_id_optional(
    profile_id: str = Depends(get_profile_id_from_header)
) -> str | None:
    """Returns the profile ID if X-Profile-ID is provided and the profile
    exists (implicitly creates if new). Returns None if header is missing."""
    if not profile_id:
        return None

    # If header is provided, ensure profile exists (or create it)
    db = await get_db()
    query = profiles.select().where(profiles.c.id == profile_id)
    profile = await db.fetch_one(query)
    if not profile:
        try:
            insert_query = profiles.insert().values(id=profile_id,
                                                    name=profile_id)
            await db.execute(insert_query)
            logger.info(f"Implicitly created profile with\
                ID (optional context): {profile_id}")
        except Exception as e:
            logger.error(f"Error creating profile {profile_id} \
                (optional context): {e}")
            # Check again in case of race condition
            profile_check_after_error = await db.fetch_one(query)
            if not profile_check_after_error:
                # Don't raise 500 here, as profile is optional.
                logger.error(f"Could not find or create profile \
                    {profile_id} (optional context) after error.")
                return None
    return profile_id
