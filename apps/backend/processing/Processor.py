from typing import Optional, Union, Dict
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
from processing.text_processing import SentenceBreakdownService
from processing.audio_processing import AudioTools
from dotenv import load_dotenv
from utils.env_utils import check_env


class Processor:
    """
    Wrapper for 'processing' module utilities.
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

        """
        Initalize instance with API Keys or collect from
        environment variables
        """
        self.logger = logging.getLogger(__class__.__name__)
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
            self.logger.info("Not using Modal")
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
        self.logger.info("Processor Initialized")

    def __str__(self):
        if isinstance(self.save_path, TemporaryDirectory):
            return str(Path(self.save_path.name).resolve())
        return str(Path(self.save_path).resolve())

    def __repr__(self):
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

    def __del__(self):
        if isinstance(self.save_path, TemporaryDirectory):
            self.save_path.cleanup()

    async def modal_transcribe_to_srt(self,
                                      media_fp: Union[str, Path]
                                      ) -> Union[str, None]:
        async with self.modal_app.run():
            media_fp = Path(media_fp).as_posix()
            return await self.transcribe_srt_job.remote.aio(
                OPENAI_API_KEY=self.API_KEYS["OPENAI_API_KEY"],
                media_fp=media_fp)

    async def modal_transcribe_to_str(self,
                                      audio_fp: Union[str, Path]
                                      ) -> Union[str, None]:
        with self.modal_app.run():
            audio_fp = Path(audio_fp).as_posix()
            return self.transcribe_to_string_job.remote(audio_fp=audio_fp)

    async def modal_convert_to_mp4(self,
                                   video_fp: Union[str, Path],
                                   outpath: Union[str, Path]
                                   ):
        with self.modal_app.run():
            video_fp = Path(video_fp).as_posix()
            outpath = Path(outpath).as_posix()
            try:
                async for chunk in self.video_conversion_job.remote_gen.aio(
                       video_fp=video_fp):
                    with open(outpath, "ab") as f_out:
                        f_out.write(chunk)
                self.logger.info("Finished receiving converted video")
                return Path(outpath)
            except Exception as e:
                self.logger.error(f"Error Converting Video: {e}")
                return None
