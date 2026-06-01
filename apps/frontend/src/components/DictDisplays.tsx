/**
 * @packageDocumentation This file contains specialized components for displaying different types of dictionary data,
 * such as JMdict entries, proper noun entries, and Kanji information.
 */

import { useState } from "react";
import { JMEntry, JMNEntry, KanjiInfo } from "../types/types";
import { DictWildcardLookup } from "../types/types";
/**
 * Displays a standard dictionary entry from JMdict.
 * @param {object} props - The component props.
 * @param {JMEntry} props.entry - The dictionary entry data.
 * @param {boolean} props.isLast - True if this is the last item in a list, to omit the bottom border.
 * @returns {JSX.Element} The rendered JMdict entry.
 */
export const JmdictEntryDisplay = ({
    entry,
    isLast,
}: {
    entry: JMEntry;
    isLast: boolean;
}) => (
    <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
        <div className="flex items-center">
            <h3 className="text-lg font-bold mr-2">{entry.kanji.join("、")}</h3>
            <p className="text-md text-neutral-300">{entry.kana.join("、")}</p>
        </div>
        {entry.senses.map((sense, i) => (
            <div key={i} className="ml-4 mt-1">
                <p className="text-neutral-400 text-sm">({sense.pos})</p>
                <p>
                    <span className="text-neutral-400">{i + 1}.</span>{" "}
                    {sense.gloss}
                </p>
            </div>
        ))}
    </div>
);

/**
 * Displays an example sentence.
 * @param {object} props - The component props.
 * @param {string} props.example - The example sentence text.
 * @param {boolean} props.isLast - True if this is the last item in a list, to omit the bottom border.
 * @returns {JSX.Element} The rendered example.
 */
export const ExampleDisplay = ({
    example,
    isLast,
}: {
    example: string;
    isLast: boolean;
}) => (
    <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
        <div className="flex items-center">
            <div className="ml-4 mt-1">
                <p className="text-neutral-400 text-lg text-center">
                    ({example})
                </p>
            </div>
        </div>
    </div>
);

/**
 * Displays a proper noun dictionary entry from JMnedict.
 * @param {object} props - The component props.
 * @param {JMNEntry} props.entry - The proper noun entry data.
 * @param {boolean} props.isLast - True if this is the last item in a list, to omit the bottom border.
 * @returns {JSX.Element} The rendered JMnedict entry.
 */
export const JmnedictEntryDisplay = ({
    entry,
    isLast,
}: {
    entry: JMNEntry;
    isLast: boolean;
}) => (
    <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
        <div className="flex items-center">
            <h3 className="text-lg font-bold mr-2">{entry.kanji.join("、")}</h3>
            <p className="text-md text-neutral-300">{entry.kana.join("、")}</p>
        </div>
        <p className="text-neutral-400 text-sm">({entry.translation_type})</p>
        <p>{entry.gloss.join("; ")}</p>
    </div>
);

/**
 * Displays detailed information about a single Kanji character.
 * @param {object} props - The component props.
 * @param {KanjiInfo} props.kanjiInfo - The Kanji information object.
 * @param {boolean} props.isLast - True if this is the last item in a list, to omit the bottom border.
 * @returns {JSX.Element} The rendered Kanji information display.
 */
export const KanjiInfoDisplay = ({
    kanjiInfo,
    isLast,
}: {
    kanjiInfo: KanjiInfo;
    isLast: boolean;
}) => (
    <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
        <h3 className="text-xl font-bold">{kanjiInfo.literal}</h3>
        <div className="grid grid-cols-2 gap-2 text-sm mt-1">
            <p>
                <span className="font-semibold text-neutral-400">Strokes:</span>{" "}
                {kanjiInfo.stroke_count}
            </p>
            <p>
                <span className="font-semibold text-neutral-400">Grade:</span>{" "}
                {kanjiInfo.grade || "N/A"}
            </p>
            <p>
                <span className="font-semibold text-neutral-400">JLPT:</span>{" "}
                {kanjiInfo.jlpt_tanos || kanjiInfo.jlpt_kanjidic || "N/A"}
            </p>
            <div className="col-span-2">
                <p>
                    <span className="font-semibold text-neutral-400">
                        On&apos;yomi:
                    </span>{" "}
                    {kanjiInfo.onyomi.join("、")}
                </p>
                <p>
                    <span className="font-semibold text-neutral-400">
                        Kun&apos;yomi:
                    </span>{" "}
                    {kanjiInfo.kunyomi.join("、")}
                </p>
            </div>
            <div className="col-span-2">
                <p>
                    <span className="font-semibold text-neutral-400">
                        Meanings:
                    </span>{" "}
                    {kanjiInfo.meanings.join(", ")}
                </p>
            </div>
        </div>
    </div>
);

