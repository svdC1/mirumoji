/**
 * @packageDocumentation Presentational components for dictionary data (JMdict /
 * JMnedict / KANJIDIC entries, examples), shared by the WordDialog lookup and
 * the Dictionary page. Example sentences are tokenized into clickable furigana.
 */

import { useEffect, useState } from "react";
import { apiTokenizeBatch } from "@/shared/dict/api";
import { Badge, cn } from "@/shared/ui";
import TokenizedText from "./TokenizedText";
import type { JMEntry, JMNEntry, JapaneseWord, KanjiInfo, KotobaseData } from "@/shared/dict/types";

const POS_CHIP = "rounded bg-ink/10 px-1.5 py-0.5 text-2xs text-ink-muted";

/**
 * Displays a standard JMdict entry: the written/read forms + numbered senses,
 * each tagged with its part of speech.
 *
 * @param {{ entry: JMEntry; isLast: boolean }} props The entry + last-row flag.
 * @returns {JSX.Element} The rendered entry.
 */
export const JmdictEntryDisplay = ({ entry, isLast }: { entry: JMEntry; isLast: boolean }) => {
    const headword = entry.kanji.length > 0 ? entry.kanji.join("、") : entry.kana.join("、");
    return (
        <div className={cn("py-3", !isLast && "border-b border-ink/10")}>
            <div className="flex flex-wrap items-baseline gap-x-2.5">
                <h3 lang="ja" className="font-display text-xl font-semibold text-ink">
                    {headword}
                </h3>
                {entry.kanji.length > 0 && entry.kana.length > 0 && (
                    <span lang="ja" className="text-ink-muted">
                        {entry.kana.join("、")}
                    </span>
                )}
            </div>
            <ol className="mt-2 space-y-2">
                {entry.senses.map((sense, i) => (
                    <li key={i} className="flex gap-2 text-sm leading-relaxed">
                        <span className="select-none pt-0.5 text-ink-faint">{i + 1}.</span>
                        <div>
                            {sense.pos && <span className={cn(POS_CHIP, "mr-2")}>{sense.pos}</span>}
                            <span className="text-ink">{sense.gloss}</span>
                        </div>
                    </li>
                ))}
            </ol>
        </div>
    );
};

/**
 * Displays a JMnedict (proper noun) entry.
 *
 * @param {{ entry: JMNEntry; isLast: boolean }} props The entry + last-row flag.
 * @returns {JSX.Element} The rendered entry.
 */
export const JmnedictEntryDisplay = ({ entry, isLast }: { entry: JMNEntry; isLast: boolean }) => {
    const headword = entry.kanji.length > 0 ? entry.kanji.join("、") : entry.kana.join("、");
    return (
        <div className={cn("py-3", !isLast && "border-b border-ink/10")}>
            <div className="flex flex-wrap items-baseline gap-x-2.5">
                <h3 lang="ja" className="font-display text-xl font-semibold text-ink">
                    {headword}
                </h3>
                {entry.kanji.length > 0 && entry.kana.length > 0 && (
                    <span lang="ja" className="text-ink-muted">
                        {entry.kana.join("、")}
                    </span>
                )}
                {entry.translation_type && (
                    <span className={cn(POS_CHIP, "ml-auto")}>{entry.translation_type}</span>
                )}
            </div>
            <p className="mt-1.5 text-sm text-ink">{entry.gloss.join("; ")}</p>
        </div>
    );
};

/**
 * Displays detailed info for a single Kanji: the glyph alongside its stats
 * (strokes / grade / JLPT), meanings, and on/kun readings.
 *
 * @param {{ kanjiInfo: KanjiInfo; isLast: boolean }} props The kanji + last-row flag.
 * @returns {JSX.Element} The rendered kanji info.
 */
export const KanjiInfoDisplay = ({
    kanjiInfo,
    isLast,
}: {
    kanjiInfo: KanjiInfo;
    isLast: boolean;
}) => {
    const jlpt = kanjiInfo.jlpt_tanos || kanjiInfo.jlpt_kanjidic;
    return (
        <div className={cn("flex gap-4 py-3", !isLast && "border-b border-ink/10")}>
            <div lang="ja" className="font-jp text-5xl leading-none text-ink">
                {kanjiInfo.literal}
            </div>
            <div className="flex-1 space-y-2 text-sm">
                <div className="flex flex-wrap gap-1.5">
                    {kanjiInfo.stroke_count != null && (
                        <Badge>{kanjiInfo.stroke_count} Strokes</Badge>
                    )}
                    {kanjiInfo.grade != null && <Badge>Grade {kanjiInfo.grade}</Badge>}
                    {jlpt != null && <Badge tone="accent">N{jlpt}</Badge>}
                </div>
                {kanjiInfo.meanings.length > 0 && (
                    <p className="text-ink">{kanjiInfo.meanings.join(", ")}</p>
                )}
                {kanjiInfo.onyomi.length > 0 && (
                    <p>
                        <span className="text-2xs uppercase tracking-wide text-ink-faint">On </span>
                        <span lang="ja" className="text-ink-muted">
                            {kanjiInfo.onyomi.join("、")}
                        </span>
                    </p>
                )}
                {kanjiInfo.kunyomi.length > 0 && (
                    <p>
                        <span className="text-2xs uppercase tracking-wide text-ink-faint">
                            Kun{" "}
                        </span>
                        <span lang="ja" className="text-ink-muted">
                            {kanjiInfo.kunyomi.join("、")}
                        </span>
                    </p>
                )}
            </div>
        </div>
    );
};

