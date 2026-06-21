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
from ..constants import CONVERSION_PRESETS, DEFAULT_CONVERSION_PRESET

LOGGER = logging.getLogger(__name__)


def _resolve_preset(preset: str) -> dict[str, tuple[str, str]]:
    """
    Looks up an encoder bundle by preset name

    Args:
        preset (str): One of `performance`, `balanced`, `quality`

    Raises:
        ValueError: If `preset` is not a known preset

    Returns:
        The per-encoder `(speed, quality)` bundle for the preset
    """
    try:
        return CONVERSION_PRESETS[preset]
    except KeyError as e:
        raise ValueError(
            f"Unknown conversion preset '{preset}'. "
            f"Expected one of: {', '.join(CONVERSION_PRESETS)}"
        ) from e


def _double_bitrate(bitrate: str) -> str:
    """
    Doubles a bitrate string for use as the VBV buffer size, preserving its
    unit suffix (e.g. `2500k` -> `5000k`)

    Args:
        bitrate (str): A bitrate like `2500k`, `4M`, or `2500000`

    Returns:
        The doubled bitrate string, or the input unchanged if it can't be
        parsed
    """
    text = bitrate.strip()
    digits = text.rstrip("kKmMgG")
    unit = text[len(digits) :]
    try:
        return f"{int(float(digits)) * 2}{unit}"
    except ValueError:
        return bitrate


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

    LOGGER.debug(f"Running Command: {' '.join(command)}")

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
                f"Command Failure Suppressed - Exit Code: {result.returncode}"
            )

        LOGGER.debug(f"STDOUT: '{result.stdout}'")
        LOGGER.debug(f"STDERR: '{result.stderr}'")

        return result

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Command Failed - Exit Code: {e.returncode}")
        LOGGER.error(f"STDOUT: '{e.stdout}'")
        LOGGER.error(f"STDERR: '{e.stderr}'")
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
            f"WAV conversion failed - {input.as_posix()} is not a valid file"
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
            f"Failed to convert '{input.as_posix()}' to WAV"
        ) from e

    LOGGER.info(
        f"Converted '{input.as_posix()}' to WAV File At '{output.as_posix()}'"
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
            f"Input {input_path} is already an "
            f"audio file ({ext}), no extraction needed"
        )
        return Path(input_path)

    LOGGER.info(f"Extracting audio from '{input_path}'")

    output = Path(output_path).resolve()
    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"Audio Extraction Failed -{input.as_posix()} is not a valid file"
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
            f"Failed to extract WAV audio from '{input.as_posix()}'"
        ) from e
    LOGGER.info(
        f"Extracted audio from '{input.as_posix()}' to WAV "
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
            f"Audio Filtering Failed -{input.as_posix()} is not a valid file"
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
        f"Applying Band-Pass ({highpass} - {lowpass}) and "
        f"loudness normalization to {input.as_posix()}"
    )
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        raise FFmpegError(f"Failed to filter '{input.as_posix()}'") from e

    LOGGER.info(
        f"Filtered '{input.as_posix()}' to WAV file at '{output.as_posix()}'"
    )
    return output


