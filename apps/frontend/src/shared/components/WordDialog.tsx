/**
 * @packageDocumentation A draggable word lookup: a streamed LLM nuance
 * explanation + a dictionary reference organized into collapsible sections
 * (Entry, Kanji, Examples, Grammar), with an optional "save clip" action when
 * opened from a video and a deep link into the Dictionary hub. Shared by the
 * player, text analyzer, and transcribe pages.
 *
 * Gesture layering: dragging is owned by the header grab bar (moving only the
 * panel transform) while scrolling happens inside the body, so the two never
 * fight and in-flight stroke animations keep running through a drag.
 */

import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useDragControls } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import {
    ArrowUpRight,
    Bookmark,
    BookOpen,
    Check,
    ChevronRight,
    Copy,
    Sparkles,
} from "lucide-react";
import { toast } from "react-hot-toast";
import { apiDictQuery, apiTokenize, isEmptyDict } from "@/shared/dict/api";
import { wordRoute } from "@/shared/dict/routes";
import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { apiGetTemplate, streamBreakdown } from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { toHiragana } from "@/shared/japanese/kana";
import { createAndSaveClip } from "@/shared/clips/create";
import { warmupRecorder } from "@/shared/clips/recorder";
import { Badge, cn } from "@/shared/ui";
import type { EnrichedJapaneseWord, KotobaseData, Token } from "@/shared/dict/types";
import type { BreakdownResponse } from "@/shared/llm/types";
import type { ClipBreakdown } from "@/shared/clips/types";
import {
    ExamplesSection,
    GrammarSection,
    JmdictEntryDisplay,
    JmnedictEntryDisplay,
    KanjiCard,
} from "@/shared/components/DictDisplays";
import FuriganaText from "./FuriganaText";
import { ExplanationSkeleton } from "./ExplanationSkeleton";

export interface WordDialogProps {
    sentence: string;
    word: string;
    onClose: () => void;
    cueStart: number;
    cueEnd: number;
    videoFile: File | null;
    videoUrl?: string;
    /** Surrounding subtitle lines, exposed to the template as {context}. */
    context?: string;
}

// Cache breakdown responses for already-clicked words.
const breakdownCache = new Map<string, BreakdownResponse>();

type MainTab = "llm" | "dict";
type SectionKey = "entry" | "names" | "kanji" | "examples" | "grammar";

/**
 * One collapsible dictionary section: a compact header row when closed,
 * expanding to its content when open.
 *
 * @param {object} props The section title/count, open state, and content.
 * @returns {JSX.Element} The section.
 */
