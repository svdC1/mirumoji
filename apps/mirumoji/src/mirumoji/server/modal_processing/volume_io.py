"""
Streaming helpers for moving files in and out of a transient `Modal` volume

tip: Additional Information
    - Both the server and the `Modal` container runtime use the helpers
      defined here to copy files into or out of a transient per-job ephemeral
      `Modal Volume`

    - This volume is what allows the container to access local files for
      processing and send back processed files for the server to save locally

    - Each transfer is streamed in chunks and reported through a `tqdm`
      progress bar, so neither side ever loads a whole multi-GB media file
      into memory

    - See the `modal_processing.app` module for more information on this
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, cast

from tqdm.auto import tqdm

from ...exceptions import ModalVolumeError

if TYPE_CHECKING:
    import modal

LOGGER = logging.getLogger(__name__)


def upload_to_volume(
    volume: modal.Volume,
    local_path: str | os.PathLike[str],
    vol_fp: str,
    *,
    desc: str | None = None,
) -> None:
    """
    Stream a local file into a `Modal.Volume` under the `vol_fp` key

    The file is read from disk in chunks (never loaded whole into memory) while
    a `tqdm` bar reports the progress

    Args:
        volume (modal.Volume): The modal volume to upload into
        local_path (str | os.PathLike[str]): The local file to upload
        vol_fp (str): The destination path inside the volume
        desc (str | None): Optional `tqdm` description. Defaults to
            `f"Uploading {name} To Volume"`

    Raises:
        ModalVolumeError: If the source is missing or the upload fails
    """
    src = Path(local_path)
    if not src.is_file():
        raise ModalVolumeError(
            f"Cannot Upload '{src}' To Volume: Not A File",
        )

    size = src.stat().st_size
    desc = desc or f"Uploading {src.name} To Volume"
    LOGGER.info(f"Uploading '{src}' ({size} Bytes) To Volume Path '{vol_fp}'")

    try:
        with (
            src.open("rb") as raw,
            tqdm.wrapattr(
                raw,
                "read",
                total=size,
                desc=desc,
                unit="B",
                unit_scale=True,
            ) as wrapped,
            volume.batch_upload() as batch,
        ):
            # `tqdm.wrapattr` returns a transparent read-counting proxy that
            # delegates seek/tell/etc... to the real file, so it behaves like a
            # binary stream for the chunked upload
            batch.put_file(cast(BinaryIO, wrapped), vol_fp)
    except Exception as e:
        raise ModalVolumeError(
            f"Failed To Upload '{src}' To Volume Path '{vol_fp}': {e}",
        ) from e

    LOGGER.info(f"Uploaded '{src}' To Volume Path '{vol_fp}'")


def download_from_volume(
    volume: modal.Volume,
    vol_fp: str,
    local_path: str | os.PathLike[str],
    *,
    desc: str | None = None,
) -> Path:
    """
    Copies the `vol_fp` file out of a `Modal.Volume` to `local_path`

    The file is read from the volume in chunks (never loaded whole into memory)
    while a `tqdm` bar reports the progress. The destination's parent directory
    is created if missing, and a partially-written file is removed on failure

    Args:
        volume (modal.Volume): The volume to read from
        vol_fp (str): The file's path inside the volume
        local_path (str | os.PathLike[str]): The local destination file
        desc (str | None): Optional `tqdm` description. Defaults to
            `f"Downloading {vol_fp} From Volume"`

    Returns:
        The local destination path

    Raises:
        ModalVolumeError: If the download fails
    """
    dest = Path(local_path)
    desc = desc or f"Downloading {vol_fp} From Volume"
    LOGGER.info(f"Downloading Volume Path '{vol_fp}' To '{dest}'")

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with (
            tqdm(unit="B", unit_scale=True, desc=desc) as bar,
            dest.open("wb") as f,
        ):
            for chunk in volume.read_file(vol_fp):
                f.write(chunk)
                bar.update(len(chunk))
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise ModalVolumeError(
            f"Failed To Download Volume Path '{vol_fp}' To '{dest}': {e}",
        ) from e

    LOGGER.info(f"Downloaded Volume Path '{vol_fp}' To '{dest}'")
    return dest
