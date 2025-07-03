/**
 * @fileoverview This file contains specialized components for displaying different types of dictionary data,
 * such as JMdict entries, proper noun entries, and Kanji information.
 */

import { JMEntry, JMNEntry, KanjiInfo } from "../types/types";

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
 * @param {number} props.key - The unique key for the component.
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
                <p className="text-neutral-400 text-lg">({example})</p>
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
                        On'yomi:
                    </span>{" "}
                    {kanjiInfo.onyomi.join("、")}
                </p>
                <p>
                    <span className="font-semibold text-neutral-400">
                        Kun'yomi:
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
