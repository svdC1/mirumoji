/**
 * @packageDocumentation The Dictionary hub's word view: the full entry for one
 * word — furigana headword with badges, numbered senses with readable tags
 * (cross-references resolve on click), its kanji as clickable cards, and
 * clickable example sentences with translations.
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiDictQuery, isEmptyDict } from "@/shared/dict/api";
import { kanjiRoute, wordRoute } from "@/shared/dict/routes";
import { toastApiError } from "@/shared/api/errors";
import { Badge, EmptyState, Skeleton } from "@/shared/ui";
import {
    DictTabs,
    ExamplesSection,
    JmdictEntryDisplay,
    JmnedictEntryDisplay,
    KanjiCard,
} from "@/shared/components/DictDisplays";
import FuriganaText from "@/shared/components/FuriganaText";
import { pushRecentLookup } from "./recent";
import type { KotobaseData } from "@/shared/dict/types";

/**
 * The WordView component.
 *
 * @returns {JSX.Element} The word entry view.
 */
export default function WordView() {
    const [searchParams] = useSearchParams();
    const term = searchParams.get("term") ?? "";
    const navigate = useNavigate();
    const [data, setData] = useState<KotobaseData | null | undefined>(undefined);
    const [tab, setTab] = useState("Entries");

    useEffect(() => {
        let cancelled = false;
        setData(undefined);
        apiDictQuery(term)
            .then((r) => {
                if (cancelled) return;
                const empty = isEmptyDict(r);
                setData(empty ? null : r);
                if (!empty) pushRecentLookup({ kind: "word", value: term });
            })
            .catch((e) => {
                if (cancelled) return;
                setData(null);
                toastApiError(e);
            });
        return () => {
            cancelled = true;
        };
    }, [term]);

    if (data === undefined) {
        return (
            <div className="mx-auto max-w-2xl space-y-3">
                <Skeleton className="h-12" />
                <Skeleton className="h-40" />
            </div>
        );
    }

    if (data === null) {
        return (
            <EmptyState title="Nothing Found" description={`No Dictionary Entry For “${term}”`} />
        );
    }

    const reading = data.jmentries[0]?.kana[0] || data.jmnentries[0]?.kana[0] || "";
    // The ruby annotation already shows the reading, so the italic reading
    // beside the headword only appears when no furigana is known
    const showReading = !!reading && data.furigana.length === 0;
    const openWord = (word: string) => navigate(wordRoute(word));

    const tabs: string[] = [];
    if (data.jmentries.length > 0) tabs.push("Entries");
    if (data.jmnentries.length > 0) tabs.push("Names");
    if (data.kanji.length > 0) tabs.push("Kanji");
    if (data.examples.length > 0) tabs.push("Examples");
    const active = tabs.includes(tab) ? tab : tabs[0];

    return (
        <div className="mx-auto max-w-2xl rounded-card border border-ink/10 bg-surface p-5 shadow-soft sm:p-6">
            <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                <h2 className="font-display text-4xl font-bold text-ink">
                    <FuriganaText segments={data.furigana} fallback={data.query || term} />
                </h2>
                {showReading && (
                    <span lang="ja" className="text-lg italic text-ink-muted">
                        {reading}
                    </span>
                )}
                {data.jmentries[0]?.is_common && <Badge tone="success">Common</Badge>}
                {data.jlpt !== "Unknown" && <Badge tone="accent">{data.jlpt}</Badge>}
            </div>

            <DictTabs tabs={tabs} active={active} onSelect={setTab} />

            <div className="pt-3">
                {active === "Entries" &&
                    data.jmentries.map((entry, i) => (
                        <JmdictEntryDisplay
                            key={i}
                            entry={entry}
                            isLast={i === data.jmentries.length - 1}
                            onRefClick={(ref) => openWord(ref.split("・")[0])}
                        />
                    ))}
                {active === "Names" &&
                    data.jmnentries.map((entry, i) => (
                        <JmnedictEntryDisplay
                            key={i}
                            entry={entry}
                            isLast={i === data.jmnentries.length - 1}
                        />
                    ))}
                {active === "Kanji" &&
                    data.kanji.map((kanji, i) => (
                        <KanjiCard
                            key={kanji.literal}
                            kanji={kanji}
                            isLast={i === data.kanji.length - 1}
                            onKanjiClick={(literal) =>
                                navigate(kanjiRoute(literal), {
                                    state: { fromWord: term },
                                })
                            }
                            onRadicalClick={(radical) =>
                                navigate(
                                    `/dictionary/radicals?picked=${encodeURIComponent(radical)}`
                                )
                            }
                        />
                    ))}
                {active === "Examples" && (
                    <ExamplesSection
                        examples={data.examples}
                        onWordClick={(_, word) => openWord(word)}
                    />
                )}
            </div>
        </div>
    );
}
