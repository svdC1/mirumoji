"""
Defines functions that run `FFMPEG` in a subprocess to perform various
media operations
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

from ...exceptions import FFmpegError, MissingFFmpegError, MissingFFprobeError

LOGGER = logging.getLogger("mirumoji")


def get_ffmpeg_path() -> dict[str, str]:
    """
    Uses `shutil.which` to find the absolute path to the system's `FFMPEG` and
    `FFPROBE` executables, raising an exception when either one of them
    can't be found

    Raises:
        MissingFFmpegError: If the `FFMPEG` executable couldn't be located
        MissingFFprobeError: If the `FFROBE` executable couldn't be located

    Returns:
        dictionary mapping `ffmpeg` and `ffprobe` to their respective paths
    """

    # Search for FFMPEG and FFPROBE with shutil
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg:
        raise MissingFFmpegError(
            "The `FFMPEG` executable couldn't be located. "
            "Mirumoji requires `FFMPEG` to be installed in order "
            "to perform media operations."
        )
    if not ffprobe:
        raise MissingFFprobeError(
            "The `FFPROBE` executable couldn't be located. "
            "Mirumoji requires `FFMPROBE` to be installed in order "
            "to perform media operations."
        )

    return {"ffmpeg": ffmpeg, "ffprobe": ffprobe}


def run_command(
    command: list[str],
    check: bool = True,
    cwd: str | os.PathLike[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Wraps `subprocess.run` in order to log errors and results

    Args:
        command (list[str]): The CMD list of the command to be executed
        check (bool): When `True`, raises an exception on subprocess
            error. Defaults to True
        cwd (str | os.PathLike[str], None): Directory from which the command
            will be executed. Defaults to `None` (the currently running python
            process' directory)

    Raises:
        subprocess.CalledProcessError: When `check=True` and the process
            returns a non-zero exit code

    Returns:
        A `subprocess.CompletedProcess` object
    """

    LOGGER.debug(f"Audio Processing - Running Command: {' '.join(command)}")

    try:
        # Redirect `stdout` and `stderr` to `subprocess.PIPE`
        result = subprocess.run(
            command,
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=cwd,
        )

        # Warn error if check=False
        if result.returncode != 0:
            LOGGER.warning(
                f"Audio Processing - Command Failure Suppressed - "
                f"Exit Code: {result.returncode}"
            )

        LOGGER.debug(f"Audio Processing - STDOUT: '{result.stdout}'")
        LOGGER.debug(f"Audio Processing - STDERR: '{result.stderr}'")

        return result

    except subprocess.CalledProcessError as e:
        LOGGER.error(
            f"Audio Processing - Command Failed - "
            f"Audio Processing - Exit Code: {e.returncode}"
        )
        LOGGER.error(f"Audio Processing - STDOUT: '{e.stdout}'")
        LOGGER.error(f"Audio Processing - STDERR: '{e.stderr}'")
        raise


def to_wav(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
) -> Path:
    """
    Converts a file to `.wav` format using FFMPEG

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str | os.PathLike[str]): Path to the file to convert
        output_path (str | os.PathLike[str]): Output file path

    Raises:
        FFmpegError: If the FFMPEG command returned a non-zero exit code
        ValueError: If `input_path` doesn't exist or is not a file

    Returns:
        The output path of the converted file
    """
    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"Audio Processing - WAV conversion failed - {input.as_posix()} is"
            f" not a valid file"
        )

    output = Path(output_path).resolve()

    # Use POSIX path style for ffmpeg
    command = [
        ffmpeg_path,
        "-y",  # Overwrite output file without asking
        "-i",
        input.as_posix(),
        "-ar",
        "44100",
        "-ac",
        "2",
        "-f",
        "wav",
        output.as_posix(),
    ]

    try:
        run_command(command)
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"Audio Processing - Failed to convert '{input.as_posix()}' to WAV"
        ) from e

    LOGGER.info(
        f"Audio Processing - Converted '{input.as_posix()}' "
        f"to WAV File At '{output.as_posix()}'"
    )
    return output


def extract_audio(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
) -> Path:
    """
    Extracts a WAV audio file from a video container using `FFMPEG`

    If input file is already an audio file, returns the unchanged input file
    path

    info: File Extensions
        This function checks the `input_path` file's extension to determine if
        it's an audio file. The following extensions are considered to be
        audio files

        - `.wav`
        - `.mp3`
        - `.m4a`
        - `.flac`
        - `.aac`

        If the file at `input_path` has any of these extensions, its path will
        be returned unchanged

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str | os.PathLike[str]): Path to the video file
        output_path (str | os.PathLike[str]): Output path

    Raises:
        FFmpegError: If the FFMPEG command returned a non-zero exit code
        ValueError: If `input_path` doesn't exist or is not a file

    Returns:
        The output path of the converted file, or `input_path` if it
            is already an audio file
    """

    ext = Path(input_path).resolve().suffix

    if ext in {".wav", ".mp3", ".m4a", ".flac", ".aac"}:
        LOGGER.info(
            f"Audio Processing - Input {input_path} is already an "
            f"audio file ({ext}), no extraction needed"
        )
        return Path(input_path)

    LOGGER.info(f"Audio Processing - Extracting audio from '{input_path}'")

    output = Path(output_path).resolve()
    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"Audio Processing - Audio Extraction Failed -"
            f"{input.as_posix()} is not a valid file"
        )

    cmd = [
        ffmpeg_path,
        "-y",
        "-i",
        input.as_posix(),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        output.as_posix(),
    ]
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"Audio Processing - Failed to extract WAV audio from "
            f"'{input.as_posix()}'"
        ) from e
    LOGGER.info(
        f"Audio Processing - Extracted audio from '{input.as_posix()}' to WAV "
        f"file at '{output.as_posix()}'"
    )
    return output