/**
 * Renders example sentences as clickable, furigana-annotated tokens
 * (batch-tokenized on the server). Falls back to plain text while loading.
 *
 * @param {object} props The examples + a per-word click handler.
 * @returns {JSX.Element} The rendered examples.
 */
export const TokenizedExamples = ({
    examples,
    onWordClick,
}: {
    examples: string[];
    onWordClick: (sentence: string, word: string) => void;
}) => {
    const [wordsList, setWordsList] = useState<JapaneseWord[][] | null>(null);
    const joined = examples.join(" ");

    useEffect(() => {
        let cancelled = false;
        setWordsList(null);
        apiTokenizeBatch(examples)
            .then((r) => !cancelled && setWordsList(r))
            .catch(() => !cancelled && setWordsList(null));
        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [joined]);

    return (
        <ul className="space-y-2">
            {examples.map((ex, i) => (
                <li
                    key={i}
                    className="rounded-control bg-surface-2 px-3 py-2.5 text-lg leading-relaxed"
                >
                    {wordsList && wordsList[i] && wordsList[i].length > 0 ? (
                        <TokenizedText
                            words={wordsList[i]}
                            sentence={ex}
                            showFurigana
                            onWordClick={onWordClick}
                        />
                    ) : (
                        <span lang="ja" className="text-ink-muted">
                            {ex}
                        </span>
                    )}
                </li>
            ))}
        </ul>
    );
};

/**
 * A comprehensive, tabbed card showing JMdict / JMnedict / Kanji / Examples for
 * a looked-up word.
 *
 * @param {object} props The lookup result split into its lists + the word.
 * @returns {JSX.Element} The rendered card.
 */
export const ComprehensiveEntryCard = ({
    word,
    jmdictEntries,
    jmnedictEntries,
    kanjiInfo,
    examples,
    onWordSelect,
}: {
    word: string;
    jmdictEntries: JMEntry[];
    jmnedictEntries: JMNEntry[];
    kanjiInfo: KanjiInfo[];
    examples: string[];
    onWordSelect?: (word: string) => void;
}) => {
    const reading = jmdictEntries[0]?.kana[0] ?? jmnedictEntries[0]?.kana[0] ?? "";
    const tabs: string[] = [];
    if (jmdictEntries.length > 0) tabs.push("Definition");
    if (jmnedictEntries.length > 0) tabs.push("Proper Noun");
    if (kanjiInfo.length > 0) tabs.push("Kanji");
    if (examples.length > 0) tabs.push("Examples");

    const [activeTab, setActiveTab] = useState(tabs[0]);
    if (!tabs.includes(activeTab)) {
        setActiveTab(tabs[0]);
    }

    return (
        <div className="mx-auto w-full max-w-2xl rounded-card border border-ink/10 bg-surface p-4 text-ink shadow-soft sm:p-6">
            <div className="mb-4 flex flex-col items-center gap-1 text-center">
                <h2 lang="ja" className="font-display text-4xl font-bold">
                    {word}
                </h2>
                {reading && (
                    <p lang="ja" className="text-lg italic text-ink-muted">
                        {reading}
                    </p>
                )}
            </div>

            <div className="mb-4 border-b border-ink/10">
                <nav className="-mb-px flex justify-center space-x-4" aria-label="Tabs">
                    {tabs.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`${
                                activeTab === tab
                                    ? "border-shu text-shu"
                                    : "border-transparent text-ink-faint hover:border-ink/20 hover:text-ink-muted"
                            } whitespace-nowrap border-b-2 px-1 py-2 text-sm font-medium transition-colors`}
                        >
                            {tab}
                        </button>
                    ))}
                </nav>
            </div>

            <div className="mt-4 max-h-[60vh] overflow-y-auto px-2">
                {activeTab === "Definition" &&
                    jmdictEntries.map((entry, i) => (
                        <JmdictEntryDisplay
                            key={i}
                            entry={entry}
                            isLast={i === jmdictEntries.length - 1}
                        />
                    ))}
                {activeTab === "Proper Noun" &&
                    jmnedictEntries.map((entry, i) => (
                        <JmnedictEntryDisplay
                            key={i}
                            entry={entry}
                            isLast={i === jmnedictEntries.length - 1}
                        />
                    ))}
                {activeTab === "Kanji" &&
                    kanjiInfo.map((info, i) => (
                        <KanjiInfoDisplay
                            key={i}
                            kanjiInfo={info}
                            isLast={i === kanjiInfo.length - 1}
                        />
                    ))}
                {activeTab === "Examples" && (
                    <TokenizedExamples
                        examples={examples}
                        onWordClick={(_, w) => onWordSelect?.(w)}
                    />
                )}
            </div>
        </div>
    );
};

