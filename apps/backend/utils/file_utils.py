"""
This module provides helper functions for file operations.
"""
import logging
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import (Request,
                     Header,
                     HTTPException
                     )
from tqdm.auto import tqdm

LOGGER = logging.getLogger(__name__)
BASE_MEDIA_DIR = Path("media_files")
TEMP_DIR = BASE_MEDIA_DIR / "temp"


async def save_upload_file(request: Request,
                           dest: Path,
                           tqdm_description: Optional[str] = None
                           ) -> None:
    """
    Saves a `FastAPI.Request.stream` by reading and writing streamed
    chunks to `dest` and displaying a `TQDM` progress bar in logging.

    Args:
      request (UploadFile): FastAPI `Request` object.
      dest (Path): The path where the file will be saved.
      tqdm_description (str, optional): Description of the progress bar in
                                        logging. Defaults to None

    Raises:
      Exception: If the upload fails for any reason.
    """
    if tqdm_description is None:
        tqdm_description = f"Saving file to {dest}"
    try:
        total_content = 0
        with tqdm(unit="B", unit_scale=True, desc=tqdm_description) as p:
            async with aiofiles.open(dest, "wb+") as f:
                async for chunk in request.stream():
                    await f.write(chunk)
                    p.update(len(chunk))
                    total_content += len(chunk)
        LOGGER.info(f"Saved {total_content} bytes to {dest}")
    except Exception as e:
        LOGGER.error(
            f"Failed to save uploaded stream"
            f"to '{dest}'. Error: '{e}'"
        )
        # Clean up partially created file on error
        dest.unlink(missing_ok=True)
        raise


async def get_stream_file(request: Request,
                          upload_id: str = Header(..., alias="X-Upload-ID"),
                          file_name: str = Header(..., alias="X-File-Name")
                          ) -> Path:
    """
    Endpoint dependency to save a streamed file to local storage

    Args:
      request (Request): FastAPI `Request` object.
      upload_id (str): Header sent from frontend with upload id
      file_name (str): Header sent from frontend with file name

    Returns:
      Path: Path where the file was saved

    Raises:
      HTTPException: If upload fails or headers are not present
    """
    temp_file_path = TEMP_DIR / f"{upload_id}" / f"{file_name}"
    try:
        await save_upload_file(request,
                               temp_file_path
                               )
    except Exception as e:
        HTTPException(status_code=400, detail=f"{e}")
