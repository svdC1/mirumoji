/**
 * @packageDocumentation The Dictionary hub's radical search: pick radicals
 * from an inventory grouped by stroke count, see every kanji containing all of
 * them, and open a kanji's detail view. The picked set rides in the URL so the
 * search is shareable and survives back/forward.
 */

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiByRadicals, apiRadicals } from "@/shared/dict/api";
import { EmptyState, Skeleton, cn } from "@/shared/ui";
import type { KanjiInfo, RadicalInfo } from "@/shared/dict/types";

/**
 * The RadicalSearch component.
 *
 * @returns {JSX.Element} The radical search view.
 */
export default function RadicalSearch() {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const picked = useMemo(() => Array.from(searchParams.get("picked") ?? ""), [searchParams]);
    const match = searchParams.get("match") === "any" ? "any" : "all";

    const [inventory, setInventory] = useState<RadicalInfo[] | null>(null);
    const [matches, setMatches] = useState<KanjiInfo[] | null>(null);

    useEffect(() => {
        let cancelled = false;
        apiRadicals()
            .then((r) => !cancelled && setInventory(r))
            .catch(() => !cancelled && setInventory([]));
        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        if (picked.length === 0) {
            setMatches(null);
            return;
        }
        let cancelled = false;
        setMatches(null);
        apiByRadicals(picked, match)
            .then((k) => !cancelled && setMatches(k))
            .catch(() => !cancelled && setMatches([]));
        return () => {
            cancelled = true;
        };
    }, [picked.join(""), match]); // eslint-disable-line react-hooks/exhaustive-deps

    const setParams = (nextPicked: string[], nextMatch: "all" | "any") => {
        setSearchParams(
            {
                ...(nextPicked.length > 0 && { picked: nextPicked.join("") }),
                ...(nextMatch === "any" && { match: "any" }),
            },
            { replace: false }
        );
    };

    const togglePick = (radical: string) => {
        const next = picked.includes(radical)
            ? picked.filter((r) => r !== radical)
            : [...picked, radical];
        setParams(next, match);
    };

    const groups = useMemo(() => {
        const byStrokes = new Map<number, RadicalInfo[]>();
        (inventory ?? []).forEach((r) => {
            const strokes = r.stroke_count ?? 0;
            const group = byStrokes.get(strokes) ?? [];
            group.push(r);
            byStrokes.set(strokes, group);
        });
        return Array.from(byStrokes.entries()).sort(([a], [b]) => a - b);
    }, [inventory]);

    if (inventory === null) {
        return (
            <div className="mx-auto max-w-2xl space-y-2">
                <Skeleton className="h-24" />
                <Skeleton className="h-24" />
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-2xl space-y-4">
            <div className="rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                <div className="mb-2 flex items-center justify-between gap-2">
                    <h3 className="text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                        Pick Radicals
                    </h3>
                    <div className="flex gap-1 rounded-control bg-surface-2 p-0.5">
                        {(["all", "any"] as const).map((m) => (
                            <button
                                key={m}
                                type="button"
                                onClick={() => setParams(picked, m)}
                                aria-pressed={match === m}
                                title={
                                    m === "all"
                                        ? "Kanji Must Contain Every Picked Radical"
                                        : "Kanji Must Contain At Least One Picked Radical"
                                }
                                className={cn(
                                    "rounded-control px-2 py-0.5 text-2xs font-medium transition-colors",
                                    match === m
                                        ? "bg-shu/15 text-shu"
                                        : "text-ink-faint hover:text-ink"
                                )}
                            >
                                {m === "all" ? "All" : "Any"}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
                    {groups.map(([strokes, radicals]) => (
                        <div key={strokes} className="flex flex-wrap items-center gap-1">
                            <span className="w-5 shrink-0 text-2xs tabular-nums text-ink-faint">
                                {strokes}
                            </span>
                            {radicals.map((r) => (
                                <button
                                    key={r.radical}
                                    type="button"
                                    lang="ja"
                                    onClick={() => togglePick(r.radical)}
                                    aria-pressed={picked.includes(r.radical)}
                                    className={cn(
                                        "rounded-control px-1.5 py-0.5 text-lg leading-tight transition-colors",
                                        picked.includes(r.radical)
                                            ? "bg-shu/20 text-shu"
                                            : "text-ink-muted hover:bg-ink/5 hover:text-ink"
                                    )}
                                >
                                    {r.radical}
                                </button>
                            ))}
                        </div>
                    ))}
                </div>
            </div>

            {picked.length === 0 ? (
                <EmptyState
                    title="Pick A Radical"
                    description={
                        match === "all"
                            ? "Kanji Containing Every Picked Radical Will Show Here"
                            : "Kanji Containing Any Picked Radical Will Show Here"
                    }
                />
            ) : matches === null ? (
                <Skeleton className="h-24" />
            ) : matches.length === 0 ? (
                <EmptyState
                    title="No Kanji Found"
                    description={
                        match === "all"
                            ? "No Kanji Contains Every Picked Radical"
                            : "No Kanji Contains Any Picked Radical"
                    }
                />
            ) : (
                <div className="rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                    <h3 className="mb-2 text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                        {matches.length} Kanji
                    </h3>
                    <div className="flex max-h-72 flex-wrap gap-1 overflow-y-auto">
                        {matches.map((k) => (
                            <button
                                key={k.literal}
                                type="button"
                                lang="ja"
                                title={k.meanings.join(", ")}
                                onClick={() =>
                                    navigate(`/dictionary/kanji/${encodeURIComponent(k.literal)}`, {
                                        state: {
                                            fromRadicals: picked.join(""),
                                            fromRadicalsMatch: match,
                                        },
                                    })
                                }
                                className="rounded-control px-1.5 py-0.5 font-jp text-2xl leading-tight text-ink transition-colors hover:bg-shu/15 hover:text-shu"
                            >
                                {k.literal}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