def filter_audio(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    highpass: int = 300,
    lowpass: int = 3400,
) -> Path:
    """
    Applies a band-pass and loudness normalization to a media file,
    extracting a 16 kHz mono WAV audio file from it using `FFMPEG`

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str): Path to the audio / video file to use
        output_path (str): Path in which to save the resulting WAV file
        highpass (int): Cut everything below this frequency (Hz)
        lowpass (int): Cut everything above this frequency (Hz)

    Raises:
        FFmpegError: If the FFMPEG command returned a non-zero exit code
        ValueError: If `input_path` doesn't exist or is not a file

    Returns:
        The path to the extracted 16 kHz mono WAV audio file
    """

    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"Audio Processing - Audio Filtering Failed -"
            f"{input.as_posix()} is not a valid file"
        )

    output = Path(output_path).resolve()

    cmd = [
        ffmpeg_path,
        "-y",
        "-i",
        input.as_posix(),
        "-vn",
        "-af",
        f"highpass=f={highpass}, lowpass=f={lowpass}, loudnorm",
        "-ac",
        "1",
        "-ar",
        "16000",
        output.as_posix(),
    ]

    LOGGER.info(
        f"Audio Processing - Applying Band-Pass ({highpass} - {lowpass}) and "
        f"loudness normalization to {input.as_posix()}"
    )
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"Audio Processing - Failed to filter '{input.as_posix()}'"
        ) from e

    LOGGER.info(
        f"Audio Processing - Filtered '{input.as_posix()}' t"
        f"WAV file at '{output.as_posix()}'"
    )
    return output


def to_mp4(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str] | None = None,
    resolution: str = "1280x720",
    target_bitrate: str = "2500k",
    use_nvenc: bool = False,
) -> Path:
    """
    Converts any video supported by `FFMPEG` to an MP4 file using H.264 + AAC
    encoding

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str | os.PathLike[str]): Source file
            (any container/codec supported by FFMPEG)
        output_path (str | os.PathLike[str] | None): Path in which to save the
            MP4 file. When set to `None`, the file is saved to `input_path`
            with a `.mp4` suffix
        resolution (str): Target canvas `WxH`. Aspect is preserved.
            Defaults to `1280x720`
        target_bitrate (str):  Target video bitrate. Default to `2500k`
        use_nvenc (bool): When `True`, attempts to use `NVIDIA NVENC` for
            faster encoding, falling back `libx264 CPU` in case of failures

    Raises:
        FFmpegError: If any of the FFMPEG commands have returned a non-zero
            exit code
        ValueError: If `input_path` doesn't exist or is not a file, or if an
            invalid resolution is provided

    Returns:
        Path to the resulting MP4
    """

    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"Audio Processing - MP4 Conversion Failed -"
            f"{input.as_posix()} is not a valid file"
        )

    output = Path(output_path or input.with_suffix(".mp4")).resolve()

    # Normalise resolution
    try:
        w, h = map(int, resolution.lower().split("x"))
    except ValueError as e:
        raise ValueError(
            f"Resolution must be 'WxH', got '{resolution}'"
        ) from e

    # --- FFMPEG Parameters ---

    # Scale To Fit +  Pad To Canvas (Center)
    vf = (
        f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,"
        f"pad=w={w}:h={h}:x=(ow-iw)/2:y=(oh-ih)/2:color=black"
    )

    # Set Longer Analyze Duration And Probesize For Complex Video Files
    input_args = [
        "-analyzeduration",
        "20M",  # 20 Million Microseconds = 20 seconds
        "-probesize",
        "50M",  # 50 Megabytes
    ]

    # --- CPU Parameters ---

    cpu_enc = [
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-b:v",
        target_bitrate,
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
    ]

    cpu_cmd = [
        ffmpeg_path,
        "-y",
        *input_args,
        "-i",
        input.as_posix(),
        "-vf",
        vf,
        *cpu_enc,
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output.as_posix(),
    ]

    # --- NVENC Parameters ---

    nvidia_enc = [
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p6",
        "-rc:v",
        "vbr",
        "-b:v",
        target_bitrate,
        "-pix_fmt",
        "yuv420p",
    ]

    nvidia_cmd = [
        ffmpeg_path,
        "-y",
        *input_args,
        "-i",
        input.as_posix(),
        "-vf",
        vf,
        *nvidia_enc,
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output.as_posix(),
    ]

    # --- Determine Encoder ---

    cmd = nvidia_cmd if use_nvenc else cpu_cmd

    LOGGER.info(
        f"Audio Processing - Converting {input.as_posix()} to MP4 with"
        f"use_nvenc='{use_nvenc}'"
    )

    result = run_command(cmd, check=False)

    if result.returncode != 0 and use_nvenc:
        LOGGER.warning(
            f"Audio Processing - NVENC MP4 Conversion Failed For "
            f"{input.as_posix()} - Retrying with libx264"
        )

        # Retry with `libx264` in case of NVENC error
        result = run_command(cpu_cmd)

    try:
        result.check_returncode()
        LOGGER.info(
            f"Audio Processing - Converted {input.as_posix()} to MP4 file at "
            f"{output.as_posix()}"
        )
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"Audio Processing - CPU MP4 conversion for"
            f"{input.as_posix()} failed"
        ) from e

    return output