def to_mp4(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str] | None = None,
    resolution: str = "1280x720",
    target_bitrate: str = "2500k",
    preset: str = DEFAULT_CONVERSION_PRESET,
    use_gpu: bool = False,
) -> Path:
    """
    Converts any video supported by `FFMPEG` to an MP4 file using H.264 + AAC
    encoding

    info: Hardware Acceleration
        - When `use_gpu` is `True`, the whole pipeline stays on the GPU

        - `NVDEC` decodes, `scale_cuda` scales, and `NVENC` (`h264_nvenc`)
          encodes, so no frame ever crosses the PCIe bus to system memory

        - Callers gate `use_gpu` on `config.nvenc_available`, since the data
          center compute GPUs (`A100`, `H100`, `B200`) have `NVDEC` but no
          `NVENC`

        - The GPU command still falls back to CPU `libx264` if it
          fails for any other reason

    info: Geometry
        The video is scaled to fit within `resolution` while preserving aspect
        ratio. It is not padded to a fixed canvas, so the output keeps the
        source's aspect ratio (the player letterboxes as needed)

    info: Rate Control
        `preset` sets the encoder speed and quality (`-crf` / `-cq`), while
        `target_bitrate` is applied as a ceiling (`-maxrate` + `-bufsize`), so
        the file targets a quality level but never exceeds the bitrate cap

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str | os.PathLike[str]): Source file
            (any container/codec supported by FFMPEG)
        output_path (str | os.PathLike[str] | None): Path in which to save the
            MP4 file. When set to `None`, the file is saved to `input_path`
            with a `.mp4` suffix
        resolution (str): Maximum output size `WxH`. Aspect is preserved.
            Defaults to `1280x720`
        target_bitrate (str): Video bitrate ceiling. Defaults to `2500k`
        preset (str): One of `performance`, `balanced`, `quality`. Defaults to
            `balanced`
        use_gpu (bool): When `True`, runs the fully on-device NVIDIA pipeline,
            falling back to CPU `libx264` if it fails for any reason

    Raises:
        FFmpegError: If any of the FFMPEG commands have returned a non-zero
            exit code
        ValueError: If `input_path` doesn't exist or is not a file, if an
            invalid resolution is provided, or if `preset` is unknown

    Returns:
        Path to the resulting MP4
    """

    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"MP4 Conversion Failed -{input.as_posix()} is not a valid file"
        )

    output = Path(output_path or input.with_suffix(".mp4")).resolve()

    # Normalise resolution
    try:
        w, h = map(int, resolution.lower().split("x"))
    except ValueError as e:
        raise ValueError(
            f"Resolution must be 'WxH', got '{resolution}'"
        ) from e

    bundle = _resolve_preset(preset)
    bufsize = _double_bitrate(target_bitrate)

    # --- FFMPEG Parameters ---

    # Set Longer Analyze Duration And Probesize For Complex Video Files
    input_args = [
        "-analyzeduration",
        "20M",  # 20 Million Microseconds = 20 seconds
        "-probesize",
        "50M",  # 50 Megabytes
    ]

    # --- CPU Parameters ---

    # Scale To Fit (Aspect Preserved), Keep Dimensions Even For H.264
    cpu_vf = (
        f"scale=w={w}:h={h}:"
        "force_original_aspect_ratio=decrease:force_divisible_by=2"
    )

    # libx264 multi-threads automatically (frame-level threading across the
    # available cores), so no explicit `-threads` flag is needed
    x264_speed, x264_crf = bundle["x264"]
    cpu_enc = [
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-preset",
        x264_speed,
        "-crf",
        x264_crf,
        "-maxrate",
        target_bitrate,
        "-bufsize",
        bufsize,
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
        cpu_vf,
        *cpu_enc,
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output.as_posix(),
    ]

    # --- GPU Parameters (fully on-device NVDEC + scale_cuda + NVENC) ---

    # `scale_cuda` scales the decoded CUDA frames on the GPU and emits 8-bit
    # `yuv420p` so `h264_nvenc` can consume them directly
    gpu_vf = (
        f"scale_cuda=w={w}:h={h}:"
        "force_original_aspect_ratio=decrease:force_divisible_by=2:"
        "format=yuv420p"
    )

    nvenc_speed, nvenc_cq = bundle["nvenc"]
    nvidia_enc = [
        "-c:v",
        "h264_nvenc",
        "-preset",
        nvenc_speed,
        "-rc",
        "vbr",
        "-cq",
        nvenc_cq,
        "-b:v",
        "0",
        "-maxrate",
        target_bitrate,
        "-bufsize",
        bufsize,
    ]

    # `-hwaccel_output_format cuda` keeps NVDEC's decoded frames in GPU memory,
    # so the whole decode -> scale -> encode pipeline runs on the device
    # without PCIe round-trip to system memory
    nvidia_cmd = [
        ffmpeg_path,
        "-y",
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
        *input_args,
        "-i",
        input.as_posix(),
        "-vf",
        gpu_vf,
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

    cmd = nvidia_cmd if use_gpu else cpu_cmd

    LOGGER.info(
        f"Converting {input.as_posix()} to MP4 "
        f"(preset='{preset}', use_gpu='{use_gpu}')"
    )

    result = run_command(cmd, check=False)

    if result.returncode != 0 and use_gpu:
        LOGGER.warning(
            f"GPU MP4 Conversion Failed For "
            f"{input.as_posix()} - Retrying with CPU libx264"
        )

        # Retry on CPU. `check=False` so a failure flows into the
        # `check_returncode()` below and is wrapped as `FFmpegError`
        result = run_command(cpu_cmd, check=False)

    try:
        result.check_returncode()
        LOGGER.info(
            f"Converted {input.as_posix()} to MP4 file at {output.as_posix()}"
        )
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"CPU MP4 conversion for{input.as_posix()} failed"
        ) from e

    return output


