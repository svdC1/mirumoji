/**
 * @packageDocumentation Shared presentational components for dictionary data
 * (JMdict / JMnedict entries, kanji profiles, examples, morphology), reused by
 * the WordDialog quick lookup and the Dictionary hub at different levels of
 * interactivity: the hub makes examples, kanji, radicals, and cross-references
 * clickable, while the dialog renders them inert.
 */

import { useEffect, useState } from "react";
import { Languages } from "lucide-react";
import { apiTokenizeBatch } from "@/shared/dict/api";
import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { grammarTermEn } from "@/shared/japanese/grammarTerms";
import { toHiragana } from "@/shared/japanese/kana";
import { Badge, Tooltip, cn } from "@/shared/ui";
import TokenizedText from "./TokenizedText";
import StrokeOrder, { KanjiGlyph } from "./StrokeOrder";
import type {
    Example,
    JMEntry,
    JMNEntry,
    JapaneseWord,
    KanjiInfo,
    Token,
    WordSense,
} from "@/shared/dict/types";

const POS_CHIP = "rounded bg-ink/10 px-1.5 py-0.5 text-2xs text-ink-muted";
const TAG_CHIP = "rounded bg-ai/10 px-1.5 py-0.5 text-2xs text-ai";

/** The badge row shown beside a JMdict entry headword. */
export function EntryBadges({ entry }: { entry: JMEntry }) {
    return (
        <>
            {entry.is_common && <Badge tone="success">Common</Badge>}
            {entry.freq_rank != null && <Badge>Top {entry.freq_rank * 500}</Badge>}
        </>
    );
}

/**
 * One sense: numbered glosses with readable POS / field / misc tags and
 * optional antonym / cross-reference chips.
 *
 * @param {object} props The sense, its 1-based number, and an optional
 *     reference click handler (references render inert without it).
 * @returns {JSX.Element} The rendered sense.
 */
function SenseRow({
    sense,
    number,
    onRefClick,
}: {
    sense: WordSense;
    number: number;
    onRefClick?: (ref: string) => void;
}) {
    const refs = [
        ...sense.xrefs.map((r) => ({ ref: r, label: "See" })),
        ...sense.antonyms.map((r) => ({ ref: r, label: "Antonym" })),
    ];
    return (
        <li className="flex gap-2 text-sm leading-relaxed">
            <span className="select-none pt-0.5 text-ink-faint">{number}.</span>
            <div className="min-w-0">
                <div className="mb-0.5 flex flex-wrap items-center gap-1">
                    {sense.pos.map((tag) => (
                        <span key={tag} className={POS_CHIP}>
                            {tag}
                        </span>
                    ))}
                    {[...sense.field, ...sense.misc].map((tag) => (
                        <span key={tag} className={TAG_CHIP}>
                            {tag}
                        </span>
                    ))}
                </div>
                <span className="text-ink">{sense.glosses.join(", ")}</span>
                {refs.length > 0 && (
                    <span className="ml-2 inline-flex flex-wrap items-center gap-1 align-middle">
                        {refs.map(({ ref, label }) => (
                            <button
                                key={`${label}-${ref}`}
                                type="button"
                                lang="ja"
                                disabled={!onRefClick}
                                onClick={() => onRefClick?.(ref)}
                                className={cn(
                                    "rounded bg-ink/5 px-1.5 py-0.5 text-2xs text-ink-muted",
                                    onRefClick && "transition-colors hover:bg-shu/15 hover:text-shu"
                                )}
                            >
                                {label} {ref.split("・")[0]}
                            </button>
                        ))}
                    </span>
                )}
            </div>
        </li>
    );
}

/**
 * Displays a JMdict entry: written / read forms, common + frequency badges,
 * and its numbered senses.
 *
 * @param {object} props The entry, a last-row flag, and an optional
 *     cross-reference click handler.
 * @returns {JSX.Element} The rendered entry.
 */
