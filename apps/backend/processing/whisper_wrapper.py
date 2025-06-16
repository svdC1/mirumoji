from typing import Dict, Union
import logging
import time
from faster_whisper import WhisperModel
import srt
import datetime
from pathlib import Path
from processing.gpt_wrapper import GptModel


class FWhisperWrapper:
    def __init__(self,
                 model_name: str = 'large-v3',
                 lang: str = 'ja',
                 compute_type: str = "float16",
                 device: str = 'cuda',
                 gpt_sys_msg: str = None,
                 gpt_version: str = 'gpt-4.1'
                 ) -> None:

        self.logger = logging.getLogger(self.__class__.__name__)
        self.lang = lang
        self.instance = WhisperModel(model_name,
                                     device=device,
                                     compute_type=compute_type)
        self.device = device
        self.model_name = model_name
        self.gpt_version = gpt_version

        if not gpt_sys_msg:
            self.gpt_sys_msg = """You are an expert subtitle editor for \
                Japanese anime.You understand:\
            - Conversational Japanese, character names, honorifics,\
                onomatopoeia and scene-specific slang.\
            - How to pick the correct Kanji/Kana from phonetic transcriptions\
                based on context.\
            - Natural sentence flow and typical timing for subtitles.

            Your job is to **clean only the text** of each SRT cue:
            • Fix mis-recognized Kanji or Kana.
            • Merge cues that split a single sentence \
                (new cue’s start = earlier, end = later).\
            • Remove any pure gibberish or repeated song-lyric artifacts.
            • Insert correct punctuation (。？！、) and adjust spacing.

            **You must not**:
            - Change any start/end timestamps.
            - Renumber beyond simple sequential order.
            - Add or remove cues (only merge as above).
            - Add any commentary or explanations.

            Output **only** the cleaned `.srt` file content.
            """
        else:
            self.gpt_sys_msg = gpt_sys_msg

    def _check_input(self,
                     audio_path: str) -> Union[str, None]:

        audio_path = Path(audio_path).resolve()
        if audio_path.is_file():
            return str(audio_path)
        else:
            self.logger.error(f"Transcribe Failed : Path : {audio_path} \
                is invalid.\
                ")
            return None

    def gpt_fix_srt(self,
                    source: str,
                    gpt_model_kwargs: dict = {}):
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
            self.logger.info("Requesting GPT to fix SRT")
            request = model.request(source)
            rsrt = request['response']
            return rsrt
        except Exception as e:
            self.logger.error(f"Error Requesting GPT: {e}")
            return None

    def transcribe(self,
                   audio_path: str,
                   language: str = "ja",
                   generator_only: bool = False,
                   add_kargs: dict = {}) -> Union[Dict,
                                                  None]:
        """
        Transcribe audio and return a list of segment objects.
        Each segment has .start, .end, .text, and optionally .words.
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
            segments, info = self.instance.transcribe(** add_kwds)
            if generator_only:
                return {'obj': segments,
                        'info': info}
            else:
                elapsed = time.perf_counter()
                segments = list(segments)
                tt = time.perf_counter() - elapsed
                return {'obj': segments,
                        'info': info,
                        'elapsed': tt}
        except Exception as e:
            self.logger.error(f"Transcription Failed :{e}")
            return None

    def transcribe_to_str(self,
                          audio_path: str,
                          transcribe_kwargs: dict = {}):
        """
        Transcribe to single raw string from joining segments.
        """
        try:
            rdict = self.transcribe(audio_path, **transcribe_kwargs)
            segments = rdict['obj']
            text = "。".join(seg.text for seg in segments)
            return {"obj": segments,
                    "text": text,
                    "elapsed": rdict['elapsed']}
        except Exception as e:
            self.logger.error(f"Error when generating str transcript: {e}")
            return None

    def transcribe_to_srt(self,
                          audio_path: str,
                          output_path: str,
                          fix_with_chat_gpt: bool = True,
                          string_result: bool = False,
                          gpt_model_kwargs: dict = {},
                          transcribe_kwargs: dict = {}) -> Union[str, None]:
        """
        Transcribe audio and save as an SRT file with sentence-level cues.
        """
        try:
            opath = Path(output_path).resolve()
            if opath.suffix != '.srt':
                output_path = str(opath.with_suffix(".srt"))
        except Exception as e:
            self.logger.error(f"Error cleaning output path : {e}")
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
            self.logger.error(f"Error when generating SRT: {e}")
            return None

        if fix_with_chat_gpt:
            try:
                rsrt = self.gpt_fix_srt(srt.compose(subtitles),
                                        gpt_model_kwargs)
                if not rsrt:
                    return None

                if string_result:
                    self.logger.info("Generated SRT")
                    return rsrt

                with open(opath.parent / "nogpt.srt", "w", encoding="utf-8"
                          ) as f:
                    f.write(srt.compose(subtitles))

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(rsrt)

                self.logger.info("Generated SRT")
                return output_path

            except Exception as e:
                self.logger.error(f"Error Writing SRT File: {e}")
                return None
        else:
            try:
                if string_result:
                    self.logger.info("Generated SRT")
                    return srt.compose(subtitles)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(srt.compose(subtitles))
                self.logger.info("Generated SRT")
                return output_path
            except Exception as e:
                self.logger.error(f"Failed to save SRT File : {e}")
                return None
