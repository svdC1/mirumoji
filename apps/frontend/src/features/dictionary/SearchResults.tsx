/**
 * @packageDocumentation The Dictionary hub's index view: an invitation when
 * idle, wildcard results (entries / names / kanji tabs) for Japanese pattern
 * searches, and entry rows for English reverse lookups. Rows navigate to the
 * word / kanji views.
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiDictQuery, apiSearchEnglish, isEmptyDict } from "@/shared/dict/api";
import { kanjiRoute, wordRoute } from "@/shared/dict/routes";
import { EmptyState, Skeleton, cn } from "@/shared/ui";
import { DictTabs, JMEntryRow, JMNEntryRow, KanjiRow } from "@/shared/components/DictDisplays";
import StrokeOrder from "@/shared/components/StrokeOrder";
import { getRecentLookups } from "./recent";
import type { JMEntry, KotobaseData } from "@/shared/dict/types";

type Tab = "Entries" | "Proper Nouns" | "Kanji";

/** Common kanji the landing page offers as starting points. */
const EXPLORE_KANJI = ["語", "食", "水", "心", "時", "見", "気", "本", "話", "学", "字", "書"];

/** Common words the landing page floats as starting points. */
const EXPLORE_WORDS = [
    "言葉",
    "友達",
    "時間",
    "楽しい",
    "勉強",
    "音楽",
    "映画",
    "世界",
    "夢",
    "旅行",
    "元気",
    "面白い",
    "大丈夫",
    "気持ち",
    "物語",
    "朝ご飯",
];

/**
 * The hub's landing: recent lookups to jump back into and a few kanji drawing
 * themselves as starting points, so the page is a place rather than an empty
 * form.
 *
 * @param {{ onWord: (w: string) => void; onKanji: (k: string) => void }} props
 *     Navigation callbacks.
 * @returns {JSX.Element} The landing content.
 */
function Landing({
    onWord,
    onKanji,
}: {
    onWord: (word: string) => void;
    onKanji: (literal: string) => void;
}) {
    const [recent] = useState(getRecentLookups);
    // A stable random sample per visit keeps the invitation fresh
    const [explore] = useState(() =>
        [...EXPLORE_KANJI].sort(() => Math.random() - 0.5).slice(0, 4)
    );
    const [words] = useState(() => [...EXPLORE_WORDS].sort(() => Math.random() - 0.5).slice(0, 8));

    return (
        <div className="mx-auto max-w-xl space-y-4">
            {recent.length > 0 && (
                <div className="rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                    <h3 className="mb-2 text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                        Recent
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                        {recent.map((r) => (
                            <button
                                key={`${r.kind}-${r.value}`}
                                type="button"
                                lang="ja"
                                onClick={() =>
                                    r.kind === "kanji" ? onKanji(r.value) : onWord(r.value)
                                }
                                className="rounded-control bg-surface-2 px-2.5 py-1 text-sm text-ink-muted transition-colors hover:bg-shu/15 hover:text-shu"
                            >
                                {r.value}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <div className="rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                <h3 className="mb-3 text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                    Explore A Kanji
                </h3>
                <div className="flex items-center justify-around">
                    {explore.map((k) => (
                        <button
                            key={k}
                            type="button"
                            onClick={() => onKanji(k)}
                            aria-label={`Open ${k} in the dictionary`}
                            className="rounded-control p-1 transition-colors hover:bg-shu/10"
                        >
                            <StrokeOrder literal={k} numbers={false} className="h-16 w-16" />
                        </button>
                    ))}
                </div>
            </div>

            <div className="rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                <h3 className="mb-3 text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                    Explore A Word
                </h3>
                <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 py-1">
                    {words.map((w, i) => (
                        <button
                            key={w}
                            type="button"
                            lang="ja"
                            onClick={() => onWord(w)}
                            className={cn(
                                "rounded-control px-2 py-0.5 font-jp text-ink-muted transition-colors hover:bg-shu/10 hover:text-shu",
                                i % 3 === 0 ? "text-xl" : "text-lg"
                            )}
                        >
                            {w}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

/**
 * The SearchResults component.
 *
 * @returns {JSX.Element} The search results view.
 */
export default function SearchResults() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const q = searchParams.get("q") ?? "";
    const mode = searchParams.get("mode") === "en" ? "en" : "jp";

    const [loading, setLoading] = useState(false);
    const [wildcard, setWildcard] = useState<KotobaseData | null>(null);
    const [english, setEnglish] = useState<JMEntry[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [tab, setTab] = useState<Tab>("Entries");

    useEffect(() => {
        if (!q) {
            setWildcard(null);
            setEnglish(null);
            setError(null);
            return;
        }
        let cancelled = false;
        setLoading(true);
        setError(null);
        setWildcard(null);
        setEnglish(null);
        const run =
            mode === "en"
                ? apiSearchEnglish(q).then((r) => {
                      if (cancelled) return;
                      if (r.length === 0) setError(`No Results For “${q}”`);
                      else setEnglish(r);
                  })
                : apiDictQuery(q, true).then((r) => {
                      if (cancelled) return;
                      if (isEmptyDict(r)) setError(`No Results For “${q}”`);
                      else {
                          setWildcard(r);
                          setTab(
                              r.jmentries.length > 0
                                  ? "Entries"
                                  : r.jmnentries.length > 0
                                    ? "Proper Nouns"
                                    : "Kanji"
                          );
                      }
                  });
        run.catch(() => !cancelled && setError("Failed To Fetch Results")).finally(
            () => !cancelled && setLoading(false)
        );
        return () => {
            cancelled = true;
        };
    }, [q, mode]);

    const openWord = (word: string) => navigate(wordRoute(word));
    const openKanji = (literal: string) => navigate(kanjiRoute(literal));

    if (!q) {
        return <Landing onWord={openWord} onKanji={openKanji} />;
    }

    if (loading) {
        return (
            <div className="mx-auto max-w-2xl space-y-2">
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
            </div>
        );
    }

    if (error) {
        return <EmptyState title="Nothing Found" description={error} />;
    }

    if (english) {
        return (
            <div className="mx-auto max-w-2xl rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                {english.map((entry, i) => (
                    <JMEntryRow key={i} entry={entry} onSelect={openWord} />
                ))}
            </div>
        );
    }

    if (!wildcard) return <></>;

    const tabs: Tab[] = [];
    if (wildcard.jmentries.length > 0) tabs.push("Entries");
    if (wildcard.jmnentries.length > 0) tabs.push("Proper Nouns");
    if (wildcard.kanji.length > 0) tabs.push("Kanji");

    const active = tabs.includes(tab) ? tab : tabs[0];

    return (
        <div className="mx-auto max-w-2xl rounded-card border border-ink/10 bg-surface px-4 pt-1 shadow-soft">
            <DictTabs tabs={tabs} active={active} onSelect={(t) => setTab(t as Tab)} />
            <div className="max-h-[60vh] overflow-y-auto py-3">
                {active === "Entries" &&
                    wildcard.jmentries.map((entry, i) => (
                        <JMEntryRow key={i} entry={entry} onSelect={openWord} />
                    ))}
                {active === "Proper Nouns" &&
                    wildcard.jmnentries.map((entry, i) => (
                        <JMNEntryRow key={i} entry={entry} onSelect={openWord} />
                    ))}
                {active === "Kanji" &&
                    wildcard.kanji.map((kanji, i) => (
                        <KanjiRow key={i} kanji={kanji} onSelect={openKanji} />
                    ))}
            </div>
        </div>
    );
}