export const JmdictEntryDisplay = ({
    entry,
    isLast,
    onRefClick,
}: {
    entry: JMEntry;
    isLast: boolean;
    onRefClick?: (ref: string) => void;
}) => {
    const headword = entry.kanji.length > 0 ? entry.kanji.join("、") : entry.kana.join("、");
    return (
        <div className={cn("py-3", !isLast && "border-b border-ink/10")}>
            <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                <h3 lang="ja" className="font-display text-xl font-semibold text-ink">
                    {headword}
                </h3>
                {entry.kanji.length > 0 && entry.kana.length > 0 && (
                    <span lang="ja" className="text-ink-muted">
                        {entry.kana.join("、")}
                    </span>
                )}
                <EntryBadges entry={entry} />
            </div>
            <ol className="mt-2 space-y-2">
                {entry.senses.map((sense, i) => (
                    <SenseRow key={i} sense={sense} number={i + 1} onRefClick={onRefClick} />
                ))}
            </ol>
        </div>
    );
};

/**
 * Displays a JMnedict (proper noun) entry with its readable name types.
 *
 * @param {{ entry: JMNEntry; isLast: boolean }} props The entry + last-row flag.
 * @returns {JSX.Element} The rendered entry.
 */
export const JmnedictEntryDisplay = ({ entry, isLast }: { entry: JMNEntry; isLast: boolean }) => {
    const headword = entry.kanji.length > 0 ? entry.kanji.join("、") : entry.kana.join("、");
    return (
        <div className={cn("py-3", !isLast && "border-b border-ink/10")}>
            <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                <h3 lang="ja" className="font-display text-xl font-semibold text-ink">
                    {headword}
                </h3>
                {entry.kanji.length > 0 && entry.kana.length > 0 && (
                    <span lang="ja" className="text-ink-muted">
                        {entry.kana.join("、")}
                    </span>
                )}
                {entry.name_types.map((t) => (
                    <span key={t} className={cn(POS_CHIP, "ml-auto")}>
                        {t}
                    </span>
                ))}
            </div>
            <p className="mt-1.5 text-sm text-ink">{entry.gloss.join("; ")}</p>
        </div>
    );
};

/**
 * Displays one kanji: its stroke-order drawing (or plain glyph) beside stats
 * badges, meanings, readings, and its radical components.
 *
 * @param {object} props The kanji, a last-row flag, and optional handlers
 *     that make the glyph / radicals clickable on the hub.
 * @returns {JSX.Element} The rendered kanji card.
 */
export const KanjiCard = ({
    kanji,
    isLast,
    onKanjiClick,
    onRadicalClick,
}: {
    kanji: KanjiInfo;
    isLast: boolean;
    onKanjiClick?: (literal: string) => void;
    onRadicalClick?: (radical: string) => void;
}) => {
    // Without a navigation handler (the dialog) the diagram itself replays on
    // click, so the animation stays playable in compact surfaces
    const glyph = kanji.has_stroke_order ? (
        <StrokeOrder
            literal={kanji.literal}
            numbers={false}
            replayOnClick={!onKanjiClick}
            className="h-16 w-16"
        />
    ) : (
        <KanjiGlyph literal={kanji.literal} className="h-16 w-16 text-ink" />
    );
    return (
        <div className={cn("flex gap-4 py-3", !isLast && "border-b border-ink/10")}>
            {onKanjiClick ? (
                <button
                    type="button"
                    onClick={() => onKanjiClick(kanji.literal)}
                    aria-label={`Open ${kanji.literal} in the dictionary`}
                    className="shrink-0 self-start rounded-control transition-colors hover:bg-shu/10"
                >
                    {glyph}
                </button>
            ) : (
                <div className="shrink-0 self-start">{glyph}</div>
            )}
            <div className="min-w-0 flex-1 space-y-2 text-sm">
                <div className="flex flex-wrap gap-1.5">
                    {kanji.stroke_count != null && <Badge>{kanji.stroke_count} Strokes</Badge>}
                    {kanji.grade != null && <Badge>Grade {kanji.grade}</Badge>}
                    {kanji.jlpt != null && <Badge tone="accent">N{kanji.jlpt}</Badge>}
                    {kanji.is_joyo && <Badge tone="success">Joyo</Badge>}
                    {kanji.freq != null && <Badge>Freq {kanji.freq}</Badge>}
                </div>
                {kanji.meanings.length > 0 && (
                    <p className="text-ink">{kanji.meanings.join(", ")}</p>
                )}
                {kanji.onyomi.length > 0 && (
                    <p>
                        <span className="text-2xs uppercase tracking-wide text-ink-faint">On </span>
                        <span lang="ja" className="text-ink-muted">
                            {kanji.onyomi.join("、")}
                        </span>
                    </p>
                )}
                {kanji.kunyomi.length > 0 && (
                    <p>
                        <span className="text-2xs uppercase tracking-wide text-ink-faint">
                            Kun{" "}
                        </span>
                        <span lang="ja" className="text-ink-muted">
                            {kanji.kunyomi.join("、")}
                        </span>
                    </p>
                )}
                {kanji.radicals.length > 0 && (
                    <p className="flex flex-wrap items-center gap-1">
                        <span className="text-2xs uppercase tracking-wide text-ink-faint">
                            Radicals{" "}
                        </span>
                        {kanji.radicals.map((r) => (
                            <button
                                key={r}
                                type="button"
                                lang="ja"
                                disabled={!onRadicalClick}
                                onClick={() => onRadicalClick?.(r)}
                                className={cn(
                                    "rounded bg-ink/5 px-1.5 py-0.5 text-sm text-ink-muted",
                                    onRadicalClick &&
                                        "transition-colors hover:bg-shu/15 hover:text-shu"
                                )}
                            >
                                {r}
                            </button>
                        ))}
                    </p>
                )}
            </div>
        </div>
    );
};

