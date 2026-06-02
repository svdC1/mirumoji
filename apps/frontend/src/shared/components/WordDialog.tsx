/**
 * @packageDocumentation A draggable word lookup: an LLM nuance explanation
 * (typewriter reveal) + dictionary definitions, with an optional "save clip"
 * action when opened from a video. Shared by the player, text analyzer, and
 * transcribe pages.
 */

import { useEffect, useState } from "react";
import { motion, useDragControls } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { Copy, Check, Bookmark } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiDictQuery, isEmptyDict } from "@/shared/dict/api";
import { apiBreakdown, apiGetTemplate } from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { toHiragana } from "@/shared/japanese/kana";
import { createAndSaveClip } from "@/shared/clips/create";
import { cn } from "@/shared/ui";
import type { KotobaseData } from "@/shared/dict/types";
import type { BreakdownResponse } from "@/shared/llm/types";
import type { ClipBreakdown } from "@/shared/clips/types";
import {
    JmdictEntryDisplay,
    JmnedictEntryDisplay,
    KanjiInfoDisplay,
    ExampleDisplay,
} from "./DictDisplays";

export interface WordDialogProps {
    sentence: string;
    word: string;
    onClose: () => void;
    cueStart: number;
    cueEnd: number;
    videoFile: File | null;
    videoUrl?: string;
}

// Cache breakdown responses for already-clicked words.
const breakdownCache = new Map<string, BreakdownResponse>();

// A profile template's prompt uses {sentence}/{focus}; the API expects {0}/{1}.
const toApiPrompt = (prompt: string): string =>
    prompt.replace(/{sentence}/g, "{0}").replace(/{focus}/g, "{1}");

type MainTab = "llm" | "dict";
type DictTab = "jmdict" | "jmnedict" | "kanji" | "examples";

/**
 * The WordDialog component.
 *
 * @param {WordDialogProps} props The props.
 * @returns {JSX.Element} The dialog.
 */
