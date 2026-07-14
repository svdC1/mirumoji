/**
 * @packageDocumentation Demo variant of the dictionary display components,
 * aliased in only for `--mode demo`. It re-exports the real components and
 * overrides the click-through rows / kanji card so a link to an entry that was
 * not captured in the fixtures renders disabled (muted, no click) instead of
 * landing on an empty page. This one file gates the search results, the word /
 * kanji views, and the word dialog at once.
 */

import { KanjiCard as RealKanjiCard } from "@real/shared/components/DictDisplays";
import { cn } from "@/shared/ui";
import type { JMEntry, JMNEntry, KanjiInfo } from "@/shared/dict/types";
import { hasKanji, hasWord } from "../fixtureSet";

export * from "@real/shared/components/DictDisplays";

const ROW =
    "grid grid-cols-3 gap-4 items-center text-center py-2 px-3 rounded-control transition-colors";
const ROW_ON = "cursor-pointer hover:bg-ink/5";
const ROW_OFF = "cursor-default opacity-40";
const OFF_TITLE = "Not Part Of The Demo Sample";

/** A JMdict result row, disabled when the entry is not in the fixtures. */
export const JMEntryRow = ({
    entry,
    onSelect,
}: {
    entry: JMEntry;
    onSelect: (word: string) => void;
}) => {
    const term = entry.kanji[0] || entry.kana[0];
    const on = hasWord(term);
    return (
        <div
            onClick={on ? () => onSelect(term) : undefined}
            title={on ? undefined : OFF_TITLE}
            className={cn(ROW, on ? ROW_ON : ROW_OFF)}
        >
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
};

/** A JMnedict result row, disabled when the entry is not in the fixtures. */
export const JMNEntryRow = ({
    entry,
    onSelect,
}: {
    entry: JMNEntry;
    onSelect: (word: string) => void;
}) => {
    const term = entry.kanji[0] || entry.kana[0];
    const on = hasWord(term);
    return (
        <div
            onClick={on ? () => onSelect(term) : undefined}
            title={on ? undefined : OFF_TITLE}
            className={cn(ROW, on ? ROW_ON : ROW_OFF)}
        >
            <p lang="ja" className="font-semibold text-ink">
                {entry.kanji.join("、")}
            </p>
            <p lang="ja" className="text-ink-muted">
                {entry.kana.join("、")}
            </p>
            <p className="truncate text-sm text-ink-faint">{entry.name_types.join(", ")}</p>
        </div>
    );
};

/** A kanji result row, disabled when the kanji is not in the fixtures. */
export const KanjiRow = ({
    kanji,
    onSelect,
}: {
    kanji: KanjiInfo;
    onSelect: (word: string) => void;
}) => {
    const on = hasKanji(kanji.literal);
    return (
        <div
            onClick={on ? () => onSelect(kanji.literal) : undefined}
            title={on ? undefined : OFF_TITLE}
            className={cn(ROW, on ? ROW_ON : ROW_OFF)}
        >
            <p lang="ja" className="col-span-1 text-lg font-bold text-ink">
                {kanji.literal}
            </p>
            <p className="col-span-2 truncate text-sm text-ink-faint">
                {kanji.meanings.join(", ")}
            </p>
        </div>
    );
};

/** The real kanji card, but its open-in-dictionary link is dropped when the kanji is not in the fixtures. */
export const KanjiCard = (props: {
    kanji: KanjiInfo;
    isLast: boolean;
    onKanjiClick?: (literal: string) => void;
    onRadicalClick?: (radical: string) => void;
}) => {
    const gated =
        props.onKanjiClick && !hasKanji(props.kanji.literal)
            ? { ...props, onKanjiClick: undefined }
            : props;
    return <RealKanjiCard {...gated} />;
};
