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

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, Field

from .jpdict import BundleMode

# --- Dictionary Requests ---


class TokenizeBatchRequest(BaseModel):
    """
    Request for the batch tokenize endpoint (`POST /dict/tokenize`)

    Args:
        sentences (list[str]): The sentences to tokenize, in order
        mode (BundleMode): How aggressively to group tokens into words
    """

    sentences: list[str]
    mode: BundleMode = BundleMode.grammar


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
        srt_sys_msg (str): Subtitle-fix system message (empty = server default)
        srt_model (str): Subtitle-fix model override (empty = use `model`)
    """

    sys_msg: str
    prompt: str
    model: str
    srt_sys_msg: str = ""
    srt_model: str = ""


class SaveSubtitlesRequest(BaseModel):
    """
    Request for persisting SRT content to the active profile
    (`POST /profiles/subtitles`)

    abstract: Replace vs Create
        - When `file_id` references an existing SRT file owned by the profile,
          that file's content is overwritten in place (same id / path)

        - Otherwise a new SRT file is created under the profile

    Args:
        content (str): The SRT content to store
        file_id (str | None): Existing SRT file id to overwrite, if any
        name (str | None): Optional file name for a newly created file
    """

    content: str
    file_id: str | None = None
    name: str | None = None


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


# --- Job Submission Requests ---


class SubmitJobBase(BaseModel):
    """
    Shared fields for every job submission request

    Args:
        file_id (str): The profile file that the job operates on
    """

    file_id: str


class GenerateSrtJobRequest(SubmitJobBase):
    """
    Submission for a `generate_srt` job

    Args:
        type (Literal['generate_srt']): The operation discriminator
        opts (GenerateSrtRequest): Curated transcription options
    """

    type: Literal["generate_srt"]
    opts: GenerateSrtRequest = Field(default_factory=GenerateSrtRequest)

    def to_params(self) -> dict[str, Any]:
        """
        Builds the persisted job's `params` attribute

        Returns:
            The file reference and normalised transcription options
        """
        return {
            "file_id": self.file_id,
            "opts": self.opts.model_dump(exclude_none=True),
        }


class TranscribeJobRequest(SubmitJobBase):
    """
    Submission for a `transcribe` job

    Args:
        type (Literal['transcribe']): The operation discriminator
        opts (TranscribeAudioRequest): `clean_audio` + curated transcription
            options
    """

    type: Literal["transcribe"]
    opts: TranscribeAudioRequest = Field(
        default_factory=TranscribeAudioRequest,
    )

    def to_params(self) -> dict[str, Any]:
        """
        Builds the persisted job's `params` attribute

        Returns:
            The file reference and normalised transcription options
        """
        return {
            "file_id": self.file_id,
            "opts": self.opts.model_dump(exclude_none=True),
        }


class ConvertJobRequest(SubmitJobBase):
    """
    Submission for a `convert` job

    Args:
        type (Literal['convert']): The operation discriminator
        opts (ConvertVideoRequest): Conversion options
    """

    type: Literal["convert"]
    opts: ConvertVideoRequest = Field(default_factory=ConvertVideoRequest)

    def to_params(self) -> dict[str, Any]:
        """
        Builds the persisted job's stored `params`

        Returns:
            The file reference and normalised conversion options
        """
        return {
            "file_id": self.file_id,
            "opts": self.opts.model_dump(exclude_none=True),
        }


class FixSrtJobRequest(SubmitJobBase):
    """
    Submission for a `fix_srt` job

    Args:
        type (Literal): The operation discriminator
        model (str): LLM model selector in `provider:model` form
        sys_msg (str | None): Optional LLM system message
    """

    type: Literal["fix_srt"]
    model: str
    sys_msg: str | None = None

    def to_params(self) -> dict[str, Any]:
        """
        Builds the persisted job's `params` attribute

        Returns:
            The file reference, model selector, and optional system message
        """
        return {
            "file_id": self.file_id,
            "model": self.model,
            "sys_msg": self.sys_msg,
        }


SubmitJobRequest: TypeAlias = Annotated[
    GenerateSrtJobRequest
    | TranscribeJobRequest
    | ConvertJobRequest
    | FixSrtJobRequest,
    Field(discriminator="type"),
]
"""
The body of a `POST /jobs` request

A discriminated union keyed by a persisted job's `type` attribute, so that
each operation's `opts` are validated against their own model
"""