export default function WordDialog({
    sentence,
    word,
    onClose,
    cueStart,
    cueEnd,
    videoFile,
    videoUrl,
}: WordDialogProps) {
    const key = `${sentence}__${word}`;
    const [data, setData] = useState<BreakdownResponse | null>(breakdownCache.get(key) ?? null);
    const [tab, setTab] = useState<MainTab>("dict");
    const [noModel, setNoModel] = useState(false);
    const [dictTab, setDictTab] = useState<DictTab>("jmdict");
    const [copied, setCopied] = useState(false);
    const [saving, setSaving] = useState(false);
    const [dictData, setDictData] = useState<KotobaseData | null | undefined>(undefined);

    const [screenWidth, setScreenWidth] = useState(
        typeof window !== "undefined" ? window.innerWidth : 0
    );
    const dragControls = useDragControls();

    useEffect(() => {
        if (typeof window === "undefined") return;
        const handleResize = () => setScreenWidth(window.innerWidth);
        window.addEventListener("resize", handleResize);
        handleResize();
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    const isMobile = screenWidth < 1380;
    const canSaveClip = !!(videoFile || videoUrl);

    const fetchBreakdown = async (): Promise<BreakdownResponse | null> => {
        const cached = breakdownCache.get(key);
        if (cached) {
            setData(cached);
            return cached;
        }
        try {
            // Model (+ optional sys_msg/prompt) comes from the profile template;
            // without one, the LLM features stay disabled.
            const template = await apiGetTemplate();
            if (!template) {
                setNoModel(true);
                return null;
            }
            setNoModel(false);

            const useCustomPrompt =
                template.prompt.includes("{sentence}") && template.prompt.includes("{focus}");

            const json = await apiBreakdown({
                sentence,
                focus: word,
                model: template.model,
                sys_msg: template.sys_msg || undefined,
                prompt: useCustomPrompt ? toApiPrompt(template.prompt) : undefined,
            });
            breakdownCache.set(key, json);
            setData(json);
            return json;
        } catch (e) {
            toastApiError(e);
            onClose();
            throw e;
        }
    };

    useEffect(() => {
        if (data || tab !== "llm") return;
        fetchBreakdown().catch(() => {});
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [key, data, tab]);

    // Typewriter reveal of the explanation.
    const [typed, setTyped] = useState("");
    useEffect(() => {
        const full = data?.explanation ?? "";
        setTyped("");
        if (!full) return;
        let i = 0;
        const id = window.setInterval(() => {
            i += 2;
            setTyped(full.slice(0, i));
            if (i >= full.length) window.clearInterval(id);
        }, 12);
        return () => window.clearInterval(id);
    }, [data]);

    useEffect(() => {
        if (tab !== "dict") return;
        setDictData(undefined);
        apiDictQuery(word)
            .then((entry) => {
                if (isEmptyDict(entry)) {
                    setDictData(null);
                    return;
                }
                setDictData(entry);
                if (entry.jmentries.length === 0) {
                    if (entry.jmnentries.length > 0) setDictTab("jmnedict");
                    else if (entry.kanji.length > 0) setDictTab("kanji");
                    else if (entry.examples.length > 0) setDictTab("examples");
                }
            })
            .catch((e) => {
                console.error("apiDictQuery error", e);
                setDictData(null);
                toastApiError(e);
            });
    }, [tab, word]);

    const handleCopy = () => {
        let textToCopy = "";
        if (tab === "llm" && data) {
            const focus = data.focus;
            textToCopy = [
                ...(focus ? [focus.word.surface] : []),
                ...(focus?.word.reading ? [toHiragana(focus.word.reading)] : []),
                ...(focus?.kotobase_data.meanings ?? []),
                "",
                data.explanation,
            ].join("\n");
        } else if (tab === "dict" && dictData) {
            textToCopy = JSON.stringify(dictData);
        }
        if (textToCopy) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            });
        }
    };

    const handleSave = async () => {
        const clipToastId = "clip-save-toast";
        if (!canSaveClip) {
            toast.error("No Video Source Available");
            return;
        }
        setSaving(true);
        try {
            let breakdown = data;
            if (!breakdown) {
                toast.loading("Fetching explanation...", { id: clipToastId });
                breakdown = await fetchBreakdown();
            }
            if (!breakdown) {
                toast.error("Configure An LLM Model In Your Profile To Save Clips.", {
                    id: clipToastId,
                });
                setSaving(false);
                return;
            }

            const clipBreakdown: ClipBreakdown = { ...breakdown, sentence };
            const onProgress = (message: string, type: "success" | "error" | "loading") => {
                if (type === "loading") toast.loading(message, { id: clipToastId });
                else if (type === "success") toast.success(message, { id: clipToastId });
                else toast.error(message, { id: clipToastId });
            };

            await createAndSaveClip("mirumoji-player", cueStart, cueEnd, clipBreakdown, onProgress);
        } catch (error) {
            console.error("Failed to save clip from WordDialog:", error);
            toast.error("Failed To Save Clip", { id: clipToastId });
        } finally {
            setSaving(false);
        }
    };

    const tabClasses = (active: boolean) =>
        cn(
            "flex-1 py-2 text-sm transition-colors sm:text-base",
            active ? "border-b-2 border-shu text-ink" : "text-ink-faint hover:text-ink-muted"
        );

    const dictSubTab = (active: boolean) =>
        cn(
            "flex-1 py-2 text-sm transition-colors",
            active ? "border-b-2 border-ai text-ink" : "text-ink-faint hover:text-ink-muted"
        );

    return (
        <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
                drag
                dragListener={!isMobile}
                dragControls={dragControls}
                dragMomentum={false}
                className="pointer-events-auto relative max-h-[70vh] w-full max-w-lg overflow-y-auto rounded-card border border-ink/10 bg-surface p-6 text-lg text-ink shadow-lift"
            >
                {isMobile && (
                    <div
                        onPointerDown={(event) =>
                            dragControls.start(event, { snapToCursor: false })
                        }
                        className="absolute left-0 right-0 top-0 z-20 flex h-10 cursor-grab items-center justify-center"
                        style={{ touchAction: "none" }}
                    >
                        <div className="mt-1 h-1.5 w-10 rounded-full bg-ink/30" />
                    </div>
                )}

                <div className={isMobile ? "pt-8" : ""}>
                    <div className="absolute right-4 top-3 z-30 flex space-x-3">
                        {canSaveClip && (
                            <button
                                className={cn(
                                    "transition-colors",
                                    saving ? "text-ink-faint" : "text-ink-muted hover:text-matcha"
                                )}
                                onClick={handleSave}
                                disabled={saving}
                                aria-label="Save clip"
                            >
                                <Bookmark size={22} />
                            </button>
                        )}
                        <button
                            className="text-ink-muted transition-colors hover:text-ai"
                            onClick={handleCopy}
                            aria-label="Copy content"
                        >
                            {copied ? <Check size={22} /> : <Copy size={22} />}
                        </button>
                        <button
                            className="text-2xl leading-none text-ink-muted hover:text-ink"
                            onClick={onClose}
                            aria-label="Close"
                        >
                            ×
                        </button>
                    </div>

                    <div
                        className={cn(
                            "mb-4 flex border-b border-ink/10",
                            isMobile ? "mt-6" : "mt-2"
                        )}
                    >
                        <button className={tabClasses(tab === "llm")} onClick={() => setTab("llm")}>
                            LLM
                        </button>
                        <button
                            className={tabClasses(tab === "dict")}
                            onClick={() => setTab("dict")}
                        >
                            Dictionary
                        </button>
                    </div>

                    {tab === "llm" ? (
                        noModel ? (
                            <div className="py-6 text-center italic text-ink-muted">
                                Configure an LLM model in your Profile (Dashboard &rarr; LLM
                                Template) to enable explanations.
                            </div>
                        ) : !data ? (
                            <div className="w-full space-y-4">
                                <div className="h-6 w-1/3 animate-pulse rounded bg-ink/10" />
                                {Array.from({ length: 4 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className="h-4 w-full animate-pulse rounded bg-ink/10"
                                    />
                                ))}
                            </div>
                        ) : (
                            <>
                                <h2 lang="ja" className="mb-1 font-display text-xl font-bold">
                                    {data.focus?.word.surface ?? word}
                                </h2>
                                {data.focus &&
                                (data.focus.word.reading ||
                                    data.focus.kotobase_data.meanings.length) ? (
                                    <div className="mb-3 mt-1 text-base leading-relaxed text-ink-muted">
                                        {data.focus.word.reading && (
                                            <span lang="ja" className="mr-2 italic">
                                                {toHiragana(data.focus.word.reading)}
                                            </span>
                                        )}
                                        {data.focus.kotobase_data.meanings.length > 0 && (
                                            <span>
                                                {data.focus.kotobase_data.meanings.join("；")}
                                            </span>
                                        )}
                                    </div>
                                ) : null}
                                <ReactMarkdown
                                    className="prose prose-sm prose-invert max-w-none whitespace-pre-wrap sm:prose-base"
                                    remarkPlugins={[remarkGfm, remarkBreaks]}
                                >
                                    {typed}
                                </ReactMarkdown>
                            </>
                        )
                    ) : dictData === undefined ? (
                        <p className="text-center italic text-ink-muted">Loading dictionary…</p>
                    ) : dictData === null ? (
                        <p className="text-center italic text-ink-muted">
                            No dictionary entry found for &quot;{word}&quot;.
                        </p>
                    ) : (
                        <div>
                            <div className="mb-2 flex border-b border-ink/10">
                                {dictData.jmentries.length > 0 && (
                                    <button
                                        className={dictSubTab(dictTab === "jmdict")}
                                        onClick={() => setDictTab("jmdict")}
                                    >
                                        Common
                                    </button>
                                )}
                                {dictData.jmnentries.length > 0 && (
                                    <button
                                        className={dictSubTab(dictTab === "jmnedict")}
                                        onClick={() => setDictTab("jmnedict")}
                                    >
                                        Proper Nouns
                                    </button>
                                )}
                                {dictData.kanji.length > 0 && (
                                    <button
                                        className={dictSubTab(dictTab === "kanji")}
                                        onClick={() => setDictTab("kanji")}
                                    >
                                        Kanji
                                    </button>
                                )}
                                {dictData.examples.length > 0 && (
                                    <button
                                        className={dictSubTab(dictTab === "examples")}
                                        onClick={() => setDictTab("examples")}
                                    >
                                        Examples
                                    </button>
                                )}
                            </div>
                            {dictTab === "jmdict" ? (
                                <div>
                                    {dictData.jmentries.map((entry, i) => (
                                        <JmdictEntryDisplay
                                            key={i}
                                            entry={entry}
                                            isLast={i === dictData.jmentries.length - 1}
                                        />
                                    ))}
                                </div>
                            ) : dictTab === "jmnedict" ? (
                                <div>
                                    {dictData.jmnentries.map((entry, i) => (
                                        <JmnedictEntryDisplay
                                            key={i}
                                            entry={entry}
                                            isLast={i === dictData.jmnentries.length - 1}
                                        />
                                    ))}
                                </div>
                            ) : dictTab === "kanji" ? (
                                <div>
                                    {dictData.kanji.map((kanji, i) => (
                                        <KanjiInfoDisplay
                                            key={i}
                                            kanjiInfo={kanji}
                                            isLast={i === dictData.kanji.length - 1}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div>
                                    {dictData.examples.map((ex, i) => (
                                        <ExampleDisplay
                                            key={i}
                                            example={ex}
                                            isLast={i === dictData.examples.length - 1}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
