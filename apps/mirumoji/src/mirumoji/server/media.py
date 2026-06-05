"""
Defines helper functions to perform asynchronous file operations within the
`HOST_MEDIA_PATH` directory

abstract: Paths
    - `BASE_PATH` is the media root (`HOST_MEDIA_PATH`)

    - `TEMP_PATH` and `PROFILES_PATH` are its `temp` and `profiles`
      subdirectories

    - Operations take destinations **relative** to `BASE_PATH`, and
      `get_relative_path` converts an absolute path back to that format

warning: Modal Paths
    - `Modal` jobs only accept paths **relative** to `HOST_MEDIA_PATH` (see
      `modal_processing.app`), so `get_relative_path` is what should be handed
      to a job, never an absolute path
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path

import aiofiles
from fastapi import Request
from tqdm.auto import tqdm

from ..exceptions import InvalidMediaPathError, StorageError, UploadError
from ..paths import HOST_MEDIA_PATH

LOGGER = logging.getLogger(__name__)

BASE_PATH: Path = HOST_MEDIA_PATH
TEMP_PATH: Path = BASE_PATH / "temp"
PROFILES_PATH: Path = BASE_PATH / "profiles"


async def save_upload_file(
    request: Request,
    output_path: str | os.PathLike[str],
    tqdm_description: str | None = None,
) -> Path:
    """
    Saves a `FastAPI.Request.stream` to the file system by reading and writing
    the streamed chunks to `output_path` while logging the progress to a `TQDM`
    progress bar with `tqdm_description` as its message

    Args:
        request (Request): The `FastAPI.Request` object
        output_path (str | os.PathLike[str]): File path in which to save the
            stream
        tqdm_description (str | None): Optional description for the `TQDM`
            progress bar. When `None`, defaults to
            `f"Saving File To {output_path}"`

    Returns:
        `output_path`, if the file was written successfully

    Raises:
        UploadError: If the upload fails for any reason
    """

    output = Path(output_path).resolve()

    if tqdm_description is None:
        tqdm_description = f"Saving File To {output}"

    try:
        total_content = 0

        with tqdm(unit="B", unit_scale=True, desc=tqdm_description) as p:
            async with aiofiles.open(output, "wb+") as f:
                async for chunk in request.stream():
                    await f.write(chunk)
                    p.update(len(chunk))
                    total_content += len(chunk)

        LOGGER.info(f"Saved {total_content} Bytes To {output}")

    except Exception as e:
        # Clean Up Partially Created File
        output.unlink(missing_ok=True)
        raise UploadError(
            f"Failed to save uploaded content to {output} : {e}"
        ) from e

    return output


def init_storage() -> None:
    """
    Creates the media directory tree (`base`, `temp`, `profiles`) if missing

    Meant to be called once on application startup so module import stays free
    of filesystem side effects
    """
    for path in (BASE_PATH, TEMP_PATH, PROFILES_PATH):
        path.mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Media Storage Ensured At '{BASE_PATH}'")


def get_temp_dir(name: str) -> Path:
    """
    Creates and returns a named directory inside `TEMP_PATH`

    Args:
        name (str): Name of the temporary directory

    Returns:
        The absolute path to the created temporary directory
    """
    temp_dir = TEMP_PATH / name
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_profile_dir(profile_id: str, subfolder: str) -> Path:
    """
    Creates and returns a profile-specific subdirectory

    Args:
        profile_id (str): ID of the profile
        subfolder (str): Subfolder within the profile's directory

    Returns:
        The absolute path to the profile-specific subdirectory
    """
    profile_dir = PROFILES_PATH / profile_id / subfolder
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


def get_relative_path(full_path: str | os.PathLike[str]) -> Path:
    """
    Converts an absolute path into one relative to the media directory

    This relative form is what `Modal` jobs expect, since `HOST_MEDIA_PATH` is
    mounted into the container

    Args:
        full_path (str | os.PathLike[str]): Absolute path inside the media
            directory

    Returns:
        The path relative to `BASE_PATH`

    Raises:
        InvalidMediaPathError: If `full_path` is not inside the media directory
    """
    try:
        return Path(full_path).resolve().relative_to(BASE_PATH.resolve())
    except ValueError as e:
        raise InvalidMediaPathError(
            f"Path '{full_path}' is outside the media directory"
        ) from e


async def move_file(
    src: str | os.PathLike[str],
    dest_relative: str | os.PathLike[str],
) -> Path:
    """
    Moves a file to a destination relative to the media directory

    Args:
        src (str | os.PathLike[str]): Absolute source path of the file to move
        dest_relative (str | os.PathLike[str]): Destination path, relative to
            the media directory

    Returns:
        The absolute path to the moved file

    Raises:
        StorageError: If the file cannot be moved
    """
    dest_path = BASE_PATH / dest_relative
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.move, str(src), str(dest_path))
    except OSError as e:
        raise StorageError(
            f"Failed to move '{src}' to '{dest_path}' : {e}"
        ) from e
    LOGGER.info(f"Moved '{src}' -> '{dest_path}'")
    return dest_path


async def copy_file(
    src: str | os.PathLike[str],
    dest_relative: str | os.PathLike[str],
) -> Path:
    """
    Copies a file to a destination relative to the media directory

    Args:
        src (str | os.PathLike[str]): Absolute source path of the file to copy
        dest_relative (str | os.PathLike[str]): Destination path, relative to
            the media directory

    Returns:
        The absolute path to the new file

    Raises:
        StorageError: If the file cannot be copied
    """
    dest_path = BASE_PATH / dest_relative
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.copy, str(src), str(dest_path))
    except OSError as e:
        raise StorageError(
            f"Failed to copy '{src}' to '{dest_path}' : {e}"
        ) from e
    LOGGER.info(f"Copied '{src}' -> '{dest_path}'")
    return dest_path


async def delete_file(
    file_path_relative: str | os.PathLike[str],
    check: bool = False,
) -> None:
    """
    Deletes a single file located relative to the media directory

    Args:
        file_path_relative (str | os.PathLike[str]): Path of the file to
            delete, relative to the media directory
        check (bool): When `True`, raise on failure. Otherwise log and skip

    Raises:
        StorageError: If the file cannot be deleted and `check` is `True`
    """
    path = BASE_PATH / file_path_relative
    if path.exists() and path.is_file():
        try:
            await asyncio.to_thread(path.unlink, missing_ok=not check)
            LOGGER.info(f"Deleted file: '{path}'")
        except OSError as e:
            if check:
                raise StorageError(
                    f"Failed to delete file '{path}' : {e}"
                ) from e
            LOGGER.error(f"Error Deleting File '{path}' : '{e}'")


async def delete_dir(dir_path_relative: str | os.PathLike[str]) -> None:
    """
    Deletes a directory located relative to the media directory

    Args:
        dir_path_relative (str | os.PathLike[str]): Path of the directory to
            delete, relative to the media directory

    Raises:
        StorageError: If the directory cannot be deleted
    """
    path = BASE_PATH / dir_path_relative
    if path.exists() and path.is_dir():
        try:
            await asyncio.to_thread(shutil.rmtree, str(path))
            LOGGER.info(f"Deleted directory: '{path}'")
        except OSError as e:
            raise StorageError(
                f"Failed to delete directory '{path}' : {e}"
            ) from e


async def write_file(
    file_path_relative: str | os.PathLike[str],
    content: str,
) -> Path:
    """
    Writes text content to a file relative to the media directory, creating
    parent directories as needed

    Args:
        file_path_relative (str | os.PathLike[str]): Path of the file to write,
            relative to the media directory
        content (str): Text content to append to the file

    Returns:
        The absolute path to the written file

    Raises:
        StorageError: If the file cannot be written
    """
    path = BASE_PATH / file_path_relative
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "a+", encoding="utf-8") as f:
            await f.write(content)
    except OSError as e:
        raise StorageError(f"Failed To Write File '{path}' : {e}") from e
    return path


async def clean_temp(check: bool = False) -> None:
    """
    Deletes everything in the `temp` directory and recreates it

    Args:
        check (bool): When `True`, raise on failure. Otherwise log and skip

    Raises:
        StorageError: If the directory cannot be cleared and `check` is `True`
    """
    try:
        await delete_dir("temp")
    except StorageError:
        if check:
            raise
        LOGGER.error(f"Error clearing temp directory '{TEMP_PATH}'")
    TEMP_PATH.mkdir(parents=True, exist_ok=True)
