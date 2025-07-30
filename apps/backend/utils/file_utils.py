"""
This module provides helper functions for file operations.
"""
import logging
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from tqdm.auto import tqdm

LOGGER = logging.getLogger(__name__)


async def save_upload_file(upload_file: UploadFile,
                           dest: Path,
                           chunk_size: int = 1048576,
                           tqdm_description: Optional[str] = None
                           ) -> None:
    """
    Saves a `FastAPI.UploadFile` by reading and writing `chunk_size` lengthed
    chunks to `dest` and displaying a `TQDM` progress bar in logging.

    Args:
      upload_file (UploadFile): The file uploaded via a FastAPI endpoint.
      dest (Path): The path where the file will be saved.
      chunk_size (int, optional): Size of chunk to read and write per
                                  iteration. Defaults to 1MB
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
                while content := await upload_file.read(chunk_size):
                    await f.write(content)
                    p.update(len(content))
                    total_content += len(content)
        LOGGER.info(f"Saved {total_content} bytes to {dest}")
    except Exception as e:
        LOGGER.error(
            f"Failed to save uploaded file '{upload_file.filename}' "
            f"to '{dest}'. Error: {e}"
        )
        # Clean up partially created file on error
        dest.unlink(missing_ok=True)
        raise