/**
 * A comprehensive card that displays multiple JMdict entries, JMnedict entries, Kanji information, and examples
 * in a well-divided, responsive card with a tabbed interface.
 * @param {object} props - The component props.
 * @param {string} props.word - The word that was looked up.
 * @param {JMEntry[]} props.jmdictEntries - The standard dictionary entries.
 * @param {JMNEntry[]} props.jmnedictEntries - The proper noun dictionary entries.
 * @param {KanjiInfo[]} props.kanjiInfo - The Kanji information.
 * @param {string[]} props.examples - The example sentences.
 * @returns {JSX.Element} The rendered comprehensive card.
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
    const tabs = [];
    if (jmdictEntries.length > 0) tabs.push("Definition");
    if (jmnedictEntries.length > 0) tabs.push("Proper Noun");
    if (kanjiInfo.length > 0) tabs.push("Kanji");
    if (examples.length > 0) tabs.push("Examples");

    const [activeTab, setActiveTab] = useState(tabs[0]);

    // This ensures that even if the active tab has no content (e.g., after a new search),
    // it defaults to the first available tab.
    if (!tabs.includes(activeTab)) {
        setActiveTab(tabs[0]);
    }

    return (
        <div className="bg-neutral-900 border border-neutral-700 rounded-lg shadow-xl p-4 sm:p-6 w-full max-w-2xl mx-auto text-white">
            <h2 className="text-4xl font-bold mb-4 text-center">{word}</h2>

            <div className="border-b border-neutral-700 mb-4">
                <nav
                    className="-mb-px flex justify-center space-x-4"
                    aria-label="Tabs"
                >
                    {tabs.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`${
                                activeTab === tab
                                    ? "border-indigo-500 text-indigo-400"
                                    : "border-transparent text-neutral-400 hover:text-neutral-200 hover:border-neutral-500"
                            } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200`}
                        >
                            {tab}
                        </button>
                    ))}
                </nav>
            </div>

            <div className="mt-4 max-h-[60vh] overflow-y-auto px-2 custom-scrollbar">
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
 * Displays the tabbed results from a wildcard search.
 * @param {object} props - The component props.
 * @param {DictWildcardLookup} props.results - The wildcard search results.
 * @param {(word: string) => void} props.onWordSelect - Callback to handle when a word is selected.
 * @returns {JSX.Element} The wildcard results component.
 */