def to_webm(
    ffmpeg_path: str,
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str] | None = None,
    resolution: str = "1280x720",
    target_bitrate: str = "2500k",
) -> Path:
    """
    Converts any video supported by `FFMPEG` to an WebM file using VP9 + Opus
    encoding

    info: CPU-Only
        - VP9 has no `NVENC` encoder, so the encode is always CPU `libvpx-vp9`

        - Decoding on `NVDEC` then copying the frames back to system memory for
          the CPU encode buys nothing on a short clip, so there is no GPU path

    info: Geometry
        The video is scaled to fit within `resolution` while preserving aspect
        ratio (no fixed-canvas padding), so the output keeps the source's
        aspect ratio

    info: Rate Control
        This is used for saved clips, which are short and become `Anki` card
        media, so it encodes at high quality (`-cpu-used 1`, `-crf 28`) with
        `target_bitrate` applied as a constrained-quality ceiling (`-b:v`)

    Args:
        ffmpeg_path (str): Path to the system's FFMPEG executable
        input_path (str | os.PathLike[str]): Source file
            (any container/codec supported by FFMPEG)
        output_path (str | os.PathLike[str] | None): Path in which to save the
            WebM file. When set to `None`, the file is saved to `input_path
            with a `.webm` suffix
        resolution (str): Maximum output size `WxH`. Aspect is preserved.
            Defaults to `1280x720`
        target_bitrate (str): Video bitrate ceiling. Defaults to `2500k`

    Raises:
        FFmpegError: If the FFMPEG command returned a non-zero exit code
        ValueError: If `input_path` doesn't exist or is not a file, or if an
            invalid resolution is provided

    Returns:
        Path to the resulting WebM
    """

    input = Path(input_path).resolve()

    if not input.is_file():
        raise ValueError(
            f"WebM Conversion Failed -{input.as_posix()} is not a valid file"
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

    # Scale To Fit (Aspect Preserved), Keep Dimensions Even
    vf = (
        f"scale=w={w}:h={h}:"
        "force_original_aspect_ratio=decrease:force_divisible_by=2"
    )

    # Set Longer Analyze Duration And Probesize For Complex Video Files
    input_args = [
        "-analyzeduration",
        "20M",  # 20 Million Microseconds = 20 seconds
        "-probesize",
        "50M",  # 50 Megabytes
    ]

    # --- CPU Encode (VP9 has no NVENC encoder, so always `libvpx-vp9`) ---

    # without `-row-mt`, `-tile-columns` and `-threads` libvpx-vp9 encodes
    # almost single-threaded and is extremely slow. Clips are short and become
    # Anki card media, so they are encoded at high quality (`-cpu-used 1`,
    # `-crf 28`)
    threads = str(os.cpu_count() or 4)
    cpu_enc = [
        "-c:v",
        "libvpx-vp9",
        "-crf",
        "28",
        "-b:v",
        target_bitrate,
        "-deadline",
        "good",
        "-cpu-used",
        "1",
        "-row-mt",
        "1",
        "-tile-columns",
        "2",
        "-threads",
        threads,
    ]

    cmd = [
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

    LOGGER.info(f"Converting {input.as_posix()} to WebM")

    result = run_command(cmd, check=False)

    try:
        result.check_returncode()
        LOGGER.info(
            f"Converted {input.as_posix()} to WebM file at {output.as_posix()}"
        )
    except subprocess.CalledProcessError as e:
        raise FFmpegError(
            f"CPU WebM conversion for {input.as_posix()} failed"
        ) from e

    return output
