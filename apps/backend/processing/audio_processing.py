import subprocess
import shutil
import pathlib
from typing import Union
import logging
from datetime import datetime


class AudioTools:

    """
    Wrapper for FFMPEG to perform simple editing on video and audio
    files.
    """

    def __init__(self,
                 working_dir: Union[str, pathlib.Path]):
        """
        Create instance relating to a specific directory where
        operations will be performed.
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.working_dir = pathlib.Path(working_dir).resolve()
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.temp = (working_dir / pathlib.Path("temp")).resolve()
        self.temp.mkdir(parents=True, exist_ok=True)
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")
        if not self.ffmpeg:
            self.temp.rmdir()
            raise EnvironmentError("FFmpeg not found.")
        if not self.ffprobe:
            self.temp.rmdir()
            raise EnvironmentError("FFprobe not found.")
        self.logger.debug(f"FFMPEG at : {self.ffmpeg}")

    def run_command(self,
                    command: list[str],
                    capture_output: bool = False,
                    check: bool = False,
                    cwd: str = None,
                    hide_and_log: bool = False
                    ) -> Union[subprocess.CompletedProcess,
                               None]:
        """
        Simple wrapper for subprocess execution which returns a completed
        subprocess instance in case of sucess or returns None and logs error
        in case of failed subprocess execution.
        """
        self.logger.debug(f"Running Command: {' '.join(command)}")

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
                self.logger.debug(f"STDOUT: {result.stdout}")
                self.logger.debug(f"STDERR: {result.stderr}")

            return result

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command Failed: {' '.join(command)}")
            if capture_output:
                self.logger.error(f"STDOUT: {e.stdout}")
                self.logger.error(f"STDERR: {e.stderr}")
                error_message = e.stderr.decode()
                timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
                with open(self.working_dir / "error_log.txt",
                          "w", encoding="utf-8") as log_file:
                    log_file.write(
                        f"{timestamp} FFmpeg error:\n{error_message}\n\n")
            return None

    def to_wav(self,
               input_path: str,
               output_path: str = None):

        ip = pathlib.Path(input_path).resolve()
        op = pathlib.Path(output_path or ip.with_suffix(".wav")).resolve()
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
        return op

    def extract_audio(self, input_path: str) -> str:
        """
        If input is a video container, extract to a temp WAV.
        Otherwise return the original path.
        """
        ext = pathlib.Path(input_path).resolve().suffix
        audio_exts = {".wav", ".mp3", ".m4a", ".flac", ".aac"}
        if ext in audio_exts:
            self.logger.debug("Input is audio (%s), no extraction needed", ext)
            return input_path

        self.logger.info("Extracting audio from video container %s",
                         input_path)
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
        self.logger.debug(f"Audio Saved at {so}")
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
        input_path:   Path to video (any container) or audio file.
        output_wav:   Path where the cleaned WAV will be saved.
        highpass:     Cut everything below this frequency (Hz).
        lowpass:      Cut everything above this frequency (Hz).

        Returns:
        The output_wav path, for chaining into Whisper.
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
        self.run_command(cmd, hide_and_log=True)
        return output_wav

    def to_mp4(
        self,
        input_path: str,
        output_path: str | None = None,
        resolution: str = "1280x720",
        target_bitrate: str = "2500k",
        use_nvenc: bool = False,
    ) -> pathlib.Path | None:
        """
        Convert any video to MP4 (H.264 + AAC) that streams well in <video>.

        Args:
            input_path:      Source file (any container/codec FFmpeg supports).
            output_path:     Destination .mp4 (defaults to same stem).
            resolution:      Target canvas WxH. Aspect is preserved.
            target_bitrate:  Video bitrate (e.g. '2500k').
            use_nvenc:       True → try NVIDIA NVENC; False → libx264 CPU.

        Returns:
            pathlib.Path of the MP4, or None on failure.
        """
        src = pathlib.Path(input_path).resolve()
        if not src.is_file():
            self.logger.error("to_mp4: %s does not exist", src)
            return None

        dst = pathlib.Path(output_path or src.with_suffix(".mp4")).resolve()

        try:
            w, h = map(int, resolution.lower().split("x"))
        except ValueError:
            self.logger.error("to_mp4: resolution must be 'WxH', got %s",
                              resolution)
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
                "-preset", "p6",           # quality-speed sweet spot
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

        result = self.run_command(cmd, capture_output=True, hide_and_log=True)
        # Retry with normal args in case of NVENC error
        if result.returncode != 0 and use_nvenc:
            result = self.run_command(cpu_cmd,
                                      capture_output=True,
                                      hide_and_log=True)
        if result is None or result.returncode != 0:
            self.logger.error("FFmpeg to_mp4 failed:\n%s", result.stderr)
            return None

        self.logger.info("Converted %s → %s", src.name, dst.name)
        return dst
