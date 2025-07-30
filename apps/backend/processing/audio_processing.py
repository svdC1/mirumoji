"""
This module defines the `AudioTools` class for performing media operations.

Attributes:
    LOGGER (logging.Logger): Logger object of module.
"""

import subprocess
import shutil
import pathlib
from typing import Union
import logging
from datetime import datetime

LOGGER = logging.getLogger(__name__)


class AudioTools:

    """
    Perform operations on media using system installed FFMPEG.

    Args:
      workding_dir (Union[str, pathlib.Path], optional): Default directory to
                                                         save processed media

    Attributes:
      working_dir (pathlib.Path): Default directory to save processed media.
      temp (pathlib.Path): Temporary directory for operations created inside
                           working_dir.
      ffmpeg (str): System FFmpeg Path.
      ffprobe (str): System FFprobe Path.

    """

    def __init__(self,
                 working_dir: Union[str, pathlib.Path] = None
                 ) -> None:

        # Check if Directory exists, create if it doesn't
        if not working_dir:
            working_dir = "audio_tools_wd"
        self.working_dir = pathlib.Path(working_dir).resolve()
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Setup Temp
        self.temp = (self.working_dir / pathlib.Path("temp")
                     ).resolve()
        self.temp.mkdir(parents=True, exist_ok=True)
        self.log_dir = pathlib.Path.home() / ".mirumoji_logs"
        self.log_dir.mkdir(exist_ok=True)

        # Search for FFMPEG and FFPROBE with shutil
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")
        if not self.ffmpeg:
            self.temp.rmdir()
            LOGGER.error("FFmpeg not found")
            raise EnvironmentError("FFmpeg not found.")
        if not self.ffprobe:
            self.temp.rmdir()
            LOGGER.error("FFprobe not found")
            raise EnvironmentError("FFprobe not found.")

        LOGGER.debug(f"FFMPEG at : {self.ffmpeg}")

    def run_command(self,
                    command: list[str],
                    capture_output: bool = False,
                    check: bool = False,
                    cwd: str = None,
                    hide_and_log: bool = False
                    ) -> Union[subprocess.CompletedProcess,
                               None]:
        """
        Wrapper for subprocess.run to handle errors and results.

        Args:
          command (list): The CMD list of the command to be executed.
          capture_output (bool): passed directly to subprocess.run
          check (bool): passed directly to subprocess.run
          cwd (str, optional): The directory in which the command is run.
          hide_and_log (bool): If True redirect stdout and stderr to
                               subprocess.DEVNULL and  subprocess.PIPE
                               respectively.

        Returns:
          Union[subprocess.CompletedProcess, None]: The result of
                                                    subprocess.run or None.
        """
        LOGGER.debug(f"Running Command: {' '.join(command)}")

        try:
            if hide_and_log:
                result = subprocess.run(command,
                                        check=check,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        cwd=cwd)
            else:
                result = subprocess.run(command,
                                        check=check,
                                        capture_output=capture_output,
                                        text=True,
                                        cwd=cwd)

            if capture_output:
                LOGGER.debug(f"STDOUT: '{result.stdout}'")
                LOGGER.debug(f"STDERR: '{result.stderr}'")

            return result

        except subprocess.CalledProcessError as e:
            LOGGER.error(f"Command Failed: {' '.join(command)}")
            if capture_output:
                LOGGER.error(f"STDOUT: '{e.stdout}'")
                LOGGER.error(f"STDERR: '{e.stderr}'")
            error_message = e.stderr.decode()
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            try:
                with open(self.log_dir / "ffmpeg_error.log",
                          "a",
                          encoding="utf-8") as log_file:
                    log_file.write(
                        f"{timestamp} FFmpeg error:\n{error_message}\n\n")
            except Exception:
                return None
            return None

    def to_wav(self,
               input_path: str,
               output_path: str = None
               ) -> pathlib.Path:

        """
        Convert file to `.wav` format.

        Args:
          input_path (str): Path to the file.
          output_path (str, optional): Optional custom output path, if not
                                       specified uses the input filename.

        Returns:
          pathlib.Path: The output path of the converted file.
        """
        ip = pathlib.Path(input_path).resolve()
        op = pathlib.Path(output_path or ip.with_suffix(".wav")).resolve()

        # Use POSIX path style for ffmpeg
        s = ip.as_posix()
        so = op.as_posix()

        command = [self.ffmpeg,
                   "-y",  # overwrite output file without asking
                   "-i", s,
                   "-ar", "44100",
                   "-ac", "2",
                   "-f", "wav",
                   so]

        self.run_command(command,
                         capture_output=True,
                         check=True,
                         hide_and_log=True)
        LOGGER.info(f"Converted to WAV '{s}' → '{so}'")
        return op

    def extract_audio(self, input_path: str) -> str:
        """
        Extract a WAV file from video container. If input file is already an
        audio file, return the unchanged input file path.

        Args:
          input_path (str): Path to the file.

        Returns:
          pathlib.Path: The output path of the converted file.
        """

        ext = pathlib.Path(input_path).resolve().suffix
        audio_exts = {".wav",
                      ".mp3",
                      ".m4a",
                      ".flac",
                      ".aac"
                      }
        if ext in audio_exts:
            LOGGER.info(f"Input is audio '{ext}', no extraction needed")
            return input_path

        LOGGER.info(f"Extracting audio from video container '{input_path}'")
        out = pathlib.Path(input_path).resolve().with_suffix(".wav")
        si = pathlib.Path(input_path).resolve().as_posix()
        so = out.as_posix()
        cmd = [
            self.ffmpeg, "-y", "-i", si,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1", so
        ]
        self.run_command(cmd,
                         hide_and_log=True)
        LOGGER.info(f"Extracted audio from '{si}' → '{so}'")
        return out

    def filter_audio(self,
                     input_path: str,
                     output_wav: str,
                     highpass: int = 300,
                     lowpass: int = 3400) -> str:
        """
        Extracts audio from video or uses an existing audio file,
        applies a band-pass (highpass→lowpass) and loudness normalization,
        then writes out a 16 kHz mono WAV ready for Whisper.

        Args:
          input_path (str):   Path to video (any container) or audio file.
          output_wav (str):   Path where the cleaned WAV will be saved.
          highpass (int):     Cut everything below this frequency (Hz).
          lowpass (int):      Cut everything above this frequency (Hz).

        Returns:
          str: The output_wav path, for chaining into Whisper.
        """
        i = pathlib.Path(input_path).resolve().as_posix()
        o = pathlib.Path(output_wav).resolve().as_posix()
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", i,
            "-vn",
            "-af",
            f"highpass=f={highpass}, lowpass=f={lowpass}, loudnorm",
            "-ac", "1",
            "-ar", "16000",
            o
        ]
        LOGGER.info("Filtering audio")
        self.run_command(cmd, hide_and_log=True)
        LOGGER.info(f"Filtered '{i}' → '{o}'")
        return output_wav

    def to_mp4(
        self,
        input_path: str,
        output_path: str | None = None,
        resolution: str = "1280x720",
        target_bitrate: str = "2500k",
        use_nvenc: bool = False,
    ) -> Union[pathlib.Path, None]:
        """
        Convert any video to MP4 (H.264 + AAC).

        Args:
          input_path (str): Source file (any container/codec FFmpeg supports).
          output_path (str, optional): Destination .mp4 (defaults to same stem)
          resolution (str): Target canvas WxH. Aspect is preserved.
          target_bitrate (str):  Video bitrate (e.g. '2500k').
          use_nvenc (bool): True → try NVIDIA NVENC; False → libx264 CPU.

        Returns:
            pathlib.Path: Path of the MP4, or None on failure.
        """

        src = pathlib.Path(input_path).resolve()
        if not src.is_file():
            LOGGER.error(f"Input '{src}' does not exist")
            return None

        dst = pathlib.Path(output_path or src.with_suffix(".mp4")).resolve()

        try:
            w, h = map(int, resolution.lower().split("x"))
        except ValueError:
            LOGGER.error(f"Resolution must be 'WxH', got '{resolution}'")
            return None

        # 1) scale to fit, 2) pad to canvas (center)
        vf = (
            f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,"
            f"pad=w={w}:h={h}:x=(ow-iw)/2:y=(oh-ih)/2:color=black"
        )
        cpu_enc = [
                "-c:v", "libx264",
                "-profile:v", "high",
                "-b:v", target_bitrate,
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
            ]
        cpu_cmd = [
            self.ffmpeg, "-y",
            "-i", src.as_posix(),
            "-vf", vf,
            *cpu_enc,
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            dst.as_posix(),
        ]

        # ---------- choose encoder ----------
        if use_nvenc:
            enc_args = [
                "-c:v", "h264_nvenc",
                "-preset", "p6",
                "-rc:v", "vbr",
                "-b:v", target_bitrate,
                "-pix_fmt", "yuv420p",
            ]
        else:
            enc_args = cpu_enc

        cmd = [
            self.ffmpeg, "-y",
            "-i", src.as_posix(),
            "-vf", vf,
            *enc_args,
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            dst.as_posix(),
        ]
        LOGGER.info(f"Converting with use_nvenc='{use_nvenc}'")
        result = self.run_command(cmd, capture_output=True, hide_and_log=True)
        # Retry with normal args in case of NVENC error
        if result.returncode != 0 and use_nvenc:
            LOGGER.info("Retrying without NVENC")
            result = self.run_command(cpu_cmd,
                                      capture_output=True,
                                      hide_and_log=True)
        if result is None or result.returncode != 0:
            LOGGER.error(f"FFmpeg to_mp4 failed:\n'{result.stderr}'")
            return None

        LOGGER.info(f"Converted '{src.name}' → '{dst.name}'")
        return dst

    def to_webm(
        self,
        input_path: str,
        output_path: str | None = None,
        resolution: str = "1280x720",
        target_bitrate: str = "2500k",
        use_nvenc: bool = False,
    ) -> Union[pathlib.Path, None]:
        """
        Convert any video to WebM (VP9 + Opus).

        Args:
          input_path (str): Source file (any container/codec FFmpeg supports).
          output_path (str, optional): Destination (defaults to same stem)
          resolution (str): Target canvas WxH. Aspect is preserved.
          target_bitrate (str):  Video bitrate (e.g. '2500k').
          use_nvenc (bool): True → try NVIDIA NVENC; False → libvpx-vp9 CPU.

        Returns:
            pathlib.Path: Path of the WebM, or None on failure.
        """

        src = pathlib.Path(input_path).resolve()
        if not src.is_file():
            LOGGER.error(f"Input '{src}' does not exist")
            return None

        dst = pathlib.Path(output_path or src.with_suffix(".webm")).resolve()

        try:
            w, h = map(int, resolution.lower().split("x"))
        except ValueError:
            LOGGER.error(f"Resolution must be 'WxH', got '{resolution}'")
            return None

        # 1) scale to fit, 2) pad to canvas (center)
        vf = (
            f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,"
            f"pad=w={w}:h={h}:x=(ow-iw)/2:y=(oh-ih)/2:color=black"
        )
        cpu_enc = [
                "-c:v", "libvpx-vp9",
                "-b:v", target_bitrate,
                "-deadline", "good",
            ]
        cpu_cmd = [
            self.ffmpeg, "-y",
            "-i", src.as_posix(),
            "-vf", vf,
            *cpu_enc,
            "-c:a", "libopus",
            "-b:a", "128k",
            dst.as_posix(),
        ]

        # ---------- choose encoder ----------
        if use_nvenc:
            enc_args = [
                "-c:v", "vp9_nvenc",
                "-rc:v", "vbr",
                "-b:v", target_bitrate,
            ]
        else:
            enc_args = cpu_enc

        cmd = [
            self.ffmpeg, "-y",
            "-i", src.as_posix(),
            "-vf", vf,
            *enc_args,
            "-c:a", "libopus",
            "-b:a", "128k",
            dst.as_posix(),
        ]
        LOGGER.info(f"Converting with use_nvenc='{use_nvenc}'")
        result = self.run_command(cmd, capture_output=True, hide_and_log=True)
        # Retry with normal args in case of NVENC error
        if result.returncode != 0 and use_nvenc:
            LOGGER.info("Retrying without NVENC")
            result = self.run_command(cpu_cmd,
                                      capture_output=True,
                                      hide_and_log=True)
        if result is None or result.returncode != 0:
            LOGGER.error(f"FFmpeg to_webm failed:\n'{result.stderr}'")
            return None

        LOGGER.info(f"Converted '{src.name}' → '{dst.name}'")
        return dst
