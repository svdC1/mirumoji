/**
 * @packageDocumentation This component displays a dialog with information about a word.
 * It includes a GPT-powered explanation, dictionary definitions, and the ability to save a clip of the word being used.
 */

import React, { useEffect, useState } from "react";
import { motion, useDragControls } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { Copy, Check, Bookmark } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiDictQuery, isEmptyDict } from "../services/dictApi";
import { apiBreakdown, apiGetTemplate } from "../services/llmApi";
import { toastApiError } from "../utils/apiErrorToaster";
import { WordDialogProps, KotobaseData, BreakdownResponse, ClipBreakdown } from "../types/types";
import { createAndSaveClip } from "../utils/clipCreator";
import {
    JmdictEntryDisplay,
    JmnedictEntryDisplay,
    KanjiInfoDisplay,
    ExampleDisplay,
} from "./DictDisplays";
import { toHiragana } from "../utils/languageUtils";

// Cache breakdown responses for already-clicked words
const breakdownCache = new Map<string, BreakdownResponse>();

// A profile template's prompt uses {sentence}/{focus}; the API expects {0}/{1}.
const toApiPrompt = (prompt: string): string =>
    prompt.replace(/{sentence}/g, "{0}").replace(/{focus}/g, "{1}");

/**
 * The WordDialog component.
 *
 * This component is responsible for the following:
 * - Displaying information about a word, including a GPT-powered explanation and dictionary definitions.
 * - Allowing the user to save a clip of the word being used in the video.
 *
 * @param {WordDialogProps} props The props for the component.
 * @returns {JSX.Element} The WordDialog component.
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
    // Key for Cache
    const key = `${sentence}__${word}`;
    const [data, setData] = useState<BreakdownResponse | null>(breakdownCache.get(key) ?? null);
    // Main Tabs State
    const [tab, setTab] = useState<"llm" | "dict">("dict");
    // Whether the profile has an LLM model configured (gates the LLM tab)
    const [noModel, setNoModel] = useState(false);
    // Dictionary SubTabs State
    const [dictTab, setDictTab] = useState<"jmdict" | "jmnedict" | "kanji" | "examples">("jmdict");
    // Copied to Clipboard State
    const [copied, setCopied] = useState(false);
    // Saving Clip State
    const [saving, setSaving] = useState(false);
    // Dictionary Data from API
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
    // Check if loaded on a player context
    const canSaveClip = !!(videoFile || videoUrl);

    const fetchBreakdown = async (): Promise<BreakdownResponse | null> => {
        // Return cache if present
        const cached = breakdownCache.get(key);
        if (cached) {
            setData(cached);
            return cached;
        }

        try {
            // The model (+ optional sys_msg/prompt) comes from the profile's
            // LLM template; without one, the LLM features stay disabled.
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
    }, [key, data, sentence, word, tab, onClose]);

    // Typewriter reveal of the explanation
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
                // Set Default SubTab when common entries aren't available
                if (entry.jmentries.length === 0) {
                    if (entry.jmnentries.length > 0) {
                        setDictTab("jmnedict");
                    } else if (entry.kanji.length > 0) {
                        setDictTab("kanji");
                    } else if (entry.examples.length > 0) {
                        setDictTab("examples");
                    }
                }
            })
            .catch((e) => {
                console.error("apiDictQuery error", e);
                setDictData(null);
                toastApiError(e);
            });
    }, [tab, word]);

    // Copy to Clipboard Functionality
    const handleCopy = () => {
        let textToCopy = "";

        // Copy LLM Data as string
        if (tab === "llm" && data) {
            const focus = data.focus;
            textToCopy = [
                ...(focus ? [focus.word.surface] : []),
                ...(focus?.word.reading ? [toHiragana(focus.word.reading)] : []),
                ...(focus?.kotobase_data.meanings ?? []),
                "",
                data.explanation,
            ].join("\n");
            // Copy Dict Data as JSON String
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

    // Save Clip Functionality
    const handleSave = async () => {
        const clipToastId = "clip-save-toast";
        if (!canSaveClip) {
            toast.error("No video source available");
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
                toast.error("Configure an LLM model in your Profile to save clips.", {
                    id: clipToastId,
                });
                setSaving(false);
                return;
            }

            const clipBreakdown: ClipBreakdown = { ...breakdown, sentence };

            // Handle clipCreator callback on UI
            const onProgress = (message: string, type: "success" | "error" | "loading") => {
                switch (type) {
                    case "loading":
                        toast.loading(message, { id: clipToastId });
                        break;
                    case "success":
                        toast.success(message, { id: clipToastId });
                        break;
                    case "error":
                        toast.error(message, { id: clipToastId });
                        break;
                }
            };

            await createAndSaveClip(
                "mirumoji-player", // The ID of the main video player
                cueStart,
                cueEnd,
                clipBreakdown,
                onProgress
            );
        } catch (error) {
            console.error("Failed to save clip from WordDialog:", error);
            toast.error("Failed to Save Clip", { id: clipToastId });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 pointer-events-none p-4">
            <motion.div
                drag={true}
                dragListener={!isMobile}
                dragControls={dragControls}
                dragMomentum={false}
                className="bg-neutral-800 rounded-xl p-6 w-full max-w-lg max-h-[70vh] overflow-y-auto relative text-lg pointer-events-auto"
            >
                {isMobile && (
                    <div
                        onPointerDown={(event) =>
                            dragControls.start(event, { snapToCursor: false })
                        }
                        className="absolute top-0 left-0 right-0 h-10 flex justify-center items-center cursor-grab z-20"
                        style={{ touchAction: "none" }}
                    >
                        <div className="w-10 h-1.5 bg-neutral-500 rounded-full mt-1" />
                    </div>
                )}

                <div className={`${isMobile ? "pt-8" : ""}`}>
                    <div className="absolute top-3 right-4 flex space-x-3 z-30">
                        {canSaveClip && (
                            <button
                                className={`text-2xl transition-colors ${
                                    saving ? "text-gray-500" : "hover:text-emerald-400"
                                }`}
                                onClick={handleSave}
                                disabled={saving}
                                aria-label="Save clip"
                            >
                                <Bookmark size={22} />
                            </button>
                        )}
                        <button
                            className="text-2xl hover:text-teal-300 transition-colors"
                            onClick={handleCopy}
                            aria-label="Copy content"
                        >
                            {copied ? <Check size={22} /> : <Copy size={22} />}
                        </button>
                        <button className="text-2xl" onClick={onClose} aria-label="Close">
                            ×
                        </button>
                    </div>
                    <div
                        className={`flex border-b border-neutral-700 mb-4 ${
                            isMobile ? "mt-6" : "mt-2"
                        }`}
                    >
                        <button
                            className={`flex-1 py-2 text-sm sm:text-base ${
                                tab === "llm"
                                    ? "border-b-2 border-emerald-400 text-white"
                                    : "text-neutral-400 hover:text-neutral-200"
                            }`}
                            onClick={() => setTab("llm")}
                        >
                            LLM
                        </button>
                        <button
                            className={`flex-1 py-2 text-sm sm:text-base ${
                                tab === "dict"
                                    ? "border-b-2 border-emerald-400 text-white"
                                    : "text-neutral-400 hover:text-neutral-200"
                            }`}
                            onClick={() => setTab("dict")}
                        >
                            Dictionary
                        </button>
                    </div>
                    {tab === "llm" ? (
                        noModel ? (
                            <div className="text-center text-neutral-400 italic py-6">
                                Configure an LLM model in your Profile (Dashboard &rarr; LLM
                                Template) to enable explanations.
                            </div>
                        ) : !data ? (
                            <div className="w-full space-y-4">
                                <div className="h-6 w-1/3 rounded bg-neutral-700 animate-pulse" />
                                {Array.from({ length: 4 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className="h-4 w-full rounded bg-neutral-700 animate-pulse"
                                    />
                                ))}
                            </div>
                        ) : (
                            <>
                                <h2 className="text-xl font-bold mb-1">
                                    {data.focus?.word.surface ?? word}
                                </h2>
                                {data.focus &&
                                (data.focus.word.reading ||
                                    data.focus.kotobase_data.meanings.length) ? (
                                    <div className="mt-1 mb-3 text-neutral-300 text-base leading-relaxed">
                                        {data.focus.word.reading && (
                                            <span className="mr-2 italic">
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
                                    className="prose prose-sm sm:prose-base prose-invert max-w-none whitespace-pre-wrap"
                                    remarkPlugins={[remarkGfm, remarkBreaks]}
                                >
                                    {typed}
                                </ReactMarkdown>
                            </>
                        )
                    ) : dictData === undefined ? (
                        <p className="italic text-center text-neutral-400">Loading dictionary…</p>
                    ) : dictData === null ? (
                        <p className="italic text-neutral-400 text-center">
                            No dictionary entry found for &quot;{word}&quot;.
                        </p>
                    ) : (
                        <div>
                            <div className="flex border-b border-neutral-700 mb-2">
                                {dictData.jmentries.length > 0 && (
                                    <button
                                        className={`flex-1 py-2 text-sm ${
                                            dictTab === "jmdict"
                                                ? "border-b-2 border-teal-400 text-white"
                                                : "text-neutral-400 hover:text-neutral-200"
                                        }`}
                                        onClick={() => setDictTab("jmdict")}
                                    >
                                        Common
                                    </button>
                                )}
                                {dictData.jmnentries.length > 0 && (
                                    <button
                                        className={`flex-1 py-2 text-sm ${
                                            dictTab === "jmnedict"
                                                ? "border-b-2 border-teal-400 text-white"
                                                : "text-neutral-400 hover:text-neutral-200"
                                        }`}
                                        onClick={() => setDictTab("jmnedict")}
                                    >
                                        Proper Nouns
                                    </button>
                                )}
                                {dictData.kanji.length > 0 && (
                                    <button
                                        className={`flex-1 py-2 text-sm ${
                                            dictTab === "kanji"
                                                ? "border-b-2 border-teal-400 text-white"
                                                : "text-neutral-400 hover:text-neutral-200"
                                        }`}
                                        onClick={() => setDictTab("kanji")}
                                    >
                                        Kanji
                                    </button>
                                )}
                                {dictData.examples.length > 0 && (
                                    <button
                                        className={`flex-1 py-2 text-sm ${
                                            dictTab === "examples"
                                                ? "border-b-2 border-teal-400 text-white"
                                                : "text-neutral-400 hover:text-neutral-200"
                                        }`}
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
                                        ></ExampleDisplay>
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
