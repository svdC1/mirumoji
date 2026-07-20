"""
Defines helper functions to perform asynchronous file operations within the
`HOST_MEDIA_PATH` directory

abstract: Paths
    - `BASE_PATH` is the media root (`HOST_MEDIA_PATH`)

    - `TEMP_PATH` and `PROFILES_PATH` are its `temp` and `profiles`
      subdirectories

    - Operations take destinations **relative** to `BASE_PATH`, and
      `get_relative_path` converts an absolute path back to that format

info: Modal Paths
    - When using the `modal` transcription backend, the server uploads input
      files to (and downloads processed files from) an ephemeral per-job
      volume shared between it and the `Modal` container running the job
      (See `modal_processing.worker`)

    - Both the server and the container pass the in-volume paths in which
      they've stored files so that the server's media handling
      doesn't depend on the container sharing its file system layout

    - The media-relative path from `get_relative_path` is only used as the
      path in which the server stores files inside the modal volume to maintain
      consistency
"""

import asyncio
import contextlib
import logging
import os
import shutil
import uuid
from collections.abc import Iterator
from pathlib import Path

import aiofiles
from fastapi import Request, UploadFile
from starlette.requests import ClientDisconnect

from ..exceptions import InvalidMediaPathError, StorageError, UploadError
from ..paths import HOST_MEDIA_PATH
from .progress import transfer_bar

LOGGER = logging.getLogger(__name__)

BASE_PATH: Path = HOST_MEDIA_PATH
TEMP_PATH: Path = BASE_PATH / "temp"
PROFILES_PATH: Path = BASE_PATH / "profiles"

PARTIAL_SUFFIX: str = ".mirumoji-partial"
"""
Reserved marker naming a media file that is still being written

Writes land on a uniquely named `<stem>.<token>.mirumoji-partial<ext>` sibling
and are atomically renamed into place, so a reader never observes a partially
written file and two concurrent writes never share a temporary
"""


def partial_path(path: Path) -> Path:
    """
    Builds a unique temporary sibling path for an atomic write of `path`

    The random token keeps two concurrent writes to the same destination from
    sharing a temporary file, and the reserved marker keeps the Modal-host
    volume syncer from mirroring it

    info: The Marker Sits Before The Extension
        - `FFMPEG` picks its muxer from the output's extension and takes no
          format flag here, so the temporary has to keep the real one

        - Appending the marker would leave `ffmpeg` unable to infer a container

    Args:
        path (Path): The final destination path

    Returns:
        A unique `<stem>.<token>.mirumoji-partial<ext>` sibling of `path`
    """
    token = f".{uuid.uuid4().hex}{PARTIAL_SUFFIX}"
    return path.with_name(f"{path.stem}{token}{path.suffix}")


@contextlib.contextmanager
def atomic_output(path: str | os.PathLike[str]) -> Iterator[Path]:
    """
    Yields a temporary sibling to write to, renamed into `path` on success

    info: Producers That Write Their Own Output
        The helpers in this module stream their own bytes, so they build the
        temporary themselves. `FFMPEG` and `genanki` instead take a
        destination path and write it over many seconds

    Args:
        path (str | os.PathLike[str]): The final destination path

    Yields:
        The temporary sibling to write to

    Raises:
        StorageError: If the finished output cannot be renamed into place
    """
    final = Path(path)
    final.parent.mkdir(parents=True, exist_ok=True)
    partial = partial_path(final)
    try:
        yield partial
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    try:
        os.replace(partial, final)
    except OSError as e:
        partial.unlink(missing_ok=True)
        raise StorageError(f"Failed To Finalise Output '{final}' : {e}") from e


