/**
 * @packageDocumentation A static glossary translating the Japanese
 * grammatical terms that UniDic morphology uses (parts of speech,
 * conjugation types and forms, word origins) into short English
 * descriptions, surfaced as tooltips in the grammar breakdown.
 */

/** Japanese grammar term -> short English description. */
const TERMS: Record<string, string> = {
    // Parts of speech (pos1)
    動詞: "Verb",
    名詞: "Noun",
    代名詞: "Pronoun",
    形容詞: "I-Adjective",
    形状詞: "Na-Adjective Stem",
    副詞: "Adverb",
    助詞: "Particle",
    助動詞: "Auxiliary (Tense / Politeness / Negation)",
    接続詞: "Conjunction",
    接頭辞: "Prefix",
    接尾辞: "Suffix",
    連体詞: "Adnominal (Modifies Nouns)",
    感動詞: "Interjection",
    記号: "Symbol",
    補助記号: "Punctuation / Supplementary Symbol",
    空白: "Whitespace",

    // Sub-categories (pos2-4)
    普通名詞: "Common Noun",
    固有名詞: "Proper Noun",
    数詞: "Numeral",
    非自立可能: "Can Act As A Helper (Bound) Word",
    格助詞: "Case Particle (Marks Grammatical Role)",
    係助詞: "Binding Particle (は / も Topic, Emphasis)",
    終助詞: "Sentence-Final Particle (ね / よ)",
    接続助詞: "Conjunctive Particle (Connecting て / けど)",
    副助詞: "Adverbial Particle (だけ / まで)",
    準体助詞: "Nominalizing Particle (の)",
    サ変可能: "Can Form A Suru Verb",
    形状詞可能: "Can Act As A Na-Adjective",
    副詞可能: "Can Act As An Adverb",
    助数詞可能: "Can Act As A Counter",
    人名: "Person Name",
    地名: "Place Name",
    一般: "General",

    // Conjugation types (cType families)
    五段: "Godan (U-Verb) Conjugation",
    上一段: "Kami-Ichidan (Ru-Verb) Conjugation",
    下一段: "Shimo-Ichidan (Ru-Verb) Conjugation",
    サ行変格: "Irregular Suru Conjugation",
    カ行変格: "Irregular Kuru Conjugation",
    文語: "Classical (Literary) Conjugation",

    // Conjugation forms (cForm families)
    終止形: "Terminal Form (Sentence-Ending)",
    連体形: "Attributive Form (Before Nouns)",
    連用形: "Continuative Form (Connects To What Follows)",
    未然形: "Irrealis Form (Before ない / う)",
    仮定形: "Hypothetical Form (Before ば)",
    命令形: "Imperative Form",
    意志推量形: "Volitional Form (Let's / Probably)",
    語幹: "Stem",

    // Word origins (goshu)
    和: "Native Japanese Word",
    漢: "Sino-Japanese Word (Chinese Origin)",
    外: "Foreign Loanword",
    混: "Mixed-Origin Word",
    固: "Proper Name",
};

/**
 * Looks up the English description of a Japanese grammatical term. Compound
 * UniDic values (e.g. `五段-マ行` or `助動詞-タ`) match on their leading
 * family before the first dash.
 *
 * @param {string} term The Japanese grammatical term.
 * @returns {string | undefined} The English description, if known.
 */
export function grammarTermEn(term: string): string | undefined {
    if (TERMS[term]) return TERMS[term];
    const family = term.split("-")[0];
    return TERMS[family];
}
