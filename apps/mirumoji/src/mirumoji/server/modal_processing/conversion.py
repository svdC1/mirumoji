"""
Defines `Modal` GPU jobs for `NVENC` video conversion
"""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any


def video_conversion_job(
    rel_video_fp: str | os.PathLike[str],
    to_mp4_kwargs: dict[str, Any] | None = None,
) -> Generator[bytes, None, None]:
    """
    Convert `video_fp` to MP4 using NVENC and stream the content as bytes

    Args:
        rel_video_fp (str | Path): Path to the video relative to
            `HOST_MEDIA_PATH`
        to_mp4_kwargs (dict | None): Additional arguments for
            `mirumoji.server.audio.to_mp4`

    Yields:
        The converted video chunks

    Raises:
        FFmpegError: If any of the FFMPEG commands have returned a non-zero
            exit code
        ValueError: If input_path doesn't exist or is not a file, or if an
            invalid resolution is provided
        MissingFFmpegError: If the FFMPEG executable couldn't be located
        MissingFFprobeError: If the FFROBE executable couldn't be located
        RuntimeError: If conversion produces no output
    """
    import logging

    from mirumoji.paths import CONTAINER_MEDIA_DIR
    from mirumoji.server.processing.audio import get_ffmpeg_path, to_mp4

    # Configure Container Logging
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{levelname}-{name}-{message}",
    )
    logger = logging.getLogger(__name__)
    logger.info(f"'video_conversion_job' Started For Video: '{rel_video_fp}'")

    # Create Temp For Storage
    tmp_p = Path.cwd() / "tmp"
    tmp_p.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using Temporary Directory For Video Conversion: '{tmp_p}'")

    # The path arrives relative to the mounted host media dir
    # (CONTAINER_MEDIA_DIR), so resolve against it to reach the file
    input_local = Path(CONTAINER_MEDIA_DIR) / rel_video_fp
    output_local = tmp_p / f"{input_local.stem}_converted.mp4"

    logger.info(
        f"Converting '{input_local}' to '{output_local}' using `NVENC`"
        f"with `to_mp4_kwargs` : {to_mp4_kwargs}"
    )

    # Get Container FFMPEG Path
    ffmpeg_path = get_ffmpeg_path()

    to_mp4_kwargs = to_mp4_kwargs or {}

    to_mp4_kwargs.update(
        ffmpeg_path=ffmpeg_path["ffmpeg"],
        input_path=input_local,
        output_path=output_local,
        use_nvenc=True,
    )
    result_p = to_mp4(**to_mp4_kwargs)

    if result_p and result_p.exists() and result_p.stat().st_size > 0:
        logger.info(f"Successfully Converted Video To: '{result_p}'")
        with open(result_p, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
        logger.info(f"Finished Streaming Video Bytes For: '{result_p}'")
    else:
        raise RuntimeError(
            f"Video Conversion Failed Or Produced An Empty File "
            f"For: '{input_local}'",
        )