async def save_upload_file(
    request: Request,
    output_path: str | os.PathLike[str],
    description: str | None = None,
) -> Path:
    """
    Saves a `FastAPI.Request.stream` to the file system by reading and writing
    the streamed chunks to `output_path` while reporting the progress on a
    themed transfer bar with `description` as its label

    Args:
        request (Request): The `FastAPI.Request` object
        output_path (str | os.PathLike[str]): File path in which to save the
            stream
        description (str | None): Optional label for the progress bar. When
            `None`, defaults to `f"Saving File To {output_path}"`

    Returns:
        `output_path`, if the file was written successfully

    Raises:
        ClientDisconnect: If the client cancelled the upload
        UploadError: If the upload fails for any reason
    """

    output = Path(output_path).resolve()
    partial = partial_path(output)

    if description is None:
        description = f"Saving File To {output}"

    try:
        total_content = 0

        output.parent.mkdir(parents=True, exist_ok=True)
        with transfer_bar(description) as advance:
            async with aiofiles.open(partial, "wb+") as f:
                async for chunk in request.stream():
                    await f.write(chunk)
                    advance(len(chunk))
                    total_content += len(chunk)
        # Atomic Rename
        await asyncio.to_thread(os.replace, partial, output)

        LOGGER.info(f"Saved {total_content} Bytes To {output}")

    except ClientDisconnect:
        # The client cancelled the upload, which is an ordinary outcome rather
        # than a failure. The temporary is dropped and nothing is renamed into
        # place, so the caller never records a half-uploaded file
        partial.unlink(missing_ok=True)
        LOGGER.info(f"Upload To {output} Cancelled By The Client")
        raise

    except Exception as e:
        # Clean Up Partially Written File
        partial.unlink(missing_ok=True)
        raise UploadError(
            f"Failed to save uploaded content to {output} : {e}"
        ) from e

    return output


async def save_upload_object(
    upload: UploadFile,
    output_path: str | os.PathLike[str],
) -> Path:
    """
    Saves a `FastAPI.UploadFile` (a multipart file part) to the file system by
    streaming it to `output_path` in chunks

    info: Difference From `save_upload_file`
        `save_upload_file` is used for large raw-body streamed uploads while
        `save_upload_object` is used for multipart uploads (`File(...)`) where
        the file travels alongside form metadata

    Args:
        upload (UploadFile): The multipart file part to save
        output_path (str | os.PathLike[str]): File path in which to save it

    Returns:
        `output_path`, if the file was written successfully

    Raises:
        UploadError: If the upload fails for any reason
    """
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = partial_path(output)
    chunk_size = 1024 * 1024

    try:
        async with aiofiles.open(partial, "wb") as f:
            while chunk := await upload.read(chunk_size):
                await f.write(chunk)
        # Atomic Rename
        await asyncio.to_thread(os.replace, partial, output)

    except Exception as e:
        # Clean Up Partially Written File
        partial.unlink(missing_ok=True)
        raise UploadError(
            f"Failed to save uploaded object to {output} : {e}"
        ) from e

    LOGGER.info(f"Saved Upload Object To {output}")
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

    abstract: Modal File Transfer
        - This relative form is used as the file's path within the per-job
          ephemeral `Modal` volume when the server uploads it

        - This is done so that the in-volume layout of `media_files` mirrors
          the `HOST_MEDIA_PATH` directory

        - See `modal_processing.worker` for more information on this

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
            LOGGER.info(f"Deleted File '{path}'")
        except OSError as e:
            if check:
                raise StorageError(
                    f"Failed to delete file '{path}' : {e}"
                ) from e
            LOGGER.error(f"Error Deleting File '{path}': '{e}'")


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
            LOGGER.info(f"Deleted Directory '{path}'")
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

    info: Atomic Overwrite
        The content is written to a temporary sibling and then atomically
        renamed into place, so it replaces any existing file in one step and a
        reader (or the Modal-host volume syncer) never sees a half-written file

    Args:
        file_path_relative (str | os.PathLike[str]): Path of the file to write,
            relative to the media directory
        content (str): Text content to write to the file

    Returns:
        The absolute path to the written file

    Raises:
        StorageError: If the file cannot be written
    """
    path = BASE_PATH / file_path_relative
    partial = partial_path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(partial, "w", encoding="utf-8") as f:
            await f.write(content)
        await asyncio.to_thread(os.replace, partial, path)
    except OSError as e:
        partial.unlink(missing_ok=True)
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
        LOGGER.error(f"Error Clearing Temp Directory '{TEMP_PATH}'")
    TEMP_PATH.mkdir(parents=True, exist_ok=True)