def to_webm(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str] | None = None,
    resolution: str = "1280x720",
    target_bitrate: str = "2500k",
    use_nvenc: bool = False,
) -> Path:
    """
    Converts any video supported by `FFMPEG` to an WebM file using VP9 + Opus
    encoding

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str | os.PathLike[str]): Source file
            (any container/codec supported by FFMPEG)
        output_path (str | os.PathLike[str] | None): Path in which to save the
            WebM file. When set to `None`, the file is saved to `input_path
            with a `.webm` suffix
        resolution (str): Target canvas `WxH`. Aspect is preserved.
            Defaults to `1280x720`
        target_bitrate (str):  Target video bitrate. Default to `2500k`
        use_nvenc (bool): When `True`, attempts to use `NVIDIA NVENC` for
            faster encoding, falling back `libvpx-vp9 CPU` in case of failures

    Raises:
        FFmpegError: If any of the FFMPEG commands have returned a non-zero
            exit code
        ValueError: If `input_path` doesn't exist or is not a file, or if an
            invalid resolution is provided

    Returns:
        Path to the resulting WebM
    """

    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"Audio Processing - WebM Conversion Failed -"
            f"{input.as_posix()} is not a valid file"
        )

    output = Path(output_path or input.with_suffix(".webm")).resolve()

    # Normalise Resolution
    try:
        w, h = map(int, resolution.lower().split("x"))
    except ValueError as e:
        raise ValueError(
            f"Resolution must be 'WxH', got '{resolution}'"
        ) from e

    # --- FFMPEG Parameters ---

    # Scale To Fit +  Pad To Canvas (Center)
    vf = (
        f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,"
        f"pad=w={w}:h={h}:x=(ow-iw)/2:y=(oh-ih)/2:color=black"
    )

    # Set Longer Analyze Duration And Probesize For Complex Video Files
    input_args = [
        "-analyzeduration",
        "20M",  # 20 Million Microseconds = 20 seconds
        "-probesize",
        "50M",  # 50 Megabytes
    ]

    # --- CPU Parameters ---
    cpu_enc = [
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        target_bitrate,
        "-deadline",
        "good",
    ]

    cpu_cmd = [
        ffmpeg_path,
        "-y",
        *input_args,
        "-i",
        input.as_posix(),
        "-vf",
        vf,
        *cpu_enc,
        "-c:a",
        "libopus",
        "-b:a",
        "128k",
        output.as_posix(),
    ]

    # --- NVENC Parameters ---

    nvidia_enc = [
        "-c:v",
        "vp9_nvenc",
        "-rc:v",
        "vbr",
        "-b:v",
        target_bitrate,
    ]

    nvidia_cmd = [
        ffmpeg_path,
        "-y",
        *input_args,
        "-i",
        input.as_posix(),
        "-vf",
        vf,
        *nvidia_enc,
        "-c:a",
        "libopus",
        "-b:a",
        "128k",
        output.as_posix(),
    ]

    # --- Determine Encoder ---

    cmd = nvidia_cmd if use_nvenc else cpu_cmd

    LOGGER.info(
        f"Audio Processing - Converting {input.as_posix()} to WebM with"
        f"use_nvenc='{use_nvenc}'"
    )

    result = run_command(cmd, check=False)

    if result.returncode != 0 and use_nvenc:
        LOGGER.warning(
            f"Audio Processing - NVENC WebM Conversion Failed For "
            f"{input.as_posix()} - Retrying with libvpx-vp9"
        )

        # Retry with `libvpx-vp9` in case of NVENC error
        result = run_command(cpu_cmd)

    try:
        result.check_returncode()
        LOGGER.info(
            f"Audio Processing - Converted {input.as_posix()} to WebM file at "
            f"{output.as_posix()}"
        )
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"Audio Processing - CPU WebM conversion for"
            f"{input.as_posix()} failed"
        ) from e

    return output
