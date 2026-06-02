"""
Defines Pydantic request models for the API's endpoints

abstract: Model selection
    - LLM requests have a `model` selector in `provider:model` form
      (e.g. `"openai:gpt-4.1-mini"`)

tip: LLM Request Defaults
    - `sys_msg` / `prompt` are optional

    - When omitted the server falls back to its default system message and
      prompt
"""

from pydantic import BaseModel

# --- Dictionary Requests ---


class TokenizeBatchRequest(BaseModel):
    """
    Request for the batch tokenize endpoint (`POST /dict/tokenize`)

    Args:
        sentences (list[str]): The sentences to tokenize, in order
    """

    sentences: list[str]


# --- LLM requests ---


class BreakdownRequest(BaseModel):
    """
    Request for the `/llm/breakdown` endpoint

    Args:
        sentence (str): The sentence containing the focus word
        focus (str | None): The word to explain in context
        model (str): Model selector in `provider:model` form
        sys_msg (str | None): Optional custom system message
        prompt (str | None): Optional custom prompt template
            (`{0}` = sentence, `{1}` = focus)
    """

    sentence: str
    focus: str | None = None
    model: str
    sys_msg: str | None = None
    prompt: str | None = None


class ExplainSentenceRequest(BaseModel):
    """
    Request for the `/llm/explain_sentence` endpoint

    Args:
        sentence (str): The sentence to explain
        model (str): Model selector in `provider:model` form
        sys_msg (str | None): Optional custom system message
        prompt (str | None): Optional custom prompt template
            (`{0}` = sentence)
    """

    sentence: str
    model: str
    sys_msg: str | None = None
    prompt: str | None = None


class FixSrtRequest(BaseModel):
    """
    Request for the `/llm/fix_srt` endpoint

    Args:
        srt (str): Raw SRT content to clean up
        model (str): Model selector in `provider:model` form
        sys_msg (str | None): Optional custom system message
    """

    srt: str
    model: str
    sys_msg: str | None = None


class ChatRequest(BaseModel):
    """
    Request for the streaming `/llm/stream` chat endpoint

    Args:
        prompt (str): The user prompt
        model (str): Model selector in `provider:model` form
        system_message (str | None): Optional system message
    """

    prompt: str
    model: str
    system_message: str | None = None


# --- Profile Requests ---


class LlmTemplateRequest(BaseModel):
    """
    Request for upserting a profile's LLM template

    Args:
        sys_msg (str): System message
        prompt (str): Prompt template
        model (str): Model selector in `provider:model` form
    """

    sys_msg: str
    prompt: str
    model: str


# --- Media Query-Parameters Requests (Bound via Annotated[..., Query()]) ---


class TranscribeOptions(BaseModel):
    """
    Curated, query-param-friendly transcription options for `faster_whisper`

    warning: Curation
        - Only scalar `faster_whisper` transcribe options that tune quality and
          filtering are exposed

        - Options that would change the segment structure
          (`.start` / `.end` / `.text`) or the assumption that media is
          transcribed (not translated) in the chosen language are deliberately
          omitted (e.g. `task`, `without_timestamps`)

        - Unset (`None`) fields fall back to
          `mirumoji.server.processing.whisper.DEFAULT_TRANSCRIBE_OPTS`

    Args:
        language (str): Language code to transcribe in
        beam_size (int | None): Beam size for decoding
        best_of (int | None): Number of candidates when sampling
        patience (float | None): Beam-search patience factor
        length_penalty (float | None): Exponential length penalty
        temperature (float | None): Sampling temperature
        compression_ratio_threshold (float | None): Gzip compression-ratio
            threshold above which output is treated as failed
        log_prob_threshold (float | None): Average log-probability threshold
            below which output is treated as failed
        no_speech_threshold (float | None): No-speech probability threshold
        condition_on_previous_text (bool | None): Feed prior text as context
        initial_prompt (str | None): Optional text to bias the first window
        vad_filter (bool | None): Apply voice-activity-detection filtering
    """

    language: str = "ja"
    beam_size: int | None = None
    best_of: int | None = None
    patience: float | None = None
    length_penalty: float | None = None
    temperature: float | None = None
    compression_ratio_threshold: float | None = None
    log_prob_threshold: float | None = None
    no_speech_threshold: float | None = None
    condition_on_previous_text: bool | None = None
    initial_prompt: str | None = None
    vad_filter: bool | None = None


class TranscribeAudioRequest(TranscribeOptions):
    """
    Options for `/audio/transcribe`

    Args:
        clean_audio (bool): Apply a band-pass + loudness filter before
            transcription
    """

    clean_audio: bool = False


class GenerateSrtRequest(TranscribeOptions):
    """
    Options for `/video/generate_srt`

    Inherits the curated transcription options unchanged
    """


class ConvertVideoRequest(BaseModel):
    """
    Options for `/video/convert_to_mp4`

    Args:
        resolution (str): Target canvas `WxH`
        target_bitrate (str): Target video bitrate
    """

    resolution: str = "1280x720"
    target_bitrate: str = "2500k"
