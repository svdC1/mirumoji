/**
 * @packageDocumentation Persists the Dictionary hub's recent lookups (words
 * and kanji) in localStorage, so the landing page can offer them back and the
 * hub keeps a sense of state between visits.
 */

/** One remembered lookup. */
export interface RecentLookup {
    kind: "word" | "kanji";
    value: string;
}

const KEY = "dictRecentLookups";
const LIMIT = 12;

/**
 * Reads the recent lookups, most recent first.
 *
 * @returns {RecentLookup[]} The remembered lookups (empty on parse failure).
 */
export function getRecentLookups(): RecentLookup[] {
    try {
        const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]");
        return Array.isArray(parsed) ? (parsed as RecentLookup[]) : [];
    } catch {
        return [];
    }
}

/**
 * Remembers a lookup, de-duplicated and capped to the most recent few.
 *
 * @param {RecentLookup} item The lookup to remember.
 */
export function pushRecentLookup(item: RecentLookup): void {
    const rest = getRecentLookups().filter(
        (r) => !(r.kind === item.kind && r.value === item.value)
    );
    try {
        localStorage.setItem(KEY, JSON.stringify([item, ...rest].slice(0, LIMIT)));
    } catch {
        // Storage full or unavailable: recents are a convenience, not state
    }
}
