"""
FastAPI request-scoped dependencies that bridge transport concerns (headers,
streamed request bodies) to the domain layer

Kept separate from `media` so that module stays pure storage logic with no
FastAPI coupling
"""

import logging
from pathlib import Path

from fastapi import Header, Request

from . import media

LOGGER = logging.getLogger(__name__)


async def get_stream_file(
    request: Request,
    upload_id: str = Header(..., alias="X-Upload-ID"),
    file_name: str = Header(..., alias="X-File-Name"),
) -> Path:
    """
    Endpoint dependency that saves a streamed upload to temporary storage

    Args:
        request (Request): The `FastAPI.Request` object
        upload_id (str): `X-Upload-ID` header identifying the upload
        file_name (str): `X-File-Name` header with the original file name

    Returns:
        The path where the streamed file was saved

    Raises:
        UploadError: If the upload fails (mapped to HTTP 400 by the app's
            exception handler)
    """
    temp_dir = media.get_temp_dir(upload_id)
    dest = temp_dir / file_name
    return await media.save_upload_file(request, dest)
