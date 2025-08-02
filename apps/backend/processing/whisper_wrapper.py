"""
This module defines the `FWhisperWrapper` class for running the FasterWhisper
model.

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
  DEFAULT_SYS_MSG (str): Default system message to use for OpenAI
                         post-processing.
"""
from typing import Dict, Union, Optional
import logging
import time
from faster_whisper import WhisperModel
import srt
import datetime
from pathlib import Path
from processing.gpt_wrapper import GptModel
from utils.constants import FWHISPER_GPT_DEFAULT_SYS_MSG

LOGGER = logging.getLogger(__name__)
DEFAULT_SYS_MSG = FWHISPER_GPT_DEFAULT_SYS_MSG


class FWhisperWrapper:
    """
    Wrapper for FasterWhisper's WhisperModel including post-processing logic.

    Args:
      model_name (str): Whisper model name
      lang (str): Whisper model language.
      compute_type (str): Which compute type to use.
      device (str): Which device to use.
      gpt_sys_msg (str, optional): Custom GPT system message when using OpenAI
                                   post-processing.
      gpt_version (str): Which GPT version to use for OpenAI post-processing.
    """
    def __init__(self,
                 model_name: str = 'large-v3',
                 lang: str = 'ja',
                 compute_type: str = "float16",
                 device: str = 'cuda',
                 gpt_sys_msg: Optional[str] = None,
                 gpt_version: str = 'gpt-4.1'
                 ) -> None:

        self.lang = lang
        self.instance = WhisperModel(model_name,
                                     device=device,
                                     compute_type=compute_type)
        self.device = device
        self.model_name = model_name
        self.gpt_version = gpt_version
        self.gpt_sys_msg = gpt_sys_msg if gpt_sys_msg else DEFAULT_SYS_MSG

    def _check_input(self,
                     audio_path: str
                     ) -> Union[str, None]:
        """
        Check if input audio is a valid file.

        Args:
          audio_path (str): The path to the file.

        Returns:
          str: The same audio path from input or None if path is not valid.
        """
        audio_path = Path(audio_path).resolve()
        if audio_path.is_file():
            return str(audio_path)
        else:
            LOGGER.error(
                f"Transcribe Failed : Path '{audio_path}' is invalid.")
            return None

    def gpt_fix_srt(self,
                    source: str,
                    gpt_model_kwargs: Dict = {}
                    ) -> str:
        """
        Post-process transcription with OpenAI API.

        Args:
          source (str): Unaltered Transcription
          gpt_model_kwargs (dict): Additonal keyword arguments to pass to
                                   GptModel

        Returns:
          str: The formatted response from the OpenAI model.
        """
        kwargs = {
            'version': self.gpt_version,
            'from_dotenv': True,
            'system_msg': self.gpt_sys_msg,
            'ApiKey': None,
            'max_context': 100000}
        if gpt_model_kwargs:
            kwargs.update(gpt_model_kwargs)

        try:
            model = GptModel(**kwargs)
            LOGGER.info("Requesting GPT to fix SRT")
            request = model.request(source)
            rsrt = request['response']
            return rsrt
        except Exception as e:
            LOGGER.exception(f"Error Requesting GPT: {e}")
            return None

    def transcribe(self,
                   audio_path: str,
                   language: str = "ja",
                   generator_only: bool = False,
                   add_kargs: dict = {}) -> Union[Dict,
                                                  None]:
        """
        Transcribe audio with FasterWhisper.

        Args:
          audio_path (str): Path to the file to be transcribed.
          language (str): Which language to use.
          generator_only (bool): If true, don't run transcription and return
                                 generator instead.
          add_kwargs (dict): Addition keyword arguments for FasterWhisper
                             model.

        Returns:
          dict: The segment objects returned by FasterWhisper
                (contains .start, .end, .text and optionally .words)
        """

        audio_path = self._check_input(audio_path)

        if not audio_path:
            return None

        add_kwds = {
            'audio': audio_path,
            'beam_size': 5,
            'word_timestamps': False,
            'language': language,
            'vad_filter': False,
            "no_speech_threshold": 0.3,
            "log_prob_threshold": -1.0,
            "condition_on_previous_text": False,
            "compression_ratio_threshold": 2.0,
        }

        if add_kargs:
            add_kwds.update(add_kargs)
        try:
            segments, info = self.instance.transcribe(**add_kwds)
            if generator_only:
                return {'obj': segments,
                        'info': info}
            else:
                elapsed = time.perf_counter()
                segments = list(segments)
                tt = time.perf_counter() - elapsed
                return {'obj': segments,
                        'info': info,
                        'elapsed': tt
                        }
        except Exception as e:
            LOGGER.exception(f"Transcription Failed : '{e}' ")
            return None

    def transcribe_to_str(self,
                          audio_path: str,
                          transcribe_kwargs: dict = {}
                          ) -> str:
        """
        Transcribe to single raw string from joining segments.

        Args:
          audio_path (str): Path to the audio file.
          transcribe_kwargs (dict): Additional keyword arguments for the
                                    transcribe function.

        Returns:
          str: string of joined segments.
        """
        try:
            rdict = self.transcribe(audio_path, **transcribe_kwargs)
            segments = rdict['obj']
            text = "。".join(seg.text for seg in segments)
            return {"obj": segments,
                    "text": text,
                    "elapsed": rdict['elapsed']}
        except Exception as e:
            LOGGER.error(f"Error when generating str transcript: {e}")
            return None

    def transcribe_to_srt(self,
                          audio_path: str,
                          output_path: str,
                          fix_with_chat_gpt: bool = True,
                          string_result: bool = False,
                          gpt_model_kwargs: dict = {},
                          transcribe_kwargs: dict = {}
                          ) -> Union[str, None]:
        """
        Transcribe audio and save as an SRT file with sentence-level cues.

        Args:
          audio_path (str): Path to the file to be transcribed.
          output_path (str): Path to save the .srt file.
          fix_with_chat_gpt (bool): If True, post-process with OpenAI API.
          string_result (bool): If True, don't save any files and return an
                                SRT string instead.
          gpt_model_kwargs (dict): Additional keyword arguments for GptModel
          transcribe_kwargs (dict): Addition keyword arguments for the
                                    transcribe function.

        Returns:
          str: Either the file output path or the SRT string if string_result
               is True
        """
        try:
            opath = Path(output_path).resolve()
            if opath.suffix != '.srt':
                output_path = str(opath.with_suffix(".srt"))
        except Exception as e:
            LOGGER.error(f"Error resolving output path : '{e}'")
            if not string_result:
                return None
        try:
            segments = self.transcribe(audio_path, **transcribe_kwargs)
            segments = segments['obj']
            subtitles = []
            for i, seg in enumerate(segments, start=1):
                start = datetime.timedelta(seconds=seg.start)
                end = datetime.timedelta(seconds=seg.end)
                subtitles.append(srt.Subtitle(index=i,
                                              start=start,
                                              end=end,
                                              content=seg.text))
        except Exception as e:
            LOGGER.error(f"Error when generating SRT: '{e}'")
            return None

        if fix_with_chat_gpt:
            try:
                rsrt = self.gpt_fix_srt(srt.compose(subtitles),
                                        gpt_model_kwargs)
                if not rsrt:
                    LOGGER.error("Error fixing subtitles with ChatGPT")
                    return None

                if string_result:
                    LOGGER.info("Generated SRT")
                    return rsrt

                with open(opath.parent / "nogpt.srt", "w", encoding="utf-8"
                          ) as f:
                    f.write(srt.compose(subtitles))

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(rsrt)

                LOGGER.info("Generated SRT")
                return output_path

            except Exception as e:
                LOGGER.error(f"Error Writing SRT File: {e}")
                return None
        else:
            try:
                if string_result:
                    LOGGER.info("Generated SRT")
                    return srt.compose(subtitles)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(srt.compose(subtitles))
                LOGGER.info("Generated SRT")
                return output_path
            except Exception as e:
                LOGGER.exception(f"Failed to save SRT File : '{e}'")
                return None
