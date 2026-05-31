"""
Defines deterministic constants and built-in default values for the server

abstract: Configuration Split
    - Path constants derive from `platformdirs` (appname + version) and are
      deterministic, so they're safe to evaluate at import

    - Environment-dependent configuration is resolved lazily by
      `mirumoji.server.config.get_settings` so that a `.env` loaded at
      startup is respected

warning: Directory Creation
    `HOST_DATA_DIRS` is created with `ensure_exists=False`, so none of the
    `HOST_*` directories exist merely because this module was imported

Attributes:
    HOST_DATA_DIRS (PlatformDirs): Platform-specific application directories
        (`appname="mirumoji"`, versioned), with `ensure_exists=False`
    HOST_MEDIA_PATH (Path): Media root, `user_data_path / "media_files"`
        (not auto-created)
    HOST_DB_PATH (Path): SQLite Database file, `user_data_path / "mirumoji.db"`
        (parent not auto-created)
    HOST_LOG_PATH (Path): Log directory, `user_log_dir` (not auto-created)
    DB_URL (str): Async SQLAlchemy database URL built from `HOST_DB_PATH`
    DEFAULT_SRT_SYS_MSG (str): Built-in default system message for SRT-fixing
    DEFAULT_BREAKDOWN_SYS_MSG (str): Built-in default system message for
        word-nuance breakdowns
"""

from pathlib import Path

from platformdirs import PlatformDirs

from .. import __version__

# --- File Management ---

HOST_DATA_DIRS = PlatformDirs(
    appname="mirumoji",
    appauthor=False,
    version=__version__,
    ensure_exists=False,
)

HOST_MEDIA_PATH: Path = HOST_DATA_DIRS.user_data_path / "media_files"

HOST_DB_PATH: Path = HOST_DATA_DIRS.user_data_path / "mirumoji.db"

HOST_LOG_PATH: Path = HOST_DATA_DIRS.user_log_path

# --- Database ---

DB_URL = f"sqlite+aiosqlite:///{HOST_DB_PATH}"

# --- Built-in default LLM system messages ---
# Resolved (with env overrides) by config.get_settings

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