export const WildcardResults = ({
    results,
    onWordSelect,
}: {
    results: DictWildcardLookup;
    onWordSelect: (word: string) => void;
}) => {
    const tabs = [];
    if (results.jmentries.length > 0) tabs.push("JMdict");
    if (results.jmnentries.length > 0) tabs.push("JMnedict");
    if (results.kanji.length > 0) tabs.push("Kanji");
    if (results.examples.length > 0) tabs.push("Examples");

    const [activeTab, setActiveTab] = useState(tabs[0] || "");

    return (
        <div className="bg-neutral-800 border border-neutral-700 rounded-lg shadow-lg mt-6 max-w-4xl mx-auto">
            <div className="border-b border-neutral-700">
                <nav
                    className="-mb-px flex justify-center space-x-4 px-4"
                    aria-label="Tabs"
                >
                    {tabs.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`${
                                activeTab === tab
                                    ? "border-indigo-500 text-indigo-400"
                                    : "border-transparent text-neutral-400 hover:text-neutral-200 hover:border-neutral-500"
                            } whitespace-nowrap py-3 px-2 border-b-2 font-medium text-sm transition-colors duration-200`}
                        >
                            {tab}
                        </button>
                    ))}
                </nav>
            </div>
            <div className="p-4 h-96 overflow-y-auto">
                {activeTab === "JMdict" &&
                    results.jmentries.map((entry, i) => (
                        <JMEntryRow
                            key={i}
                            entry={entry}
                            onSelect={onWordSelect}
                        />
                    ))}
                {activeTab === "JMnedict" &&
                    results.jmnentries.map((entry, i) => (
                        <JMNEntryRow
                            key={i}
                            entry={entry}
                            onSelect={onWordSelect}
                        />
                    ))}
                {activeTab === "Kanji" &&
                    results.kanji.map((kanji, i) => (
                        <KanjiRow
                            key={i}
                            kanji={kanji}
                            onSelect={onWordSelect}
                        />
                    ))}
                {activeTab === "Examples" &&
                    results.examples.map((ex, i) => (
                        <p
                            key={i}
                            className="py-2 px-3 text-center text-neutral-300"
                        >
                            {ex}
                        </p>
                    ))}
            </div>
        </div>
    );
};

/**
 * Renders a clickable row for a JMdict entry.
 * @param {object} props - The component props.
 * @param {JMEntry} props.entry - The JMdict entry.
 * @param {(word: string) => void} props.onSelect - Callback for when the row is clicked.
 * @returns {JSX.Element} The JMdict entry row component.
 */
export const JMEntryRow = ({
    entry,
    onSelect,
}: {
    entry: JMEntry;
    onSelect: (word: string) => void;
}) => (
    <div
        onClick={() => onSelect(entry.kanji[0] || entry.kana[0])}
        className="grid grid-cols-3 gap-4 items-center text-center py-2 px-3 rounded-md hover:bg-neutral-700 cursor-pointer transition-colors duration-150"
    >
        <p className="font-semibold">{entry.kanji.join("、")}</p>
        <p className="text-neutral-300">{entry.kana.join("、")}</p>
        <p className="text-sm text-neutral-400">
            {entry.senses.map((s) => s.pos).join(", ")}
        </p>
    </div>
);

/**
 * Renders a clickable row for a JMnedict entry.
 * @param {object} props - The component props.
 * @param {JMNEntry} props.entry - The JMnedict entry.
 * @param {(word: string) => void} props.onSelect - Callback for when the row is clicked.
 * @returns {JSX.Element} The JMnedict entry row component.
 */
const JMNEntryRow = ({
    entry,
    onSelect,
}: {
    entry: JMNEntry;
    onSelect: (word: string) => void;
}) => (
    <div
        onClick={() => onSelect(entry.kanji[0] || entry.kana[0])}
        className="grid grid-cols-3 gap-4 items-center text-center py-2 px-3 rounded-md hover:bg-neutral-700 cursor-pointer transition-colors duration-150"
    >
        <p className="font-semibold">{entry.kanji.join("、")}</p>
        <p className="text-neutral-300">{entry.kana.join("、")}</p>
        <p className="text-sm text-neutral-400">{entry.translation_type}</p>
    </div>
);

/**
 * Renders a clickable row for a Kanji character.
 * @param {object} props - The component props.
 * @param {KanjiInfo} props.kanji - The Kanji information.
 * @param {(word: string) => void} props.onSelect - Callback for when the row is clicked.
 * @returns {JSX.Element} The Kanji row component.
 */
export const KanjiRow = ({
    kanji,
    onSelect,
}: {
    kanji: KanjiInfo;
    onSelect: (word: string) => void;
}) => (
    <div
        onClick={() => onSelect(kanji.literal)}
        className="grid grid-cols-3 gap-4 items-center text-center py-2 px-3 rounded-md hover:bg-neutral-700 cursor-pointer transition-colors duration-150"
    >
        <p className="font-bold text-lg col-span-1">{kanji.literal}</p>
        <p className="text-sm text-neutral-400 col-span-2">
            {kanji.meanings.join(", ")}
        </p>
    </div>
);
