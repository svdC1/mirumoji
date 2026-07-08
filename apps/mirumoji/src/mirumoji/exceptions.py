"""
Defines the package's exception hierarchy

Server-side domain exceptions carry their own HTTP contract (`http_status` and
a stable machine-readable `code`) plus an optional structured `details`
payload. A single FastAPI exception handler reads those attributes and renders
the nested error envelope, so transport concerns never leak into domain code
"""

from typing import Any, ClassVar

# --- Base Exceptions ---


class MirumojiError(Exception):
    """
    The base exception for all errors raised by `mirumoji`
    """


class MirumojiServerError(MirumojiError):
    """
    The base exception for all errors raised by mirumoji's backend server

    Attributes:
      http_status (int): HTTP status code the API should return for this error
      code (str): Stable machine-readable identifier for the frontend
      details (dict | None): Optional structured context about the failure
    """

    http_status: ClassVar[int] = 500
    code: ClassVar[str] = "ServerError"

    def __init__(
        self, message: str, *, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.details = details


class MirumojiLauncherError(MirumojiError):
    """
    The base exception for all errors raised by mirumoji's launcher

    Covers the shared launcher core (`LauncherError`) plus
    the CLI and GUI front-ends, so a caller can catch every launcher failure
    with a single package-level type
    """


# --- Server Exceptions ---


# --- Missing Dependency Exceptions ---


class MissingFFmpegError(MirumojiServerError):
    """
    Raised when the system's `FFMPEG` executable couldn't be located

    Indicates that either `FFMPEG` is not installed, or `shutil.which` failed
    to locate the executable
    """

    http_status: ClassVar[int] = 503
    code: ClassVar[str] = "MissingFFmpeg"


class MissingFFprobeError(MirumojiServerError):
    """
    Raised when the system's `FFProbe` executable couldn't be located

    Indicates that either `FFMPEG` is not installed, or `shutil.which` failed
    to locate the executable
    """

    http_status: ClassVar[int] = 503
    code: ClassVar[str] = "MissingFFprobe"


# ---


class FFmpegError(MirumojiServerError):
    """
    Raised when a subprocess using `FFMPEG` returns a non-zero exit code

    Indicates a failure when executing an `FFMPEG` command. This exception is
    always raised from a `subprocess.CalledProcessError`, which can be
    inspected by accessing this exception's `__cause__` attribute
    """

    http_status: ClassVar[int] = 422
    code: ClassVar[str] = "FFmpeg"


class FugashiError(MirumojiServerError):
    """
    Raised when an error occurred while trying to use `fugashi.Tagger` to
    tokenize Japanese senteces

    Indicates that there's a problem with the system's `fugashi` installation,
    an operation using `fugashi` has failed, the required `unidic`
    dictionary is not present and needs to be downloaded, or that the required
    MeCab is not installed in the system
    """

    http_status: ClassVar[int] = 503
    code: ClassVar[str] = "Fugashi"


class KotobaseError(MirumojiServerError):
    """
    Raised when an error occurred while trying to extract dictionary
    data from `kotobase`

    Indicates that there's a problem with the system's `kotobase`
    installation, an operation using `kotobase` has failed, or that the
    required database is not present and needs to be downloaded
    """

    http_status: ClassVar[int] = 503
    code: ClassVar[str] = "Kotobase"


# --- LLM Exceptions ---


class LLMError(MirumojiServerError):
    """
    Base exception for failures in the provider-agnostic LLM layer
    """

    http_status: ClassVar[int] = 502
    code: ClassVar[str] = "LLM"


class InvalidModelStringError(LLMError):
    """
    Raised when a model selector string cannot be parsed

    Model selectors must follow the `"provider:model"` convention (e.g.
    `"openai:gpt-4.1-mini"`). Indicates a malformed selector or an unknown
    provider prefix
    """

    http_status: ClassVar[int] = 400
    code: ClassVar[str] = "InvalidModelString"


class LLMProviderUnavailableError(LLMError):
    """
    Raised when the requested LLM provider is not usable in this deployment

    Indicates that the provider's SDK isn't installed, or that the required
    API key / base URL isn't configured in the environment.
    """

    http_status: ClassVar[int] = 400
    code: ClassVar[str] = "LLMProviderUnavailable"


class LLMRequestError(LLMError):
    """
    Raised when a request to an LLM provider fails

    Indicates an upstream failure (network error, provider-side error, or an
    unexpected response) while completing or streaming a chat request
    """

    http_status: ClassVar[int] = 502
    code: ClassVar[str] = "LLMRequest"


# --- Transcription Exceptions ---


class TranscriptionError(MirumojiServerError):
    """
    Raised when an audio/video transcription operation fails
    """

    http_status: ClassVar[int] = 502
    code: ClassVar[str] = "Transcription"


class WhisperUnavailableError(MirumojiServerError):
    """
    Raised when local Whisper transcription is requested but unavailable

    Indicates that `faster-whisper` isn't installed (the `whisper-local`
    extra), or that the model failed to load
    """

    http_status: ClassVar[int] = 503
    code: ClassVar[str] = "WhisperUnavailable"


class ModalError(MirumojiServerError):
    """
    Raised when a Modal remote job fails

    Indicates an error running or communicating with a Modal function (e.g.
    transcription or video conversion offloaded to Modal's GPU containers)
    """

    http_status: ClassVar[int] = 502
    code: ClassVar[str] = "Modal"


class ModalVolumeError(ModalError):
    """
    Raised when streaming a file in or out of a `Modal Volume` fails

    Indicates that an error happened while uploading or downloading a file
    from the per-job ephemeral modal volume, either locally or inside a
    `Modal Container`
    """

    http_status: ClassVar[int] = 502
    code: ClassVar[str] = "ModalVolume"


# --- Media Exceptions ---


class MediaError(MirumojiServerError):
    """
    Base exception for failures handling media files
    """

    http_status: ClassVar[int] = 500
    code: ClassVar[str] = "Media"


class MediaNotFoundError(MediaError):
    """
    Raised when a requested media file does not exist
    """

    http_status: ClassVar[int] = 404
    code: ClassVar[str] = "MediaNotFound"


class UploadError(MediaError):
    """
    Raised when saving a streamed upload fails

    Indicates the client upload could not be written to storage (e.g. a
    broken stream or a missing required header)
    """

    http_status: ClassVar[int] = 400
    code: ClassVar[str] = "Upload"


class InvalidMediaPathError(MediaError):
    """
    Raised when a requested path is invalid for, or escapes, the media
    directory

    Guards against path traversal and malformed relative paths
    """

    http_status: ClassVar[int] = 400
    code: ClassVar[str] = "InvalidMediaPath"


class StorageError(MediaError):
    """
    Raised when a media filesystem operation fails

    Covers move, copy, delete, and directory-creation failures within the
    media directory
    """

    http_status: ClassVar[int] = 500
    code: ClassVar[str] = "Storage"


# --- Database Exceptions ---


class DatabaseError(MirumojiServerError):
    """
    Raised when a database operation fails unexpectedly
    """

    http_status: ClassVar[int] = 500
    code: ClassVar[str] = "Database"


class RecordNotFoundError(DatabaseError):
    """
    Raised when a requested database record does not exist
    """

    http_status: ClassVar[int] = 404
    code: ClassVar[str] = "RecordNotFound"
