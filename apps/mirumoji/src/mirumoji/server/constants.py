"""
Defines deterministic constants and built-in default values for the server

abstract: Configuration Split
    Environment-dependent configuration is resolved lazily by
    `mirumoji.server.config.get_settings` so that a `.env` loaded at
    startup is respected

Attributes:
    DB_URL (str): Async SQLAlchemy database URL built from `HOST_DB_PATH`
    DEFAULT_SRT_SYS_MSG (str): Built-in default system message for SRT-fixing
    DEFAULT_BREAKDOWN_SYS_MSG (str): Built-in default system message for
        word-nuance breakdowns
"""

from ..paths import HOST_DB_PATH

# --- Database ---

DB_URL = f"sqlite+aiosqlite:///{HOST_DB_PATH}"

# --- Built-In Default LLM System Messages ---

DEFAULT_SRT_SYS_MSG = (
    "You are an expert subtitle editor for Japanese anime.\n"
    "You understand:\n"
    "  - Conversational Japanese, character names, "
    "honorifics onomatopoeia and scene-specific slang.\n"
    "  - How to pick the correct Kanji/Kana from phonetic "
    "transcriptions based on context.\n"
    "  - Natural sentence flow and typical timing for "
    "subtitles.\n"
    "Your job is to **clean only the text** of each SRT cue:\n"
    "  - Fix mis-recognized Kanji or Kana.\n"
    "  - Merge cues that split a single sentence "
    "(new cue's start = earlier, end = later).\n"
    "  - Remove any pure gibberish or repeated song-lyric "
    "artifacts.\n  - "
    "Insert correct punctuation (。？！、) and adjust spacing.\n\n"  # noqa: RUF001
    "**You must not**:\n  - Change any start/end timestamps.\n  - Renumber "
    "beyond simple sequential order.\n  - Add or remove cues "
    "(only merge as above).\n  - Add any commentary or explanations.\n\n"
    "Output **only** the cleaned `.srt` file content."
)

DEFAULT_BREAKDOWN_SYS_MSG = (
    "You are a Japanese language API that explains the specific nuance "
    "of specified word(s) in a Japanese sentence.\n"
    "Respond concisely in no more than 100 words.\n"
    "Specified word(s) MUST be in Japanese\n"
    "All other explanation text MUST be in English\n"
    "In your response:\n"
    "  DO NOT OUTPUT the language name or the word 'nuance';\n"
    "  DO NOT OUTPUT the context sentence ;\n"
    "  DO NOT OUTPUT romaji/furigana or any notes on pronunciation;\n"
    "  Conclude with the specific nuance within the context sentence."
)

MAX_LLM_CONCURRENCY = 4
"""
Defines how many LLM requests should be executed simultaneously when
requesting an `SRT Fix` for a batch of files
"""

# --- Local Whisper Model Download ---

MODEL_DOWNLOAD_RETRIES = 4
"""
How many times to attempt loading the local Whisper model before giving up

The first load pulls the weights from the Hugging Face Hub, so transient
network failures are retried (the partial download resumes between attempts)
"""

MODEL_DOWNLOAD_BACKOFF_BASE = 2.0
"""
Base number of seconds for the exponential backoff between Whisper model
download retries
"""

# --- FFMPEG Conversion ---

DEFAULT_CONVERSION_PRESET = "balanced"
"""
The conversion preset used when a request does not specify one

Names a key of `CONVERSION_PRESETS`
"""

CONVERSION_PRESETS: dict[str, dict[str, tuple[str, str]]] = {
    "performance": {
        "x264": ("veryfast", "26"),
        "nvenc": ("p2", "30"),
    },
    "balanced": {
        "x264": ("medium", "23"),
        "nvenc": ("p4", "26"),
    },
    "quality": {
        "x264": ("slow", "20"),
        "nvenc": ("p6", "22"),
    },
}
"""
FFmpeg encoder arguments used when converting video to MP4

A dictionary containing bundles of ffmpeg encoder arguments keyed by
the name of a specific preset

info: Format
    Each value is `(speed, quality)` for one encoder
    - libx264    -> (`-preset`, `-crf`)
    - h264_nvenc -> (`-preset`, `-cq`)

abstract: `performance`
    - Prioritises conversion speed over output quality
    - The fastest encoder presets paired with a lower quality target, for when
      throughput matters more than fidelity

abstract: `balanced`
    - Balances conversion speed with output quality
    - The default, with mid-range encoder presets and a moderate quality target
      that suits most playback

abstract: `quality`
    - Prioritises output quality
    - The slowest encoder presets paired with a higher quality target, for when
      fidelity matters more than encode time

`resolution` and `target_bitrate` options stay separate (output geometry and a
rate ceiling), so a preset only trades encode speed against quality
"""
