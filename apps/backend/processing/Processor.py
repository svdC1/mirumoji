"""
This module defines the `Processor` class for managing modal interaction
and conditional imports for the CPU version.

Attributes:
  LOGGER (logging.Logger): Module's Logger object.
"""

from typing import Optional, Union, Dict
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
from processing.text_processing import SentenceBreakdownService
from processing.audio_processing import AudioTools
from dotenv import load_dotenv
from utils.env_utils import check_env

LOGGER = logging.getLogger(__name__)


class Processor:
    """
    Manage conditional imports, expose pre-configured instances of various
    instances from the `processing` module and manage Modal interaction.

    Args:
      save_path (Union[str, Path, None], optional): Optional Path to be used
                                                    as working directory.
      use_modal (bool): Wether to use Modal or not (CPU or GPU) version.
      gpt_version (str): Which GPT version to use for OpenAI integration.
      dotenv_path (Union[str, Path, None], optional): Optional Path to look
                                                      for .env file
      whisper_kwargs (dict): Optional additional keyword arguments for
                             `FWhisperWrapper`
      OPENAI_API_KEY (str, optional): Optionally pass OpenAI API key directly
      MODAL_TOKEN_ID (str, optional): Optionally pass Modal token id directly
      MODAL_TOKEN_SECRET (str, optional): Optionally pass Modal token secret
                                          directly

    Attributes:
      sentence_breakdown_service (SentenceBreakdownService): Instance of
                                                            `SentenceBreakdownService`
      fwhisper (FWhisperWrapper): Instance of `FWhisperWrapper`
      audio_tools (AudioTools): Instance of `AudioTools`

    """
    def __init__(
        self,
        save_path: Union[str, Path, None] = None,
        use_modal: bool = False,
        gpt_version: str = "gpt-4.1-mini",
        dotenv_path: Union[str, Path, None] = None,
        whisper_kwargs: Dict = {},
        OPENAI_API_KEY: Optional[str] = None,
        MODAL_TOKEN_ID: Optional[str] = None,
        MODAL_TOKEN_SECRET: Optional[str] = None
    ) -> None:

        # Configure Save Path
        if not save_path:
            self.save_path = TemporaryDirectory(ignore_cleanup_errors=True)
        else:
            self.save_path = Path(save_path).resolve()
            if not self.save_path.is_dir():
                raise FileNotFoundError(f"Dir: '{save_path}' does not exist")
        # Configure API Keys
        load_dotenv(dotenv_path=dotenv_path)
        if use_modal:
            expected_keys = {"OPENAI_API_KEY": OPENAI_API_KEY,
                             "MODAL_TOKEN_ID": MODAL_TOKEN_ID,
                             "MODAL_TOKEN_SECRET": MODAL_TOKEN_SECRET}
        else:
            LOGGER.info("Not using Modal")
            expected_keys = {"OPENAI_API_KEY": OPENAI_API_KEY}
        self.API_KEYS = check_env(expected_keys.keys(),
                                  expected_keys,
                                  dotenv_path)
        # Initializing Instances
        gpt_kwargs = {"from_dotenv": False,
                      "ApiKey": self.API_KEYS["OPENAI_API_KEY"]}
        self.sentence_breakdown_service = SentenceBreakdownService(gpt_version,
                                                                   gpt_kwargs)
        if not save_path:
            self.audio_tools = AudioTools(self.save_path.name)
        else:
            self.audio_tools = AudioTools(self.save_path)
        if use_modal:
            # CPU Version - Don't Import Whisper - No GPU
            from modal_processing.ModalApp import (app,
                                                   transcribe_srt_job,
                                                   transcribe_to_string_job,
                                                   video_conversion_job
                                                   )
            self.modal_app = app
            self.transcribe_srt_job = transcribe_srt_job
            self.transcribe_to_string_job = transcribe_to_string_job
            self.video_conversion_job = video_conversion_job
        else:
            # GPU Version - Import Whisper
            from processing.whisper_wrapper import FWhisperWrapper
            self.fwhisper = FWhisperWrapper(**whisper_kwargs)

        # Save attrs
        self.save_path_input = save_path
        self.use_modal = use_modal
        self.gpt_version = gpt_version
        self.dotenv_path = dotenv_path
        self.whisper_kwargs = whisper_kwargs
        self.openai_key_input = OPENAI_API_KEY
        self.modal_token_id_input = MODAL_TOKEN_ID
        self.modal_token_secret_input = MODAL_TOKEN_SECRET
        LOGGER.info("Processor Initialized")

    def __str__(self) -> str:
        if isinstance(self.save_path, TemporaryDirectory):
            return str(Path(self.save_path.name).resolve())
        return str(Path(self.save_path).resolve())

    def __repr__(self) -> str:
        args = {
            "save_path": self.save_path_input,
            "use_modal": self.use_modal,
            "gpt_version": self.gpt_version,
            "dotenv_path": self.dotenv_path,
            "whisper_kwargs": self.whisper_kwargs,
            "OPENAI_API_KEY": self.openai_key_input,
            "MODAL_TOKEN_ID": self.modal_token_id_input,
            "MODAL_TOKEN_SECRET": self.modal_token_secret_input
                }
        arg_s = ','.join([f"{k}={v}" for k, v in args.items()])
        return f"Processor({arg_s})"

    def __del__(self) -> None:
        if isinstance(self.save_path, TemporaryDirectory):
            self.save_path.cleanup()

    async def modal_transcribe_to_srt(self,
                                      media_fp: Union[str, Path]
                                      ) -> Union[str, None]:
        """
        Call Modal function to transcribe video to SRT

        Args:
          media_fp (Union[str, Path]): Path to the video to transcribe.

        Returns:
          str: Formatted SRT transcription string.
        """
        async with self.modal_app.run():
            media_fp = Path(media_fp).as_posix()
            return await self.transcribe_srt_job.remote.aio(
                OPENAI_API_KEY=self.API_KEYS["OPENAI_API_KEY"],
                media_fp=media_fp)

    async def modal_transcribe_to_str(self,
                                      audio_fp: Union[str, Path]
                                      ) -> Union[str, None]:
        """
        Call Modal function to transcribe audio to string.

        Args:
            audio_fp (Union[str, Path]): Path to the audio to transcribe.

        Returns:
            str: String transcription.
        """
        with self.modal_app.run():
            audio_fp = Path(audio_fp).as_posix()
            return self.transcribe_to_string_job.remote(audio_fp=audio_fp)

    async def modal_convert_to_mp4(self,
                                   video_fp: Union[str, Path],
                                   outpath: Union[str, Path]
                                   ):
        """
        Call Modal function to convert a video to MP4 format.

        Args:
          video_fp (Union[str, Path]): Path to the video to convert.
          outpath (Union[str, Path]): Where to save the received video stream.

        Returns:
          str: The path to converted video from `outpath`.
        """
        with self.modal_app.run():
            video_fp = Path(video_fp).as_posix()
            outpath = Path(outpath).as_posix()
            try:
                async for chunk in self.video_conversion_job.remote_gen.aio(
                       video_fp=video_fp):
                    with open(outpath, "ab") as f_out:
                        f_out.write(chunk)
                LOGGER.info("Finished receiving converted video")
                return Path(outpath)
            except Exception as e:
                LOGGER.error(f"Error Converting Video: {e}")
                return None
