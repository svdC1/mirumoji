"""
This module defines the modal integration and the code to be run
in Modal's container.

Attributes:
  LOGGER (logging.Logger): Module's logging object.
"""

from typing import Union, Generator, Optional
import modal
import os
import logging
from mirumoji.server.utils.constants import MODAL_GPU, MODAL_IMAGE, BASE_MEDIA_DIR
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
LOGGER = logging.getLogger(__name__)
# --- Modal Setup ---
script_dir = Path(__file__).resolve().parent
project_root_dir = script_dir.parent
media_files_path = project_root_dir / str(BASE_MEDIA_DIR)
media_files_path.mkdir(parents=True,
                       exist_ok=True
                       )

LOGGER.info(
    f"Config Image + Mount '{media_files_path}' at /root/{str(BASE_MEDIA_DIR)}"
    )
# Build media_files on modal container startup
mirumoji_image = (modal.Image.from_registry(MODAL_IMAGE)
                  .add_local_dir(media_files_path,
                                 remote_path=f"/root/{str(BASE_MEDIA_DIR)}")
                  )

LOGGER.info("Configured.")

app = modal.App(
    "mirumoji-gpu",
    image=mirumoji_image
)

# Create Secret from local environment variables
env_secrets = modal.Secret.from_local_environ(["OPENAI_API_KEY"])

# --- End Modal Setup ---


@app.function(
    gpu=MODAL_GPU,
    timeout=600,
    include_source=True,
    secrets=[env_secrets]
)
def transcribe_srt_job(media_fp: Union[str, Path],
                       fwhisper_kwargs: dict = {},
                       transcribe_kwargs: dict = {},
                       fix_with_chat_gpt: bool = True
                       ) -> Optional[str]:
    """
    Runs Whisper transcription on media_fp, fixes with GPT,
    and returns SRT string.

    Args:
      media_fp (Union[str, Path]): Path to the video for transcription.
      fwhisper_kwargs (dict, optional): Additional arguments for
                                        `FWhisperWrapper`
      transcribe_kwargs (dict, optional): Additional arguments for
                                          `FWhisperWrapper.transcribe`
      fix_with_chat_gpt (bool, optional): If `True` request ChatGPT to fix
                                          transcription. Defaults to True

    Returns:
      Transcription in form of SRT string.
    """
    from mirumoji.server.processing.whisper_wrapper import FWhisperWrapper

    logging.basicConfig(level=logging.INFO,
                        style="{",
                        format="{levelname}-{name}-{message}"
                        )

    LOGGER.info(f"transcribe_srt_job started for media: '{media_fp}'")
    try:
        fwhisper = FWhisperWrapper(**fwhisper_kwargs)

        gpt_model_kwargs = {
            "ApiKey": os.environ["OPENAI_API_KEY"],
            "from_dotenv": False
        }
        srt_result_string = fwhisper.transcribe_to_srt(
            audio_path=str(media_fp),
            output_path=" ",
            string_result=True,
            fix_with_chat_gpt=fix_with_chat_gpt,
            gpt_model_kwargs=gpt_model_kwargs,
            transcribe_kwargs=transcribe_kwargs
            )

        if srt_result_string:
            LOGGER.info(f"Generated SRT For: '{media_fp}'")
            return srt_result_string
        else:
            LOGGER.warning(f"SRT Transcription Failed For: '{media_fp}'")
            return None
    except Exception as e:
        LOGGER.error(f"Error in transcribe_srt_job for '{media_fp}': '{e}'",
                     exc_info=True)
        return None


@app.function(
    gpu=MODAL_GPU,
    timeout=600,
    include_source=True,
    is_generator=True
)
def video_conversion_job(video_fp: Union[str, Path],
                         to_mp4_kwargs: dict = {}
                         ) -> Generator[bytes, None, None]:
    """
    Converts video_fp to MP4 using NVENC and returns the
    video content as bytes.

    Args:
      video_fp (Union[str, Path]): Path to the video for conversion.
      to_mp4_kwargs (dict, optional): Additional arguments for
                                      `AudioTools.to_mp4`.

    Yields:
      bytes: The converted video chunks.
    """
    logging.basicConfig(level=logging.INFO,
                        style="{",
                        format="{levelname}-{name}-{message}"
                        )

    from mirumoji.server.processing.audio_processing import AudioTools
    LOGGER.info(f"video_conversion_job started for video: '{video_fp}'")
    tmp_p = Path.cwd() / "tmp"
    tmp_p.mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Using temporary directory for video conversion: '{tmp_p}'")

    audio_tools = AudioTools()

    input_p = Path(video_fp)
    outp_local = tmp_p / f"{input_p.stem}_converted.mp4"

    try:
        LOGGER.info(f"Converting '{video_fp}' to '{outp_local}' using NVENC.")
        to_mp4_kwargs.update(input_path=str(video_fp),
                             output_path=str(outp_local),
                             use_nvenc=True
                             )
        result_p = audio_tools.to_mp4(**to_mp4_kwargs)

        if result_p and result_p.exists() and result_p.stat().st_size > 0:
            LOGGER.info(f"Converted video to: '{result_p}'")
            video_bytes = result_p.read_bytes()
            LOGGER.info(
                f"Returning {len(video_bytes)} bytes for converted video.")
            # Stream the converted file in chunks
            with open(result_p, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk
            LOGGER.info(f"Finished streaming video bytes for: '{result_p}'")
        else:
            e = (f"Video conversion failed or produced an "
                 f"empty file for: '{video_fp}'")
            LOGGER.error(e)
            raise Exception(e)
    except Exception as e:
        LOGGER.error(f"Error in video_conversion_job for '{video_fp}': '{e}'",
                     exc_info=True)
        raise e


@app.function(
    gpu=MODAL_GPU,
    timeout=600,
    include_source=True
)
def transcribe_to_string_job(audio_fp: Union[str, Path],
                             fwhisper_kwargs: dict = {},
                             transcribe_kwargs: dict = {}
                             ) -> str:
    """
    Transcribe audio to string using Faster Whisper.

    Args:
      audio_fp (Union[str, Path]): Path to the audio for transcription.
      fwhisper_kwargs (dict, optional): Additional arguments for
                                        `FWhisperWrapper`
      transcribe_kwargs (dict, optional): Additional arguments for
                                          `FWhisperWrapper.transcribe`

    Returns:
      str: Transcription in form of string.
    """
    from mirumoji.server.processing.whisper_wrapper import FWhisperWrapper
    logging.basicConfig(level=logging.INFO,
                        style="{",
                        format="{levelname}-{name}-{message}"
                        )
    fwhisper = FWhisperWrapper(**fwhisper_kwargs)
    return fwhisper.transcribe_to_str(audio_fp,
                                      transcribe_kwargs=transcribe_kwargs)
