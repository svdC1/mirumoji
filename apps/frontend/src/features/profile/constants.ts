/**
 * @packageDocumentation Profile / dashboard constants — tab list + LLM template
 * defaults.
 */

export const tabs = [
    { id: "profile", label: "Profile" },
    { id: "files", label: "Files" },
    { id: "transcripts", label: "Transcripts" },
    { id: "clips", label: "Clips" },
    { id: "tasks", label: "Tasks" },
    { id: "llm-template", label: "LLM Template" },
    { id: "advanced", label: "Advanced" },
];

export const defaultSysMsg = `You are a Japanese language API that explains the specific nuance of specified word(s) in a Japanese sentence.\r\n\r\nRespond concisely in no more than 100 words.\r\n\r\nSpecified word(s) MUST be in Japanese\r\n\r\nAll other explanation text MUST be in English\r\n\r\nIn your response:\r\n\r\nDO NOT OUTPUT the language name or the word 'nuance';\r\n\r\nDO NOT OUTPUT the context sentence ;\r\n\r\nDO NOT OUTPUT romaji/furigana or any notes on pronunciation;\r\n\r\nConclude with the specific nuance within the context sentence.`;

export const defaultPrompt = `{sentence}. Explain usage of word : {focus}\r\n`;

/** Default model selector in `provider:model` form. */
export const defaultModel = "openai:gpt-4.1-mini";

/**
 * Default subtitle-fix system message (seeded into the Subtitle Fix sub-tab).
 * Mirrors the server's `DEFAULT_SRT_SYS_MSG` so the form shows what the backend
 * would use by default.
 */
export const defaultSrtSysMsg = `You are an expert subtitle editor for Japanese anime.
You understand:
  - Conversational Japanese, character names, honorifics onomatopoeia and scene-specific slang.
  - How to pick the correct Kanji/Kana from phonetic transcriptions based on context.
  - Natural sentence flow and typical timing for subtitles.
Your job is to **clean only the text** of each SRT cue:
  - Fix mis-recognized Kanji or Kana.
  - Merge cues that split a single sentence (new cue's start = earlier, end = later).
  - Remove any pure gibberish or repeated song-lyric artifacts.
  - Insert correct punctuation (。？！、) and adjust spacing.

**You must not**:
  - Change any start/end timestamps.
  - Renumber beyond simple sequential order.
  - Add or remove cues (only merge as above).
  - Add any commentary or explanations.

Output **only** the cleaned \`.srt\` file content.`;

/** Default subtitle-fix model (seeded into the Subtitle Fix sub-tab). */
export const defaultSrtModel = defaultModel;