/**
 * Tabbed results for a wildcard search, with clickable rows.
 *
 * @param {{ results: KotobaseData; onWordSelect: (word: string) => void }} props
 *     The wildcard results + a selection callback.
 * @returns {JSX.Element} The rendered results.
 */
export const WildcardResults = ({
    results,
    onWordSelect,
}: {
    results: KotobaseData;
    onWordSelect: (word: string) => void;
}) => {
    const tabs: string[] = [];
    if (results.jmentries.length > 0) tabs.push("Entries");
    if (results.jmnentries.length > 0) tabs.push("Proper Nouns");
    if (results.kanji.length > 0) tabs.push("Kanji");
    if (results.examples.length > 0) tabs.push("Examples");

    const [activeTab, setActiveTab] = useState(tabs[0] || "");

    return (
        <div className="mx-auto mt-6 max-w-4xl rounded-card border border-ink/10 bg-surface shadow-soft">
            <div className="border-b border-ink/10">
                <nav className="-mb-px flex justify-center space-x-4 px-4" aria-label="Tabs">
                    {tabs.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`${
                                activeTab === tab
                                    ? "border-shu text-shu"
                                    : "border-transparent text-ink-faint hover:border-ink/20 hover:text-ink-muted"
                            } whitespace-nowrap border-b-2 px-2 py-3 text-sm font-medium transition-colors`}
                        >
                            {tab}
                        </button>
                    ))}
                </nav>
            </div>
            <div className="h-96 overflow-y-auto p-4">
                {activeTab === "Entries" &&
                    results.jmentries.map((entry, i) => (
                        <JMEntryRow key={i} entry={entry} onSelect={onWordSelect} />
                    ))}
                {activeTab === "Proper Nouns" &&
                    results.jmnentries.map((entry, i) => (
                        <JMNEntryRow key={i} entry={entry} onSelect={onWordSelect} />
                    ))}
                {activeTab === "Kanji" &&
                    results.kanji.map((kanji, i) => (
                        <KanjiRow key={i} kanji={kanji} onSelect={onWordSelect} />
                    ))}
                {activeTab === "Examples" && (
                    <TokenizedExamples
                        examples={results.examples}
                        onWordClick={(_, w) => onWordSelect(w)}
                    />
                )}
            </div>
        </div>
    );
};

const ROW =
    "grid grid-cols-3 gap-4 items-center text-center py-2 px-3 rounded-control hover:bg-ink/5 cursor-pointer transition-colors";

/**
 * A clickable JMdict result row.
 *
 * @param {{ entry: JMEntry; onSelect: (word: string) => void }} props The entry + callback.
 * @returns {JSX.Element} The row.
 */
export const JMEntryRow = ({
    entry,
    onSelect,
}: {
    entry: JMEntry;
    onSelect: (word: string) => void;
}) => (
    <div onClick={() => onSelect(entry.kanji[0] || entry.kana[0])} className={ROW}>
        <p lang="ja" className="font-semibold text-ink">
            {entry.kanji.join("、")}
        </p>
        <p lang="ja" className="text-ink-muted">
            {entry.kana.join("、")}
        </p>
        <p className="text-sm text-ink-faint">{entry.senses.map((s) => s.pos).join(", ")}</p>
    </div>
);

/**
 * A clickable JMnedict result row.
 *
 * @param {{ entry: JMNEntry; onSelect: (word: string) => void }} props The entry + callback.
 * @returns {JSX.Element} The row.
 */
const JMNEntryRow = ({
    entry,
    onSelect,
}: {
    entry: JMNEntry;
    onSelect: (word: string) => void;
}) => (
    <div onClick={() => onSelect(entry.kanji[0] || entry.kana[0])} className={ROW}>
        <p lang="ja" className="font-semibold text-ink">
            {entry.kanji.join("、")}
        </p>
        <p lang="ja" className="text-ink-muted">
            {entry.kana.join("、")}
        </p>
        <p className="text-sm text-ink-faint">{entry.translation_type}</p>
    </div>
);

/**
 * A clickable Kanji result row.
 *
 * @param {{ kanji: KanjiInfo; onSelect: (word: string) => void }} props The kanji + callback.
 * @returns {JSX.Element} The row.
 */
export const KanjiRow = ({
    kanji,
    onSelect,
}: {
    kanji: KanjiInfo;
    onSelect: (word: string) => void;
}) => (
    <div onClick={() => onSelect(kanji.literal)} className={ROW}>
        <p lang="ja" className="col-span-1 text-lg font-bold text-ink">
            {kanji.literal}
        </p>
        <p className="col-span-2 text-sm text-ink-faint">{kanji.meanings.join(", ")}</p>
    </div>
);