/**
 * Renders example sentences with their English translations. Sentences are
 * tokenized for furigana; with `onWordClick` the tokens are clickable (the
 * hub), in the dialog the handler opens the word's entry in a new tab.
 *
 * @param {object} props The examples + a per-word click handler.
 * @returns {JSX.Element} The rendered examples.
 */
export const ExamplesSection = ({
    examples,
    onWordClick,
}: {
    examples: Example[];
    onWordClick: (sentence: string, word: string) => void;
}) => {
    const [wordsList, setWordsList] = useState<JapaneseWord[][] | null>(null);
    const texts = examples.map((e) => e.text);
    const joined = texts.join(" ");
    const { mode } = useBundleSettings();

    useEffect(() => {
        let cancelled = false;
        setWordsList(null);
        apiTokenizeBatch(texts, mode)
            .then((r) => !cancelled && setWordsList(r))
            .catch(() => !cancelled && setWordsList(null));
        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [joined, mode]);

    return (
        <ul className="space-y-2">
            {examples.map((ex, i) => (
                <li
                    key={i}
                    className="relative rounded-control bg-surface-2 px-3 py-2.5 leading-relaxed"
                >
                    <div className="flex items-start gap-2">
                        <div className="min-w-0 flex-1 text-lg">
                            {wordsList && wordsList[i] && wordsList[i].length > 0 ? (
                                <TokenizedText
                                    words={wordsList[i]}
                                    sentence={ex.text}
                                    showFurigana
                                    onWordClick={onWordClick}
                                />
                            ) : (
                                <span lang="ja" className="text-ink-muted">
                                    {ex.text}
                                </span>
                            )}
                        </div>
                        {ex.translations.length > 0 && (
                            <Tooltip
                                label={ex.translations[0]}
                                wide
                                align="right"
                                className="mt-1.5 shrink-0"
                            >
                                <button
                                    type="button"
                                    aria-label="Show translation"
                                    className="text-ink-faint transition-colors hover:text-ai focus:text-ai focus:outline-none"
                                >
                                    <Languages size={15} />
                                </button>
                            </Tooltip>
                        )}
                    </div>
                </li>
            ))}
        </ul>
    );
};

/** A grammar term chip with a translation tooltip when the term is known. */
function GrammarTerm({ term }: { term: string }) {
    const en = grammarTermEn(term);
    if (!en) {
        return (
            <span lang="ja" className="text-ink">
                {term}
            </span>
        );
    }
    return (
        <Tooltip label={en}>
            <span
                lang="ja"
                className="cursor-help text-ink underline decoration-dotted decoration-ink/30 underline-offset-2"
            >
                {term}
            </span>
        </Tooltip>
    );
}

/**
 * Renders the morphological detail carried by a stitched word's underlying
 * UniDic tokens (reading, part-of-speech hierarchy, conjugation, base form,
 * origin). Japanese grammatical terms carry a tooltip with their English
 * meaning.
 *
 * @param {{ tokens: Token[] }} props The word's constituent tokens.
 * @returns {JSX.Element} The grammar breakdown.
 */
export function GrammarSection({ tokens }: { tokens: Token[] }) {
    if (!tokens || tokens.length === 0) {
        return <p className="py-4 text-center italic text-ink-muted">No grammar data.</p>;
    }
    const clean = (v: string) => (v && v !== "*" ? v : "");
    const rowsOf = (t: Token): [string, string[]][] => {
        const reading = clean(t.kana) ? [toHiragana(t.kana)] : [];
        const pos = [t.pos1, t.pos2, t.pos3, t.pos4].map(clean).filter(Boolean);
        const conj = [t.cType, t.cForm].map(clean).filter(Boolean);
        const base = clean(t.orthBase) && t.orthBase !== t.surface ? [t.orthBase] : [];
        const pron = clean(t.pron) && t.pron !== t.kana ? [toHiragana(t.pron)] : [];
        const origin = clean(t.goshu) ? [t.goshu] : [];
        const rows: [string, string[]][] = [];
        if (reading.length) rows.push(["Reading", reading]);
        if (pron.length) rows.push(["Pronunciation", pron]);
        if (pos.length) rows.push(["Part Of Speech", pos]);
        if (conj.length) rows.push(["Conjugation", conj]);
        if (base.length) rows.push(["Base Form", base]);
        if (origin.length) rows.push(["Word Origin", origin]);
        return rows;
    };
    return (
        <div className="space-y-3">
            {tokens.map((t, i) => (
                <div key={i} className="rounded-control border border-ink/10 p-3">
                    <div lang="ja" className="mb-2 font-display text-xl text-ink">
                        {t.surface}
                    </div>
                    <dl className="space-y-1 text-sm">
                        {rowsOf(t).map(([label, values]) => (
                            <div key={label} className="flex gap-3">
                                <dt className="w-32 shrink-0 text-ink-faint">{label}</dt>
                                <dd className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
                                    {values.map((v, j) => (
                                        <span key={j} className="inline-flex items-center gap-1.5">
                                            {j > 0 && (
                                                <span className="select-none text-ink-faint">
                                                    ·
                                                </span>
                                            )}
                                            <GrammarTerm term={v} />
                                        </span>
                                    ))}
                                </dd>
                            </div>
                        ))}
                    </dl>
                </div>
            ))}
        </div>
    );
}

/**
 * The hub's shared tab bar: an underlined row of section tabs, one active at
 * a time, so each view stays a single compact panel instead of a long scroll.
 *
 * @param {object} props The tab labels, the active one, and the callback.
 * @returns {JSX.Element} The tab bar.
 */
export function DictTabs({
    tabs,
    active,
    onSelect,
}: {
    tabs: string[];
    active: string;
    onSelect: (tab: string) => void;
}) {
    return (
        <div className="border-b border-ink/10">
            <nav className="-mb-px flex justify-center space-x-4" aria-label="Tabs">
                {tabs.map((tab) => (
                    <button
                        key={tab}
                        onClick={() => onSelect(tab)}
                        className={cn(
                            "whitespace-nowrap border-b-2 px-2 py-2.5 text-sm font-medium transition-colors",
                            active === tab
                                ? "border-shu text-shu"
                                : "border-transparent text-ink-faint hover:border-ink/20 hover:text-ink-muted"
                        )}
                    >
                        {tab}
                    </button>
                ))}
            </nav>
        </div>
    );
}

const ROW =
    "grid grid-cols-3 gap-4 items-center text-center py-2 px-3 rounded-control hover:bg-ink/5 cursor-pointer transition-colors";

/**
 * A clickable JMdict result row (search result lists).
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
            {entry.kanji.length > 0 ? entry.kanji.join("、") : entry.kana.join("、")}
        </p>
        <p lang="ja" className="text-ink-muted">
            {entry.kana.join("、")}
        </p>
        <p className="truncate text-sm text-ink-faint">
            {entry.senses[0]?.glosses.join(", ") ?? ""}
        </p>
    </div>
);

/**
 * A clickable JMnedict result row.
 *
 * @param {{ entry: JMNEntry; onSelect: (word: string) => void }} props The entry + callback.
 * @returns {JSX.Element} The row.
 */
export const JMNEntryRow = ({
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
        <p className="truncate text-sm text-ink-faint">{entry.name_types.join(", ")}</p>
    </div>
);

/**
 * A clickable kanji result row.
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
        <p className="col-span-2 truncate text-sm text-ink-faint">{kanji.meanings.join(", ")}</p>
    </div>
);
