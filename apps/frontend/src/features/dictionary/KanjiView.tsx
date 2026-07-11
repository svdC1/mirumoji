/**
 * @packageDocumentation The Dictionary hub's kanji view: a large stroke-order
 * drawing with replay / step / speed controls, the kanji's stats and readings,
 * pronunciation clips (Kanji Alive), its radical components, words that use
 * the kanji, and example sentences.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Volume2 } from "lucide-react";
import {
    apiKanji,
    apiKanjiAudio,
    apiKanjiSentences,
    apiKanjiWords,
    dictAudioClipUrl,
} from "@/shared/dict/api";
import { wordRoute } from "@/shared/dict/routes";
import { Badge, EmptyState, Skeleton, cn } from "@/shared/ui";
import { DictTabs, ExamplesSection, JMEntryRow } from "@/shared/components/DictDisplays";
import StrokeOrder from "@/shared/components/StrokeOrder";
import { pushRecentLookup } from "./recent";
import type { Example, JMEntry, KanjiAudio, KanjiInfo } from "@/shared/dict/types";

/** A labeled reading row (On / Kun / Nanori). */
function ReadingRow({ label, readings }: { label: string; readings: string[] }) {
    if (readings.length === 0) return <></>;
    return (
        <p>
            <span className="text-2xs uppercase tracking-wide text-ink-faint">{label} </span>
            <span lang="ja" className="text-ink">
                {readings.join("、")}
            </span>
        </p>
    );
}

/**
 * The KanjiView component.
 *
 * @returns {JSX.Element} The kanji detail view.
 */
