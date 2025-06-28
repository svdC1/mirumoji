import { apiFetch } from "./api";
import useSWR from "swr";
import { toast } from "react-hot-toast";

export interface WordSense {
    order: number;
    pos: string;
    gloss: string;
}

export interface JMEntry {
    rank: number;
    kana: string[];
    kanji: string[];
    senses: WordSense[];
}

export interface JMNEntry {
    kana: string[];
    kanji: string[];
    translation_type: string;
    gloss: string[];
}

export interface KanjiInfo {
    literal: string;
    grade?: number;
    stroke_count: number;
    meanings: string[];
    onyomi: string[];
    kunyomi: string[];
    jlpt_kanjidic?: number;
    jlpt_tanos?: number;
}
export type DictLookup = {
    word: string;
    jmentries: JMEntry[];
    jmnentries: JMNEntry[];
    kanji: KanjiInfo[];
    meanings: string[];
    jlpt: string;
    examples: string[];
};

export async function apiWordQuery(word: string): Promise<DictLookup> {
    const result = apiFetch<DictLookup>(`/dict/word?word=${word}`, {
        method: "GET",
    });
    return result;
}
