from typing import Union, Generator
import modal
import logging
from processing.whisper_wrapper import FWhisperWrapper
from processing.audio_processing import AudioTools
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# --- Modal Setup ---
script_dir = Path(__file__).resolve().parent
project_root_dir = script_dir.parent
media_files_path = project_root_dir / "media_files"
media_files_path.mkdir(parents=True,
                       exist_ok=True)

logger.info(f"Config Image + Mount {media_files_path} at /root/media_files")
# Build media_files on modal container startup
mirumoji_image = modal.Image.from_registry(
    "docker.io/svdc1/mirumoji-modal-gpu:latest"
).add_local_dir(media_files_path,
                remote_path="/root/media_files")

logger.info("Configured.")

app = modal.App(
    "mirumoji-gpu",
    image=mirumoji_image
)
# --- End Modal Setup ---


@app.function(
    gpu="A10G",
    timeout=600,
    include_source=True
)
def transcribe_srt_job(OPENAI_API_KEY: str,
                       media_fp: Union[str, Path]
                       ) -> Union[str, None]:
    """
    Runs Whisper transcription on media_fp, fixes with GPT,
    and returns SRT string.
    """

    logging.basicConfig(level=logging.INFO,
                        style="{",
                        format="{levelname}-{name}-{message}"
                        )

    logger.info(f"transcribe_srt_job started for media: {media_fp}")
    try:
        fwhisper = FWhisperWrapper()

        gpt_model_kwargs = {
            "ApiKey": OPENAI_API_KEY,
            "from_dotenv": False
        }
        srt_result_string = fwhisper.transcribe_to_srt(
            audio_path=str(media_fp),
            output_path=" ",
            string_result=True,
            fix_with_chat_gpt=True,
            gpt_model_kwargs=gpt_model_kwargs
            )

        if srt_result_string:
            logger.info(f"Generated SRT For: {media_fp}")
            return srt_result_string
        else:
            logger.warning(f"SRT Transcription Failed For: {media_fp}")
            return None
    except Exception as e:
        logger.error(f"Error in transcribe_srt_job for {media_fp}: {e}",
                     exc_info=True)
        return None


@app.function(
    gpu="A10G",
    timeout=600,
    include_source=True,
    is_generator=True
)
def video_conversion_job(video_fp: Union[str, Path],
                         ) -> Generator[bytes, None, None]:
    """
    Converts video_fp to MP4 using NVENC and returns the
    video content as bytes.
    """
    logging.basicConfig(level=logging.INFO,
                        style="{",
                        format="{levelname}-{name}-{message}"
                        )

    logger.info(f"video_conversion_job started for video: {video_fp}")
    tmp_p = Path.cwd() / "tmp"
    logger.info(f"Using temporary directory for video conversion: {tmp_p}")

    audio_tools = AudioTools(working_dir=tmp_p)

    input_p = Path(video_fp)
    outp_local = tmp_p / f"{input_p.stem}_converted.mp4"

    try:
        logger.info(f"Converting {video_fp} to {outp_local} using NVENC.")
        result_p = audio_tools.to_mp4(
            input_path=str(video_fp),
            output_path=str(outp_local),
            use_nvenc=True
        )

        if result_p and result_p.exists() and result_p.stat().st_size > 0:
            logger.info(f"Converted video to: {result_p}")
            video_bytes = result_p.read_bytes()
            logger.info(
                f"Returning {len(video_bytes)} bytes for converted video.")
            # Stream the converted file in chunks
            with open(result_p, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk
            logger.info(f"Finished streaming video bytes for: {result_p}")
        else:
            e = f"Video conversion failed or produced an \
                empty file for: {video_fp}"
            logger.error(e)
            raise Exception(e)
    except Exception as e:
        logger.error(f"Error in video_conversion_job for {video_fp}: {e}",
                     exc_info=True)
        raise e


@app.function(
    gpu="A10G",
    timeout=600,
    include_source=True
)
def transcribe_to_string_job(audio_fp: Union[str, Path],
                             ) -> Union[str, None]:
    logging.basicConfig(level=logging.INFO,
                        style="{",
                        format="{levelname}-{name}-{message}"
                        )
    fwhisper = FWhisperWrapper()
    return fwhisper.transcribe_to_str(audio_fp)
