// src/utils/dict.ts
export type DictEntry = {
    readings: string[]; // all kana forms
    meanings: string[]; // all English glosses
};

type RawEntry = {
    kanji: { text: string }[];
    kana: { text: string }[];
    sense: Array<{
        gloss: Array<{ text: string }>;
    }>;
};

type RawDict = {
    words: RawEntry[];
};

let _dictData: RawDict | null = null;
let _lookupMap: Map<string, DictEntry> | null = null;

/** Load and cache the raw JSON from public/jmdict.json */
async function loadRawDict(): Promise<RawDict> {
    if (_dictData) return _dictData;
    const res = await fetch("/jmdict.json");
    if (!res.ok) throw new Error(`Failed to load dictionary: ${res.status}`);
    _dictData = (await res.json()) as RawDict;
    console.log(`📚 Loaded jmdict.json with ${_dictData.words.length} entries`);
    return _dictData;
}

/** Build a Map from every surface form → { readings; meanings } */
async function buildLookup(): Promise<Map<string, DictEntry>> {
    if (_lookupMap) return _lookupMap;
    const { words } = await loadRawDict();
    const m = new Map<string, DictEntry>();

    for (const entry of words) {
        // gather all kana readings
        const readings = entry.kana.map((k) => k.text);

        // gather all English glosses
        const meanings = entry.sense.flatMap((s) => s.gloss.map((g) => g.text));

        const dictObj: DictEntry = { readings, meanings };

        // index under each kanji form
        for (const k of entry.kanji) {
            m.set(k.text, dictObj);
        }

        // index under each kana form
        for (const k of entry.kana) {
            m.set(k.text, dictObj);
        }
    }

    _lookupMap = m;
    return m;
}

/**
 * Look up a word (kanji or kana). Returns null if not found.
 */
export async function lookupDict(word: string): Promise<DictEntry | null> {
    try {
        const map = await buildLookup();
        const key = word.trim();
        const entry = map.get(key) ?? null;
        console.log(`🔍 lookupDict("${key}") →`, entry);
        return entry;
    } catch (e) {
        console.error("lookupDict error:", e);
        return null;
    }
}
