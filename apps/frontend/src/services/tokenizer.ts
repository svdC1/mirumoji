/**
 * @fileoverview This file contains the tokenizer for the application.
 */

import * as kuromoji from "kuromoji";
export type IpadicFeatures = kuromoji.IpadicFeatures;
export type KuromojiTokenizer = kuromoji.Tokenizer<IpadicFeatures>;

let tokPromise: Promise<KuromojiTokenizer> | null = null;

let viteBaseUrl = import.meta.env.BASE_URL;
if (viteBaseUrl !== "/" && !viteBaseUrl.endsWith("/")) {
    viteBaseUrl += "/";
}

// If viteBaseUrl is just '/', dicPath should be 'dict/'.
// Otherwise, it should be '/repo_name/dict/'.

const DICT_PATH = viteBaseUrl + "dict/";

/**
 * Gets the tokenizer.
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
