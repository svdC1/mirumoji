"""
Defines the `Modal` GPU job for video conversion
"""

from typing import Any


def video_conversion_job(
    vol_fp: str,
    vol_id: str,
    to_mp4_kwargs: dict[str, Any] | None = None,
) -> str:
    """
    Convert a video to MP4 inside a `Modal` GPU container

    info: Encoder
        The container probes `NVENC` and uses the on-device GPU pipeline only
        when an encoder is present, falling back to CPU `libx264` otherwise.
        The data center compute GPUs (`A100` / `H100` / `B200`) have no
        `NVENC`, so they convert on CPU

    info: File Transfer
        - The input video is read out of the per-job ephemeral volume into a
          container-local temp directory

        - The container converts the video and the resulting MP4 is
          written back into the same volume

        - The job returns the output key so that the local runtime can stream
          the result out and save it

        - The temp directory is removed once the job finishes

    Args:
        vol_fp (str): Path of the input video inside the per-job ephemeral
            volume
        vol_id (str): ID of the per-job ephemeral volume
        to_mp4_kwargs (dict | None): Additional arguments for
            `mirumoji.server.processing.audio.to_mp4`

    Returns:
        The Path of the converted MP4 inside the per-job ephemeral volume

    Raises:
        ModalVolumeError: If the input or output can't be transferred through
            the volume
        FFmpegError: If any of the FFMPEG commands return a non-zero exit code
        ValueError: If the input doesn't exist or an invalid resolution is
            provided
        MissingFFmpegError: If the FFMPEG executable couldn't be located
        MissingFFprobeError: If the FFPROBE executable couldn't be located
        RuntimeError: If conversion produces no output
    """
    import logging
    import shutil
    import tempfile
    from pathlib import Path, PurePosixPath

    import modal

    from mirumoji.log import setup_logging
    from mirumoji.server.config import nvenc_available
    from mirumoji.server.modal_processing.volume_io import (
        download_from_volume,
        upload_to_volume,
    )
    from mirumoji.server.processing.audio import get_ffmpeg_path, to_mp4

    # Configure Container Logging - stdout only, captured by Modal as job logs
    setup_logging(log_file=None, console=True)
    logger = logging.getLogger(__name__)

    vol = modal.Volume.from_id(vol_id)
    workdir = Path(tempfile.mkdtemp(prefix="mirumoji_convert_"))

    try:
        # Stream The Input Out Of The Volume Into Container-Local Storage
        local_in = workdir / Path(vol_fp).name
        download_from_volume(vol, vol_fp, local_in)

        # Probe NVENC inside the container, where the conversion runs. The data
        # center compute GPUs (A100 / H100 / B200) have NVDEC but no NVENC, so
        # this keeps the job on CPU there instead of attempting a doomed encode
        ffmpeg = get_ffmpeg_path()["ffmpeg"]
        use_gpu = nvenc_available(ffmpeg)

        local_out = workdir / f"{local_in.stem}_converted.mp4"
        logger.info(
            f"Converting '{local_in}' -> '{local_out}' "
            f"(use_gpu={use_gpu}, kwargs: {to_mp4_kwargs})"
        )

        kwargs = dict(to_mp4_kwargs or {})
        kwargs.update(
            ffmpeg_path=ffmpeg,
            input_path=local_in,
            output_path=local_out,
            use_gpu=use_gpu,
        )
        result_p = to_mp4(**kwargs)

        if not (
            result_p and result_p.exists() and result_p.stat().st_size > 0
        ):
            raise RuntimeError(
                f"Video Conversion Failed Or Produced An Empty File "
                f"For '{local_in}'",
            )

        # Write The Result Back Into The Volume Next To The Input Path
        out_vol_fp = str(PurePosixPath(vol_fp).with_name(local_out.name))
        upload_to_volume(vol, result_p, out_vol_fp)
        logger.info(f"Converted Video Written To Volume Path '{out_vol_fp}'")
        return out_vol_fp

    finally:
        shutil.rmtree(workdir, ignore_errors=True)
