/**
 * @packageDocumentation In-app dictionary route builders.
 *
 * The kanji/word value is carried in the query string, not a path segment, so
 * the URL path stays ASCII. A Modal-hosted deploy rejects any request whose URL
 * path contains non-ASCII bytes, including a hard reload/bookmark of an SPA
 * route, so a routed kanji or word page must never put Japanese in the path.
 */

/**
 * Builds the route to a word entry view.
 *
 * @param {string} term The word.
 * @returns {string} The `/dictionary/word` route with the word in the query.
 */
export function wordRoute(term: string): string {
    return `/dictionary/word?term=${encodeURIComponent(term)}`;
}

/**
 * Builds the route to a kanji detail view.
 *
 * @param {string} literal The kanji character.
 * @returns {string} The `/dictionary/kanji` route with the kanji in the query.
 */
export function kanjiRoute(literal: string): string {
    return `/dictionary/kanji?char=${encodeURIComponent(literal)}`;
}
