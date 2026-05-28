"""
This module provides helper functions for file operations and a class for
handling file operations within the media_files directory
"""

import asyncio
import logging
import shutil
from pathlib import Path

import aiofiles
from fastapi import Header, HTTPException, Request
from tqdm.auto import tqdm

from mirumoji.server.utils.constants import BASE_MEDIA_DIR, TEMP_DIR

LOGGER = logging.getLogger(__name__)


async def save_upload_file(
    request: Request,
    dest: Path,
    tqdm_description: str | None = None,
) -> None:
    """
    Saves a `FastAPI.Request.stream` by reading and writing streamed
    chunks to `dest` and displaying a `TQDM` progress bar in logging.

    Args:
      request (Request): FastAPI `Request` object.
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
            f"Failed to save uploaded streamto '{dest}'. Error: '{e}'",
        )
        # Clean up partially created file on error
        dest.unlink(missing_ok=True)
        raise


async def get_stream_file(
    request: Request,
    upload_id: str = Header(..., alias="X-Upload-ID"),
    file_name: str = Header(..., alias="X-File-Name"),
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
    temp_dir = TEMP_DIR / f"{upload_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / f"{file_name}"
    try:
        await save_upload_file(request, temp_file_path)
        return temp_file_path
    except Exception as e:
        HTTPException(status_code=400, detail=f"{e}")


class MediaFileHandler:
    """
    Handles file and path manipulations within the media_files directory.

    Attributes:
      project_root (Path): The root directory of the project.
      base_path (Path): The absolute local path to `media_files`.
      temp_path (Path): The absolute local path to 'media_files/temp'.
      profiles_path (Path): The absolute local path to 'media_files/profiles'
      modal_media_path (Path): The relative path to 'media_files' in Modal
    """

    def __init__(self) -> None:
        media_path = str(BASE_MEDIA_DIR)
        # File = system_path/root/utils/file_utils -> system_path/root/
        self.project_root = Path(__file__).resolve().parent.parent
        # system_path/root/media_files
        self.base_path = self.project_root / media_path
        # system_path/root/media_files/temp
        self.temp_path = self.base_path / "temp"
        # system_path/root/media_files/profiles
        self.profiles_path = self.base_path / "profiles"
        # root/media_files
        self.modal_media_path = Path(media_path)

        self.base_path.mkdir(exist_ok=True)
        self.temp_path.mkdir(exist_ok=True)
        self.profiles_path.mkdir(exist_ok=True)

    def get_temp_dir(self, name: str) -> Path:
        """
        Creates and returns a path to a named directory inside temp.

        Args:
          name (str): The name of the temporary directory.

        Returns:
          Path: The absolute path to the created temporary directory.
        """
        # system_local/root/media_files/temp/`name`
        temp_dir = self.temp_path / name
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    async def move_file(
        self,
        src: str | Path,
        dest_relative: str | Path,
    ) -> Path:
        """
        Moves a file from a source path to a destination relative to the media
        base.

        Args:
          src (Union[str, Path]): The absolute source path of the file to
                                  move.
          dest_relative (Union[str, Path]): The destination path, relative
                                            to the media directory.

        Returns:
          Path: The absolute path to the moved file.
        """
        # system_local/root/media_files/`dest_relative`
        dest_path = self.base_path / dest_relative
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.move, str(src), str(dest_path))
        LOGGER.info(f"Moved '{src}' -> '{dest_path}'")
        return dest_path

    async def copy_file(
        self,
        src: str | Path,
        dest_relative: str | Path,
    ) -> Path:
        """
        Copies a file to a destination relative to the media base.

        Args:
          src (Union[str, Path]): The absolute source path of the file to
                                  copy.
          dest_relative (Union[str, Path]): The destination path, relative
                                            to the media directory.

        Returns:
          Path: The absolute path to the new file.
        """
        # system_local/root/media_files/`dest_relative`
        dest_path = self.base_path / dest_relative
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.copy, str(src), str(dest_path))
        LOGGER.info(f"Copied '{src}' -> '{dest_path}'")
        return dest_path

    async def delete_file(
        self,
        file_path_relative: str | Path,
        check=False,
    ) -> None:
        """
        Deletes a single file located relative to the media base.

        Args:
          file_path_relative (Union[str, Path]): The path of the file to
                                                 delete, relative to the
                                                 media directory.
          check (bool, optional): If True, raise error on failure, otherwise
                                  skip. Defaults to False

        Raises:
          OSError: If the file cannot be deleted and `check=True`
        """
        # system_local/root/media_files/`file_path_relative`
        path = self.base_path / file_path_relative
        if path.exists() and path.is_file():
            try:
                missing_ok = not check
                await asyncio.to_thread(path.unlink, missing_ok=missing_ok)
                LOGGER.info(f"Deleted file: '{path}'")
            except OSError as e:
                if check:
                    raise
                else:
                    LOGGER.error(f"Error deleting file '{path}': '{e}'")

    async def delete_dir(self, dir_path_relative: str | Path) -> None:
        """
        Deletes a directory located relative to the media base.

        Args:
          dir_path_relative (Union[str, Path]): The path of the directory to
                                                delete, relative to the
                                                media directory.

        Raises:
          OSError: If the directory cannot be deleted.
        """
        # system_local/root/media_files/`dir_path_relative`
        path = self.base_path / dir_path_relative
        if path.exists() and path.is_dir():
            try:
                await asyncio.to_thread(shutil.rmtree, str(path))
                LOGGER.info(f"Deleted directory: '{path}'")
            except OSError as e:
                LOGGER.error(f"Error deleting directory '{path}': '{e}'")
                raise

    def get_profile_dir(self, profile_id: str, subfolder: str) -> Path:
        """
        Gets or creates a profile-specific subdirectory.

        Args:
          profile_id (str): The ID of the profile.
          subfolder (str): The name of the subfolder within the profile
                           directory.

        Returns:
          Path: The absolute path to the profile-specific subdirectory.
        """
        # system_local/root/media_files/profiles/`profile_id`/`subfolder`
        profile_dir = self.profiles_path / profile_id / subfolder
        profile_dir.mkdir(parents=True, exist_ok=True)
        return profile_dir

    def get_relative_path(self, full_path: str | Path) -> Path:
        """
        Resolves a path relative to the media directory.

        Args:
          full_path (Union[str, Path]): An absolute path to a file or
                                        directory.

        Returns:
          Path: The path relative to the media directory.
        """
        # full_path = system_local/root/media_files/some_folder/some_file ->
        # return = some_folder/some_file
        return Path(full_path).relative_to(self.base_path)

    def get_modal_path(self, local_path: str | Path) -> Path:
        """
        Converts an absolute local path to a Modal-compatible relative path.

        Args:
          local_path (Union[str, Path]): An absolute local path.

        Returns:
          Path: A path relative to the project root, suitable for Modal.
        """
        # full_path = system_local/root/media_files/some_folder/some_file ->
        # return = media_files/some_folder/some_file
        relative_path = self.get_relative_path(local_path)
        return self.modal_media_path / relative_path

    async def write_file(
        self,
        file_path_relative: str | Path,
        content: str,
    ) -> Path:
        """
        Writes text content to a file, creating directories if necessary.

        Args:
          file_path_relative (Union[str, Path]): The path of the file to write
                                                 to, relative to the media
                                                 directory.
          content (str): The string content to write to the file.

        Returns:
          Path: The absolute path to the written file.

        Raises:
          IOError: If there is an error writing the file.
        """
        path = self.base_path / file_path_relative
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with aiofiles.open(path, "a+", encoding="utf-8") as f:
                await f.write(content)
            return path
        except OSError as e:
            LOGGER.error(f"Error writing to file '{path}': '{e}'")
            raise

    async def clean_temp(self, check=False) -> None:
        """
        Tries to delete all files in temp folder and recreate it

        Args:
          check (bool, optional): If `True` raise errors if directory couldn't
                                  be deleted, otherwise skip. Defaults to False

        Raises:
          OSError: If `check=True` and there's an error deleting the directory
        """
        try:
            self.delete_dir("temp")
            self.temp_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            if check:
                raise
            else:
                LOGGER.error(f"Error deleting '{self.temp_path}': '{e}'")