export default function KanjiView() {
    const [searchParams] = useSearchParams();
    const char = searchParams.get("char") ?? "";
    const navigate = useNavigate();
    const [info, setInfo] = useState<KanjiInfo | null | undefined>(undefined);
    const [audio, setAudio] = useState<KanjiAudio | null>(null);
    const [words, setWords] = useState<JMEntry[]>([]);
    const [sentences, setSentences] = useState<Example[]>([]);
    const [tab, setTab] = useState("Words");
    const playerRef = useRef<HTMLAudioElement | null>(null);
    const [playingClip, setPlayingClip] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setInfo(undefined);
        setAudio(null);
        setWords([]);
        setSentences([]);
        apiKanji(char)
            .then((k) => {
                if (cancelled) return;
                setInfo(k);
                pushRecentLookup({ kind: "kanji", value: char });
            })
            .catch(() => !cancelled && setInfo(null));
        apiKanjiAudio(char)
            .then((a) => !cancelled && setAudio(a))
            .catch(() => !cancelled && setAudio(null));
        apiKanjiWords(char, 20)
            .then((w) => !cancelled && setWords(w))
            .catch(() => !cancelled && setWords([]));
        apiKanjiSentences(char, 5)
            .then((s) => !cancelled && setSentences(s))
            .catch(() => !cancelled && setSentences([]));
        return () => {
            cancelled = true;
            playerRef.current?.pause();
        };
    }, [char]);

    const playClip = (clip: string) => {
        playerRef.current?.pause();
        const player = new Audio(dictAudioClipUrl(char, clip));
        playerRef.current = player;
        setPlayingClip(clip);
        player.onended = () => setPlayingClip(null);
        player.play().catch(() => setPlayingClip(null));
    };

    if (info === undefined) {
        return (
            <div className="mx-auto max-w-2xl space-y-3">
                <Skeleton className="mx-auto h-48 w-48" />
                <Skeleton className="h-24" />
            </div>
        );
    }

    if (info === null) {
        return <EmptyState title="Nothing Found" description={`No Kanji Data For “${char}”`} />;
    }

    const wordsTab = `Words`;
    const showWords = words.length > 0 && (tab === "Words" || sentences.length === 0);

    return (
        <div className="mx-auto max-w-2xl space-y-5">
            <div className="rounded-card border border-ink/10 bg-surface p-5 shadow-soft sm:p-6">
                <StrokeOrder
                    literal={info.literal}
                    controls
                    numbers
                    className="mx-auto h-48 w-48 text-ink sm:h-56 sm:w-56"
                />

                <div className="mt-4 flex flex-wrap justify-center gap-1.5">
                    {info.stroke_count != null && <Badge>{info.stroke_count} Strokes</Badge>}
                    {info.grade != null && <Badge>Grade {info.grade}</Badge>}
                    {info.jlpt != null && <Badge tone="accent">N{info.jlpt}</Badge>}
                    {info.is_joyo && <Badge tone="success">Joyo</Badge>}
                    {info.freq != null && <Badge>Freq {info.freq}</Badge>}
                </div>

                {info.meanings.length > 0 && (
                    <p className="mt-3 text-center text-ink">{info.meanings.join(", ")}</p>
                )}

                <div className="mt-3 space-y-1.5 text-center text-sm">
                    <ReadingRow label="On" readings={info.onyomi} />
                    <ReadingRow label="Kun" readings={info.kunyomi} />
                    <ReadingRow label="Nanori" readings={info.nanori} />
                </div>

                {audio && audio.clips.length > 0 && (
                    <div className="mt-4 border-t border-ink/10 pt-3">
                        <h3 className="mb-2 text-center text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                            Word Pronunciation
                        </h3>
                        <div className="flex flex-wrap justify-center gap-1.5">
                            {audio.clips.map((clip, i) => (
                                <button
                                    key={clip}
                                    type="button"
                                    onClick={() => playClip(clip)}
                                    aria-label={`Play pronunciation clip ${i + 1}`}
                                    className={cn(
                                        "inline-flex items-center gap-1 rounded-control bg-surface-2 px-2 py-1 text-xs transition-colors",
                                        playingClip === clip
                                            ? "text-shu"
                                            : "text-ink-muted hover:text-shu"
                                    )}
                                >
                                    <Volume2 size={13} />
                                    {i + 1}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {info.radicals.length > 0 && (
                    <div className="mt-4 border-t border-ink/10 pt-3">
                        <h3 className="mb-2 text-center text-2xs font-semibold uppercase tracking-wide text-ink-faint">
                            Radicals
                        </h3>
                        <div className="flex flex-wrap justify-center gap-1.5">
                            {info.radicals.map((r) => (
                                <button
                                    key={r}
                                    type="button"
                                    lang="ja"
                                    onClick={() =>
                                        navigate(
                                            `/dictionary/radicals?picked=${encodeURIComponent(r)}`
                                        )
                                    }
                                    className="rounded-control bg-surface-2 px-2.5 py-1 text-lg text-ink-muted transition-colors hover:bg-shu/15 hover:text-shu"
                                >
                                    {r}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {(words.length > 0 || sentences.length > 0) && (
                <div className="rounded-card border border-ink/10 bg-surface p-4 shadow-soft">
                    <DictTabs
                        tabs={[
                            ...(words.length > 0 ? [wordsTab] : []),
                            ...(sentences.length > 0 ? ["Examples"] : []),
                        ]}
                        active={showWords ? wordsTab : "Examples"}
                        onSelect={(t) => setTab(t === wordsTab ? "Words" : "Examples")}
                    />
                    <div className="max-h-96 overflow-y-auto pt-2">
                        {showWords ? (
                            words.map((entry, i) => (
                                <JMEntryRow
                                    key={i}
                                    entry={entry}
                                    onSelect={(word) =>
                                        navigate(wordRoute(word), {
                                            state: { fromKanji: char },
                                        })
                                    }
                                />
                            ))
                        ) : (
                            <ExamplesSection
                                examples={sentences}
                                onWordClick={(_, word) =>
                                    navigate(wordRoute(word), {
                                        state: { fromKanji: char },
                                    })
                                }
                            />
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
