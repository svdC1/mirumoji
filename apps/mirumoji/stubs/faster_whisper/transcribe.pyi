"""
Minimal stubs for `faster_whisper.transcribe` (only what the server uses)
"""
from collections.abc import Iterable
from typing import Any, BinaryIO

from numpy import ndarray

from .vad import VadOptions

class Word:
    start: float
    end: float
    word: str
    probability: float
    ...

class Segment:
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: list[int]
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: list[Word] | None
    temperature: float | None
    ...


class TranscriptionOptions:
    beam_size: int
    best_of: int
    patience: float
    length_penalty: float
    repetition_penalty: float
    no_repeat_ngram_size: int
    log_prob_threshold: float | None
    no_speech_threshold: float | None
    compression_ratio_threshold: float | None
    condition_on_previous_text: bool
    prompt_reset_on_temperature: float
    temperatures: list[float]
    initial_prompt: str | Iterable[int] | None
    prefix: str | None
    suppress_blank: bool
    suppress_tokens: list[int] | None
    without_timestamps: bool
    max_initial_timestamp: float
    word_timestamps: bool
    prepend_punctuations: str
    append_punctuations: str
    multilingual: bool
    max_new_tokens: int | None
    clip_timestamps: str | list[float]
    hallucination_silence_threshold: float | None
    hotwords: str | None
    ...


class TranscriptionInfo:
    language: str
    language_probability: float
    duration: float
    duration_after_vad: float
    all_language_probs: list[tuple[str, float]] | None
    transcription_options: TranscriptionOptions
    vad_options: VadOptions
    ...

class WhisperModel:
    def __init__(
        self,
        model_size_or_path: str,
        device: str = "auto",
        device_index: int | list[int] = 0,
        compute_type: str = "default",
        cpu_threads: int = 0,
        num_workers: int = 1,
        download_root: str | None = None,
        local_files_only: bool = False,
        files: dict[Any, Any] | None = None,
        **model_kwargs: dict[str, Any],
        ) -> None: ...
    def transcribe(
        self,
        audio: str | BinaryIO | ndarray,
        language: str | None = None,
        task: str = "transcribe",
        log_progress: bool = False,
        beam_size: int = 5,
        best_of: int = 5,
        patience: float = 1,
        length_penalty: float = 1,
        repetition_penalty: float = 1,
        no_repeat_ngram_size: int = 0,
        temperature: float | list[float] | tuple[float, ...] = [
            0.0,
            0.2,
            0.4,
            0.6,
            0.8,
            1.0,
        ],
        compression_ratio_threshold: float | None = 2.4,
        log_prob_threshold: float | None = -1.0,
        no_speech_threshold: float | None = 0.6,
        condition_on_previous_text: bool = True,
        prompt_reset_on_temperature: float = 0.5,
        initial_prompt: str | Iterable[int] | None = None,
        prefix: str | None = None,
        suppress_blank: bool = True,
        suppress_tokens: list[int] | None = [-1],
        without_timestamps: bool = False,
        max_initial_timestamp: float = 1.0,
        word_timestamps: bool = False,
        prepend_punctuations: str = "\"'“¿([{-",
        append_punctuations: str = "\"'.。,，!！?？:：”)]}、",  # noqa: RUF001
        multilingual: bool = False,
        vad_filter: bool = False,
        vad_parameters: dict[str, Any] | VadOptions | None = None,
        max_new_tokens: int | None = None,
        chunk_length: int | None = None,
        clip_timestamps: str | list[float] = "0",
        hallucination_silence_threshold: float | None = None,
        hotwords: str | None = None,
        language_detection_threshold: float | None = 0.5,
        language_detection_segments: int = 1,
    ) -> tuple[Iterable[Segment], TranscriptionInfo]:
        ...
