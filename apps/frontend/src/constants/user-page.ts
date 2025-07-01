/**
 * @fileoverview This file contains constants for the user page.
 */

export const tabs = [
    { id: "profile", label: "Profile" },
    { id: "files", label: "Files" },
    { id: "transcripts", label: "Transcripts" },
    { id: "gpt-template", label: "GPT Template" },
];

export const API_BASE = "api/";
export const defaultSysMsg = `You are a Japanese language API that explains the specific nuance of specified word(s) in a Japanese sentence.\r\n\r\nRespond concisely in no more than 100 words.\r\n\r\nSpecified word(s) MUST be in Japanese\r\n\r\nAll other explanation text MUST be in English\r\n\r\nIn your response:\r\n\r\nDO NOT OUTPUT the language name or the word \'nuance\';\r\n\r\nDO NOT OUTPUT the context sentence ;\r\n\r\nDO NOT OUTPUT romaji/furigana or any notes on pronunciation;\r\n\r\nConclude with the specific nuance within the context sentence.`;
export const defaultPrompt = `{sentence}. Explain usage of word : {focus}\r\n`;