function Section({
    title,
    count,
    open,
    onToggle,
    children,
}: {
    title: string;
    count?: number;
    open: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}) {
    return (
        <div className="border-b border-ink/10 last:border-b-0">
            <button
                type="button"
                onClick={onToggle}
                aria-expanded={open}
                className="flex w-full items-center gap-1.5 py-2.5 text-left text-sm font-medium text-ink transition-colors hover:text-shu"
            >
                <ChevronRight
                    size={15}
                    className={cn("shrink-0 transition-transform", open && "rotate-90")}
                />
                {title}
                {count != null && <span className="text-ink-faint">({count})</span>}
            </button>
            {open && <div className="pb-3">{children}</div>}
        </div>
    );
}

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
    context,
}: WordDialogProps) {
    const key = `${sentence}__${word}__${context ?? ""}`;
    const cached = breakdownCache.get(key);
    const [focus, setFocus] = useState<EnrichedJapaneseWord | null>(cached?.focus ?? null);
    const [explanation, setExplanation] = useState<string>(cached?.explanation ?? "");
    // The streamed buffer (`explanation`) is revealed by a typewriter into
    // `displayed`, so the answer types out smoothly as the stream arrives.
    const [displayed, setDisplayed] = useState<string>(cached?.explanation ?? "");
    const [streaming, setStreaming] = useState(false);
    const [tab, setTab] = useState<MainTab>("dict");
    const [noModel, setNoModel] = useState(false);
    const [openSection, setOpenSection] = useState<SectionKey | null>("entry");
    const [copied, setCopied] = useState(false);
    const [saving, setSaving] = useState(false);
    const [dictData, setDictData] = useState<KotobaseData | null | undefined>(undefined);
    // Morphology of the word (tokenized directly, no LLM needed) backing the
    // Grammar section.
    const [dictTokens, setDictTokens] = useState<Token[]>([]);

    // Reset the LLM breakdown when the dialog moves to a new word/sentence (the
    // dialog instance is reused across clicks), so it never shows a stale answer.
    const [prevKey, setPrevKey] = useState(key);
    if (key !== prevKey) {
        setPrevKey(key);
        const c = breakdownCache.get(key);
        setFocus(c?.focus ?? null);
        setExplanation(c?.explanation ?? "");
        setDisplayed(c?.explanation ?? "");
        setStreaming(false);
        setNoModel(false);
    }

    const { mode } = useBundleSettings();
    const dragControls = useDragControls();
    const bodyRef = useRef<HTMLDivElement>(null);

    // Typewriter: reveal `displayed` toward the streamed `explanation` buffer,
    // taking bigger steps when further behind so it keeps up with a fast stream
    // without ever jumping a whole chunk in at once.
    useEffect(() => {
        if (displayed.length >= explanation.length) return;
        const remaining = explanation.length - displayed.length;
        const step = Math.max(2, Math.ceil(remaining / 12));
        const id = window.setTimeout(() => {
            setDisplayed(explanation.slice(0, displayed.length + step));
        }, 16);
        return () => window.clearTimeout(id);
    }, [displayed, explanation]);

    // Follow the text as it types, but only when the reader is already near the
    // bottom, so scrolling up to re-read isn't fought.
    useEffect(() => {
        const el = bodyRef.current;
        if (!el || displayed.length >= explanation.length) return;
        if (el.scrollHeight - el.scrollTop - el.clientHeight < 120) {
            el.scrollTop = el.scrollHeight;
        }
    }, [displayed, explanation]);

    const canSaveClip = !!(videoFile || videoUrl);

    // Streams the breakdown: the focus word, then the explanation token by token
    // (no typewriter — the stream itself is the reveal). The final result is
    // cached so re-opening the same word is instant.
    const runBreakdown = async (signal?: AbortSignal): Promise<BreakdownResponse | null> => {
        const cachedNow = breakdownCache.get(key);
        if (cachedNow) {
            setFocus(cachedNow.focus);
            setExplanation(cachedNow.explanation);
            setDisplayed(cachedNow.explanation);
            return cachedNow;
        }
        let template;
        try {
            // Model (+ optional sys_msg/prompt) comes from the profile template;
            // without one, the LLM features stay disabled.
            template = await apiGetTemplate();
        } catch (e) {
            toastApiError(e);
            onClose();
            return null;
        }
        if (!template) {
            setNoModel(true);
            return null;
        }
        setNoModel(false);

        let focusWord: EnrichedJapaneseWord | null = null;
        let text = "";
        setStreaming(true);
        try {
            await streamBreakdown(
                {
                    sentence,
                    focus: word,
                    model: template.model,
                    sys_msg: template.sys_msg || undefined,
                    prompt: template.prompt || undefined,
                    context: context || undefined,
                },
                {
                    onFocus: (f) => {
                        focusWord = f;
                        setFocus(f);
                    },
                    onToken: (t) => {
                        text += t;
                        setExplanation(text);
                    },
                },
                signal
            );
        } catch (e) {
            if (signal?.aborted) return null;
            toastApiError(e);
            onClose();
            return null;
        } finally {
            setStreaming(false);
        }
        const result: BreakdownResponse = { focus: focusWord, explanation: text };
        breakdownCache.set(key, result);
        return result;
    };

    useEffect(() => {
        if (tab !== "llm") return;
        if (breakdownCache.get(key) || explanation || streaming) return;
        const controller = new AbortController();
        runBreakdown(controller.signal).catch(() => {});
        return () => controller.abort();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [key, tab]);

    // Tokenize the sentence first (fast local morphology) and pick the
    // clicked word's bundle out of it: its in-context reading + part of
    // speech rank the dictionary entries (a lone word tokenized without
    // context could resolve to a different reading), and its tokens back the
    // Grammar section. Then look the word up with those hints. Loaded
    // regardless of the active tab so the LLM heading can show the
    // dictionary reading rather than the streamed focus event.
    useEffect(() => {
        let cancelled = false;
        setDictData(undefined);
        setDictTokens([]);

        const run = async () => {
            let hints: { reading?: string; pos?: string } | undefined;
            try {
                const ws = await apiTokenize(sentence, mode);
                if (cancelled) return;
                // The dialog's word is a lemma from this same tokenization,
                // so matching by lemma recovers the clicked bundle
                const clicked = ws.find((w) => w.lemma === word);
                if (clicked) {
                    setDictTokens(clicked.tokens);
                    hints = {
                        reading: clicked.reading || undefined,
                        pos: clicked.pos || undefined,
                    };
                } else {
                    // A word absent from the sentence (opened from outside
                    // tokenized text) tokenizes alone as the fallback
                    const lone = await apiTokenize(word, mode);
                    if (cancelled) return;
                    setDictTokens(lone.flatMap((w) => w.tokens));
                    const reading = lone.map((w) => w.reading).join("");
                    hints = {
                        reading: reading || undefined,
                        pos: lone[0]?.pos || undefined,
                    };
                }
            } catch {
                // Tokenization only provides hints here; the lookup proceeds
                // without them
            }
            try {
                const entry = await apiDictQuery(word, false, hints);
                if (cancelled) return;
                setDictData(isEmptyDict(entry) ? null : entry);
                // Open the first section that has content for this word
                if (entry.jmentries.length > 0) setOpenSection("entry");
                else if (entry.jmnentries.length > 0) setOpenSection("names");
                else if (entry.kanji.length > 0) setOpenSection("kanji");
                else setOpenSection("examples");
            } catch (e) {
                if (cancelled) return;
                console.error("apiDictQuery error", e);
                setDictData(null);
                toastApiError(e);
            }
        };
        run();
        return () => {
            cancelled = true;
        };
    }, [sentence, word, mode]);

    const handleCopy = () => {
        let textToCopy = "";
        if (tab === "llm" && (focus || explanation)) {
            textToCopy = [
                ...(focus ? [focus.word.surface] : []),
                ...(focus?.word.reading ? [toHiragana(focus.word.reading)] : []),
                ...(focus?.kotobase_data.meanings ?? []),
                "",
                explanation,
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
        // Resume the recorder's AudioContext now, while the click gesture is
        // still active. The breakdown fetch below can take seconds, after which
        // the activation is spent and the iOS canvas-fallback recorder can no
        // longer bring up its audio pipeline.
        warmupRecorder();
        setSaving(true);
        try {
            let breakdown = breakdownCache.get(key) ?? null;
            if (!breakdown) {
                toast.loading("Fetching explanation...", { id: clipToastId });
                breakdown = await runBreakdown();
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

    const toggle = (section: SectionKey) =>
        setOpenSection((current) => (current === section ? null : section));

    // Words in examples and cross-references open their entry in the
    // Dictionary hub in a new tab, so playback never stops. BASE_URL keeps
    // the link working under a non-root deployment base, so the route helper's
    // leading slash is dropped to sit after it
    const openInDict = (target: string) =>
        window.open(
            `${import.meta.env.BASE_URL}${wordRoute(target).slice(1)}`,
            "_blank",
            "noreferrer"
        );

    const reading = dictData?.jmentries[0]?.kana[0] || dictData?.jmnentries[0]?.kana[0] || "";
    const firstEntry = dictData?.jmentries[0];
    // The ruby annotation already shows the reading, so the italic reading
    // beside the headword only appears when no furigana is known
    const showReading = !!reading && (dictData?.furigana.length ?? 0) === 0;

    return (
        <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
                drag
                dragListener={false}
                dragControls={dragControls}
                dragMomentum={false}
                className="pointer-events-auto relative flex max-h-[75vh] w-full max-w-lg flex-col overflow-hidden rounded-card border border-ink/10 bg-surface text-ink shadow-lift"
            >
                {/* Grab bar: the only drag surface, so scrolling inside the
                    body never starts a drag. */}
                <div
                    onPointerDown={(event) => dragControls.start(event, { snapToCursor: false })}
                    className="flex h-8 shrink-0 cursor-grab items-center justify-center active:cursor-grabbing"
                    style={{ touchAction: "none" }}
                >
                    <div className="h-1.5 w-10 rounded-full bg-ink/30" />
                </div>

                <div className="absolute right-4 top-2.5 z-30 flex space-x-3">
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
                            <Bookmark size={20} />
                        </button>
                    )}
                    <button
                        className="text-ink-muted transition-colors hover:text-ai"
                        onClick={handleCopy}
                        aria-label="Copy content"
                    >
                        {copied ? <Check size={20} /> : <Copy size={20} />}
                    </button>
                    <button
                        className="text-2xl leading-none text-ink-muted hover:text-ink"
                        onClick={onClose}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                <div className="flex shrink-0 border-b border-ink/10 px-5">
                    <button
                        className={tabClasses(tab === "llm")}
                        onClick={() => setTab("llm")}
                        aria-label="LLM Explanation"
                        title="LLM Explanation"
                    >
                        <Sparkles size={18} className="mx-auto" />
                    </button>
                    <button
                        className={tabClasses(tab === "dict")}
                        onClick={() => setTab("dict")}
                        aria-label="Dictionary"
                        title="Dictionary"
                    >
                        <BookOpen size={18} className="mx-auto" />
                    </button>
                </div>

                {/* Body: scrolls internally without touching the drag transform. */}
                <div ref={bodyRef} className="min-h-0 flex-1 overflow-y-auto px-5 pb-4 pt-3">
                    {tab === "llm" ? (
                        noModel ? (
                            <div className="py-6 text-center italic text-ink-muted">
                                Configure an LLM model in your Profile (Dashboard &rarr; LLM
                                Template) to enable explanations.
                            </div>
                        ) : !explanation ? (
                            <ExplanationSkeleton />
                        ) : (
                            <motion.div
                                initial={{ opacity: 0, y: 6 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.25, ease: "easeOut" }}
                            >
                                <div className="mb-3 flex flex-wrap items-baseline gap-x-2.5 gap-y-1 border-b border-ink/10 pb-3">
                                    <h2 lang="ja" className="font-display text-2xl font-bold">
                                        {word}
                                    </h2>
                                    {reading && (
                                        <span lang="ja" className="text-base italic text-ink-muted">
                                            {reading}
                                        </span>
                                    )}
                                </div>
                                <ReactMarkdown
                                    className="prose prose-invert max-w-none whitespace-pre-wrap"
                                    remarkPlugins={[remarkGfm, remarkBreaks]}
                                >
                                    {displayed}
                                </ReactMarkdown>
                            </motion.div>
                        )
                    ) : dictData === undefined ? (
                        <p className="text-center italic text-ink-muted">Loading dictionary…</p>
                    ) : dictData === null ? (
                        <p className="text-center italic text-ink-muted">
                            No dictionary entry found for &quot;{word}&quot;.
                        </p>
                    ) : (
                        <div>
                            <div className="mb-1 flex flex-wrap items-center gap-x-2.5 gap-y-1 border-b border-ink/10 pb-3">
                                <h2 className="font-display text-2xl font-bold">
                                    <FuriganaText
                                        segments={dictData.furigana}
                                        fallback={dictData.query || word}
                                    />
                                </h2>
                                <Link
                                    to={wordRoute(word)}
                                    target="_blank"
                                    rel="noreferrer"
                                    aria-label="Open in Dictionary"
                                    title="Open In Dictionary"
                                    className="text-ink-muted transition-colors hover:text-shu"
                                >
                                    <ArrowUpRight size={18} />
                                </Link>
                                {showReading && (
                                    <span lang="ja" className="text-base italic text-ink-muted">
                                        {reading}
                                    </span>
                                )}
                                {firstEntry?.is_common && <Badge tone="success">Common</Badge>}
                                {dictData.jlpt !== "Unknown" && (
                                    <Badge tone="accent">{dictData.jlpt}</Badge>
                                )}
                            </div>

                            {dictData.jmentries.length > 0 && (
                                <Section
                                    title="Entry"
                                    count={dictData.jmentries.length}
                                    open={openSection === "entry"}
                                    onToggle={() => toggle("entry")}
                                >
                                    {dictData.jmentries.map((entry, i) => (
                                        <JmdictEntryDisplay
                                            key={i}
                                            entry={entry}
                                            isLast={i === dictData.jmentries.length - 1}
                                            onRefClick={(ref) => openInDict(ref.split("・")[0])}
                                        />
                                    ))}
                                </Section>
                            )}

                            {dictData.jmnentries.length > 0 && (
                                <Section
                                    title="Names"
                                    count={dictData.jmnentries.length}
                                    open={openSection === "names"}
                                    onToggle={() => toggle("names")}
                                >
                                    {dictData.jmnentries.map((entry, i) => (
                                        <JmnedictEntryDisplay
                                            key={i}
                                            entry={entry}
                                            isLast={i === dictData.jmnentries.length - 1}
                                        />
                                    ))}
                                </Section>
                            )}

                            {dictData.kanji.length > 0 && (
                                <Section
                                    title="Kanji"
                                    count={dictData.kanji.length}
                                    open={openSection === "kanji"}
                                    onToggle={() => toggle("kanji")}
                                >
                                    {dictData.kanji.map((kanji, i) => (
                                        <KanjiCard
                                            key={kanji.literal}
                                            kanji={kanji}
                                            isLast={i === dictData.kanji.length - 1}
                                        />
                                    ))}
                                </Section>
                            )}

                            {dictData.examples.length > 0 && (
                                <Section
                                    title="Examples"
                                    count={dictData.examples.length}
                                    open={openSection === "examples"}
                                    onToggle={() => toggle("examples")}
                                >
                                    <ExamplesSection
                                        examples={dictData.examples}
                                        onWordClick={(_, w) => openInDict(w)}
                                    />
                                </Section>
                            )}

                            {dictTokens.length > 0 && (
                                <Section
                                    title="Grammar"
                                    open={openSection === "grammar"}
                                    onToggle={() => toggle("grammar")}
                                >
                                    <GrammarSection tokens={dictTokens} />
                                </Section>
                            )}
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
