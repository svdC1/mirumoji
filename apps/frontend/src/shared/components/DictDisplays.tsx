/**
 * @packageDocumentation Presentational components for dictionary data (JMdict /
 * JMnedict / KANJIDIC entries, examples), shared by the WordDialog lookup and
 * the Dictionary page.
 */

import { useState } from "react";
import type { JMEntry, JMNEntry, KanjiInfo, KotobaseData } from "@/shared/dict/types";

/**
 * Displays a standard JMdict entry.
 *
 * @param {{ entry: JMEntry; isLast: boolean }} props The entry + last-row flag.
 * @returns {JSX.Element} The rendered entry.
 */
export const JmdictEntryDisplay = ({ entry, isLast }: { entry: JMEntry; isLast: boolean }) => (
    <div className={`py-2 ${!isLast ? "border-b border-ink/10" : ""}`}>
        <div className="flex items-center">
            <h3 lang="ja" className="mr-2 text-lg font-bold text-ink">
                {entry.kanji.join("、")}
            </h3>
            <p lang="ja" className="text-ink-muted">
                {entry.kana.join("、")}
            </p>
        </div>
        {entry.senses.map((sense, i) => (
            <div key={i} className="ml-4 mt-1">
                <p className="text-sm text-ink-faint">({sense.pos})</p>
                <p className="text-ink">
                    <span className="text-ink-faint">{i + 1}.</span> {sense.gloss}
                </p>
            </div>
        ))}
    </div>
);

/**
 * Displays an example sentence.
 *
 * @param {{ example: string; isLast: boolean }} props The example + last-row flag.
 * @returns {JSX.Element} The rendered example.
 */
export const ExampleDisplay = ({ example, isLast }: { example: string; isLast: boolean }) => (
    <div className={`py-2 ${!isLast ? "border-b border-ink/10" : ""}`}>
        <div className="ml-4 mt-1">
            <p lang="ja" className="text-center text-lg text-ink-muted">
                ({example})
            </p>
        </div>
    </div>
);

/**
 * Displays a JMnedict (proper noun) entry.
 *
 * @param {{ entry: JMNEntry; isLast: boolean }} props The entry + last-row flag.
 * @returns {JSX.Element} The rendered entry.
 */
export const JmnedictEntryDisplay = ({ entry, isLast }: { entry: JMNEntry; isLast: boolean }) => (
    <div className={`py-2 ${!isLast ? "border-b border-ink/10" : ""}`}>
        <div className="flex items-center">
            <h3 lang="ja" className="mr-2 text-lg font-bold text-ink">
                {entry.kanji.join("、")}
            </h3>
            <p lang="ja" className="text-ink-muted">
                {entry.kana.join("、")}
            </p>
        </div>
        <p className="text-sm text-ink-faint">({entry.translation_type})</p>
        <p className="text-ink">{entry.gloss.join("; ")}</p>
    </div>
);

/**
 * Displays detailed info for a single Kanji.
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
}) => (
    <div className={`py-2 ${!isLast ? "border-b border-ink/10" : ""}`}>
        <h3 lang="ja" className="text-xl font-bold text-ink">
            {kanjiInfo.literal}
        </h3>
        <div className="mt-1 grid grid-cols-2 gap-2 text-sm text-ink">
            <p>
                <span className="font-semibold text-ink-faint">Strokes:</span>{" "}
                {kanjiInfo.stroke_count}
            </p>
            <p>
                <span className="font-semibold text-ink-faint">Grade:</span>{" "}
                {kanjiInfo.grade || "N/A"}
            </p>
            <p>
                <span className="font-semibold text-ink-faint">JLPT:</span>{" "}
                {kanjiInfo.jlpt_tanos || kanjiInfo.jlpt_kanjidic || "N/A"}
            </p>
            <div className="col-span-2">
                <p>
                    <span className="font-semibold text-ink-faint">On&apos;yomi:</span>{" "}
                    <span lang="ja">{kanjiInfo.onyomi.join("、")}</span>
                </p>
                <p>
                    <span className="font-semibold text-ink-faint">Kun&apos;yomi:</span>{" "}
                    <span lang="ja">{kanjiInfo.kunyomi.join("、")}</span>
                </p>
            </div>
            <div className="col-span-2">
                <p>
                    <span className="font-semibold text-ink-faint">Meanings:</span>{" "}
                    {kanjiInfo.meanings.join(", ")}
                </p>
            </div>
        </div>
    </div>
);

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
}: {
    word: string;
    jmdictEntries: JMEntry[];
    jmnedictEntries: JMNEntry[];
    kanjiInfo: KanjiInfo[];
    examples: string[];
}) => {
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
            <h2 lang="ja" className="mb-4 text-center font-display text-4xl font-bold">
                {word}
            </h2>

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
                {activeTab === "Examples" &&
                    examples.map((example, i) => (
                        <ExampleDisplay
                            key={i}
                            example={example}
                            isLast={i === examples.length - 1}
                        />
                    ))}
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
    if (results.jmentries.length > 0) tabs.push("JMdict");
    if (results.jmnentries.length > 0) tabs.push("JMnedict");
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
                {activeTab === "JMdict" &&
                    results.jmentries.map((entry, i) => (
                        <JMEntryRow key={i} entry={entry} onSelect={onWordSelect} />
                    ))}
                {activeTab === "JMnedict" &&
                    results.jmnentries.map((entry, i) => (
                        <JMNEntryRow key={i} entry={entry} onSelect={onWordSelect} />
                    ))}
                {activeTab === "Kanji" &&
                    results.kanji.map((kanji, i) => (
                        <KanjiRow key={i} kanji={kanji} onSelect={onWordSelect} />
                    ))}
                {activeTab === "Examples" &&
                    results.examples.map((ex, i) => (
                        <p key={i} lang="ja" className="px-3 py-2 text-center text-ink-muted">
                            {ex}
                        </p>
                    ))}
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
