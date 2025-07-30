/**
 * @packageDocumentation This file contains the tokenizer for the application.
 */

import * as kuromoji from "kuromoji";
export type IpadicFeatures = kuromoji.IpadicFeatures;
export type KuromojiTokenizer = kuromoji.Tokenizer<IpadicFeatures>;

let tokPromise: Promise<KuromojiTokenizer> | null = null;

let viteBaseUrl = import.meta.env.BASE_URL;
// If URL isn't default `/` format it to `BASE_URL/`
if (viteBaseUrl !== "/" && !viteBaseUrl.endsWith("/")) {
    viteBaseUrl += "/";
}

// dict files folder in `public` directory served at website root
const DICT_PATH = viteBaseUrl + "dict/";

/**
 * Gets the Kurmoji tokenizer with the `DICT_PATH` constant set
 *
 * @returns {Promise<KuromojiTokenizer>} A promise that resolves to the tokenizer.
 */
export function getTokenizer() {
    if (tokPromise) return tokPromise;

    tokPromise = new Promise((resolve, reject) => {
        kuromoji
            .builder({
                dicPath: DICT_PATH,
            })
            .build((err, tokenizer) => {
                if (err) reject(err);
                else resolve(tokenizer);
            });
    });
    return tokPromise;
}
