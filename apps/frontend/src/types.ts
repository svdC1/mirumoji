// src/types.ts
/* UserPage*/
export interface GptTemplate {
    id: string;
    sysMsg: string;
    prompt: string;
}

export type ProfileFile = {
    id: string;
    file_name: string;
    get_url: string;
    file_type: string;
};

export type ProfileTranscript = {
    id: string;
    original_file_name?: string;
    transcript: string;
    gpt_explanation?: string;
    get_url: string;
};
/* SettingsDrawer*/
export interface GenerateSrtResponse {
    srt_content: string;
}

export interface ConvertVideoResponse {
    converted_video_url: string;
}
/* WordDialog*/
export interface SaveClipResponse {
    success: boolean;
    message: string;
    clip_id?: string;
}

/* SavedPage*/
export type Clip = {
    id: string;
    get_url: string;
    breakdown_response: string;
    sentence_preview?: string;
    gpt_explanation_preview?: string;
};

export interface BreakdownFocus {
    word: string;
    reading: string;
    meanings: string[];
    jlpt?: string;
    examples?: any[];
}

export interface BreakdownData {
    sentence: string;
    focus: BreakdownFocus;
    tokens: any[];
    gpt_explanation: string;
}

export interface AnkiExportResponse {
    anki_deck_url: string;
}
