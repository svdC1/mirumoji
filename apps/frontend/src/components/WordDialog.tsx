import React, { useEffect, useState, useRef } from "react";
import { motion, useDragControls } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { Copy, Check, Bookmark } from "lucide-react";
import { apiFetch, ApiError } from "../utils/api";
import { toast } from "react-hot-toast";
import { toastApiError } from "../utils/error_toaster";
import {
    apiWordQuery,
    DictLookup,
    JMEntry,
    JMNEntry,
    KanjiInfo,
} from "../utils/dict_api";
import { GptTemplate, SaveClipResponse } from "../types";

interface Props {
    sentence: string;
    word: string;
    onClose: () => void;
    cueStart: number;
    cueEnd: number;
    videoFile: File | null;
    videoUrl?: string;
}

const gptCache = new Map<string, any>();

export default function WordDialog({
    sentence,
    word,
    onClose,
    cueStart,
    cueEnd,
    videoFile,
    videoUrl,
}: Props) {
    const key = `${sentence}__${word}`;
    const [data, setData] = useState<any | null>(gptCache.get(key) ?? null);
    const [tab, setTab] = useState<"gpt" | "dict">("dict");
    const [dictTab, setDictTab] = useState<
        "jmdict" | "jmnedict" | "kanji" | "examples"
    >("jmdict");
    const [copied, setCopied] = useState(false);
    const [saving, setSaving] = useState(false);
    const [dictData, setDictData] = useState<DictLookup | null | undefined>(
        undefined
    );

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

    const fetchGptData = async () => {
        if (gptCache.has(key)) {
            setData(gptCache.get(key));
            return gptCache.get(key);
        }
        let endpointUrl = "/gpt/breakdown";
        let requestBody: any = { sentence, focus: word };

        try {
            const customTemplate = await apiFetch<GptTemplate | null>(
                "/profiles/gpt_template"
            );

            if (
                customTemplate &&
                customTemplate.sysMsg &&
                customTemplate.prompt &&
                customTemplate.prompt.includes("{sentence}") &&
                customTemplate.prompt.includes("{focus}")
            ) {
                endpointUrl = "/gpt/custom_breakdown";
                const backendPrompt = customTemplate.prompt
                    .replace(/{sentence}/g, "{0}")
                    .replace(/{focus}/g, "{1}");
                requestBody = {
                    sentence,
                    focus: word,
                    sysMsg: customTemplate.sysMsg,
                    prompt: backendPrompt,
                };
                console.log(
                    "Using custom GPT template for breakdown (from profile)."
                );
            } else {
                console.log(
                    customTemplate
                        ? "Custom template from profile is invalid. Using default."
                        : "No custom template from profile. Using default breakdown."
                );
            }
        } catch (templateError) {
            if (
                templateError instanceof ApiError &&
                templateError.status === 404
            ) {
                console.log(
                    "No GPT template set for this profile. Using default breakdown."
                );
            } else {
                console.warn(
                    "Failed to fetch profile GPT template, using default breakdown:",
                    templateError
                );
            }
        }

        try {
            const json = await apiFetch(endpointUrl, {
                method: "POST",
                body: JSON.stringify(requestBody),
            });
            gptCache.set(key, json);
            setData(json);
            return json;
        } catch (e) {
            toastApiError(e);
            onClose();
            throw e;
        }
    };

    useEffect(() => {
        if (data || tab !== "gpt") return;
        fetchGptData();
    }, [key, data, sentence, word, tab, onClose]);

    useEffect(() => {
        if (tab !== "dict") return;
        setDictData(undefined);
        apiWordQuery(word)
            .then((entry) => {
                if (entry) {
                    entry.kanji = entry.kanji.filter(
                        (k) => k.stroke_count !== 99
                    );
                    entry.jmentries = entry.jmentries.filter(
                        (jme) =>
                            (jme.kanji.length !== 0 || jme.kana.length !== 0) &&
                            jme.senses.length !== 0 &&
                            jme.senses[0].order !== 99
                    );
                    entry.jmnentries = entry.jmnentries.filter(
                        (jmne) =>
                            (jmne.kanji.length !== 0 ||
                                jmne.kana.length !== 0) &&
                            jmne.gloss.length !== 0 &&
                            jmne.translation_type !== ""
                    );
                }
                const noEntry =
                    entry.kanji.length === 0 &&
                    entry.jmentries.length === 0 &&
                    entry.jmnentries.length === 0 &&
                    entry.meanings.length === 0 &&
                    entry.examples.length === 0 &&
                    entry.jlpt === "Unknown";
                if (!noEntry) {
                    setDictData(entry);
                    if (entry?.jmentries.length === 0) {
                        if (entry?.jmnentries.length > 0) {
                            setDictTab("jmnedict");
                        } else if (entry?.kanji.length > 0) {
                            setDictTab("kanji");
                        } else if (entry?.examples.length > 0) {
                            setDictTab("examples");
                        }
                    }
                } else {
                    setDictData(null);
                }
            })
            .catch((e) => {
                console.error("apiWordQuery error", e);
                setDictData(null);
            });
    }, [tab, word]);

    const handleCopy = () => {
        // This function will need to be updated to handle the new dictData structure
        let textToCopy = "";
        if (tab === "gpt" && data) {
            textToCopy = [
                data.focus.word,
                ...(data.focus.reading ? [data.focus.reading] : []),
                ...(data.focus.meanings ?? []),
                "",
                data.gpt_explanation,
            ].join("\n");
        } else if (tab === "dict" && dictData) {
            // Simplified for now, can be expanded
            textToCopy = `${word}
${dictData.meanings.join(", ")}`;
        }
        if (textToCopy) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            });
        }
    };

    const createRecordingPromise = (
        stream: MediaStream,
        duration: number
    ): Promise<File> => {
        return new Promise<File>((resolve, reject) => {
            let recorder: MediaRecorder;
            const chunks: BlobPart[] = [];
            if (duration <= 0) {
                return reject(
                    new Error("Recording duration must be positive.")
                );
            }
            try {
                if (
                    !stream ||
                    !stream.active ||
                    stream.getTracks().length === 0
                ) {
                    return reject(
                        new Error(
                            "Stream is invalid or has no tracks at MediaRecorder creation."
                        )
                    );
                }
                const options = { mimeType: "video/webm;codecs=vp8,opus" };
                try {
                    recorder = new MediaRecorder(stream, options);
                } catch (e) {
                    console.warn(
                        `Recorder init failed with ${options.mimeType}, trying default:`,
                        e
                    );
                    recorder = new MediaRecorder(stream);
                }
                recorder.ondataavailable = (event) => {
                    if (event.data && event.data.size > 0)
                        chunks.push(event.data);
                };
                recorder.onstop = () => {
                    if (chunks.length === 0)
                        return reject(new Error("No video data recorded."));
                    const clipMimeType = recorder.mimeType || "video/webm";
                    const clipBlob = new Blob(chunks, { type: clipMimeType });
                    if (clipBlob.size === 0)
                        return reject(new Error("Recorded clip is empty."));
                    const ext =
                        clipMimeType.split(";")[0].split("/")[1] || "webm";
                    resolve(
                        new File([clipBlob], `clip.${ext}`, {
                            type: clipMimeType,
                        })
                    );
                };
                recorder.onerror = (event) =>
                    reject(new Error("MediaRecorder error"));
                recorder.start();
                setTimeout(() => {
                    if (recorder?.state === "recording") recorder.stop();
                }, duration);
            } catch (setupError) {
                console.error(
                    "Error in createRecordingPromise setup:",
                    setupError
                );
                reject(setupError);
            }
        });
    };

    const handleSave = async () => {
        if (!canSaveClip) {
            toast.error("No video source available");
            return;
        }
        const videoElement = document.getElementById(
            "mirumoji-player"
        ) as HTMLVideoElement;
        if (!videoElement) {
            toast.error("Video player not found.");
            setSaving(false);
            return;
        }
        let adjustedCueEnd = cueEnd + 1.0;
        if (cueStart >= adjustedCueEnd) {
            toast.error("Invalid clip duration.");
            setSaving(false);
            return;
        }
        // Try to get Video Duration so that clip extension doesn't exceed it
        const videoDuration = videoElement.duration;

        // Only clamp if videoDuration is a valid, finite number
        if (
            typeof videoDuration === "number" &&
            !isNaN(videoDuration) &&
            isFinite(videoDuration)
        ) {
            if (cueStart >= videoDuration) {
                toast.error("Clip start time is at or after video end.");
                setSaving(false);
                return;
            }
            if (adjustedCueEnd > videoDuration) {
                console.warn(
                    `Adjusted cue end (${adjustedCueEnd}s) exceeds video duration (${videoDuration}s). Clamping to video duration.`
                );
                adjustedCueEnd = videoDuration;
            }
        } else {
            console.warn(
                "Video duration is not available or not finite (e.g., live stream). Using original cueEnd"
            );
            adjustedCueEnd = cueEnd;
        }
        setSaving(true);
        let gptData = data;

        if (!gptData) {
            toast.loading("Fetching GPT", {
                id: "gptSaveToast",
            });
            try {
                gptData = await fetchGptData();
                toast.dismiss("gptSaveToast");
            } catch (error) {
                setSaving(false);
                toast.dismiss("gptSaveToast");
                return;
            }
        }

        if (!gptData) {
            setSaving(false);
            toast.error("Could not fetch GPT. Please try again.");
            return;
        }

        const originalPlayerTime = videoElement.currentTime;
        const wasPlayerPaused = videoElement.paused;
        const originalMutedState = videoElement.muted;
        let streamToCleanup: MediaStream | null = null;

        try {
            const recordingDurationMs = (adjustedCueEnd - cueStart) * 1000;
            if (recordingDurationMs <= 0) {
                throw new Error("Clip duration must be positive.");
            }

            videoElement.currentTime = cueStart;
            videoElement.muted = true;
            await videoElement
                .play()
                .catch((e) => console.warn("Playback warning during save:", e));
            await new Promise((r) => setTimeout(r, 150));

            const capturedStream = videoElement.captureStream();
            streamToCleanup = capturedStream;

            if (
                !capturedStream ||
                !capturedStream.active ||
                capturedStream.getTracks().length === 0
            ) {
                throw new Error(
                    "Failed to capture a valid video stream for clipping."
                );
            }

            const clipFile = await createRecordingPromise(
                capturedStream,
                recordingDurationMs
            );

            videoElement.currentTime = originalPlayerTime;
            if (wasPlayerPaused && !videoElement.paused) videoElement.pause();
            else if (!wasPlayerPaused && videoElement.paused)
                await videoElement
                    .play()
                    .catch((e) => console.warn("Restore play failed:", e));
            videoElement.muted = originalMutedState;

            if (streamToCleanup) {
                streamToCleanup.getTracks().forEach((track) => track.stop());
                streamToCleanup = null;
            }

            const formData = new FormData();
            formData.append("clip_start_time", cueStart.toString());
            formData.append("clip_end_time", adjustedCueEnd.toString());
            formData.append("gpt_breakdown_response", JSON.stringify(gptData));
            formData.append("video_clip", clipFile, clipFile.name);

            const toastId = "saveClipToast";
            toast.loading("Saving...", { id: toastId });

            const response = await apiFetch<SaveClipResponse>(
                "/profiles/clips/save",
                { method: "POST", body: formData }
            );

            if (response.success) {
                toast.success(response.message || "Clip Saved!", {
                    id: toastId,
                });
            } else {
                throw new Error(response.message || "Failed to save clip.");
            }
        } catch (error: any) {
            console.error("Error during clip saving process:", error);
            toast.error(
                error.message ||
                    "An unexpected error occurred while saving the clip."
            );
            if (videoElement) {
                videoElement.currentTime = originalPlayerTime;
                if (wasPlayerPaused && !videoElement.paused)
                    videoElement.pause();
                else if (!wasPlayerPaused && videoElement.paused)
                    await videoElement
                        .play()
                        .catch((e) =>
                            console.warn("Error restore play failed:", e)
                        );
                videoElement.muted = originalMutedState;
            }
        } finally {
            if (streamToCleanup) {
                streamToCleanup.getTracks().forEach((track) => track.stop());
            }
            setSaving(false);
        }
    };

    const JmdictEntryDisplay = ({
        entry,
        isLast,
    }: {
        entry: JMEntry;
        isLast: boolean;
    }) => (
        <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
            <div className="flex items-center">
                <h3 className="text-lg font-bold mr-2">
                    {entry.kanji.join("、")}
                </h3>
                <p className="text-md text-neutral-300">
                    {entry.kana.join("、")}
                </p>
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

    const ExampleDisplay = ({
        example,
        key,
        isLast,
    }: {
        example: string;
        key: number;
        isLast: boolean;
    }) => (
        <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
            <div className="flex items-center">
                <div key={key} className="ml-4 mt-1">
                    <p className="text-neutral-400 text-lg">({example})</p>
                </div>
            </div>
        </div>
    );

    const JmnedictEntryDisplay = ({
        entry,
        isLast,
    }: {
        entry: JMNEntry;
        isLast: boolean;
    }) => (
        <div className={`py-2 ${!isLast ? "border-b border-neutral-700" : ""}`}>
            <div className="flex items-center">
                <h3 className="text-lg font-bold mr-2">
                    {entry.kanji.join("、")}
                </h3>
                <p className="text-md text-neutral-300">
                    {entry.kana.join("、")}
                </p>
            </div>
            <p className="text-neutral-400 text-sm">
                ({entry.translation_type})
            </p>
            <p>{entry.gloss.join("; ")}</p>
        </div>
    );

    const KanjiInfoDisplay = ({
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
                    <span className="font-semibold text-neutral-400">
                        Strokes:
                    </span>{" "}
                    {kanjiInfo.stroke_count}
                </p>
                <p>
                    <span className="font-semibold text-neutral-400">
                        Grade:
                    </span>{" "}
                    {kanjiInfo.grade || "N/A"}
                </p>
                <p>
                    <span className="font-semibold text-neutral-400">
                        JLPT:
                    </span>{" "}
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
                                    saving
                                        ? "text-gray-500"
                                        : "hover:text-emerald-400"
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
                        <button
                            className="text-2xl"
                            onClick={onClose}
                            aria-label="Close"
                        >
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
                                tab === "gpt"
                                    ? "border-b-2 border-emerald-400 text-white"
                                    : "text-neutral-400 hover:text-neutral-200"
                            }`}
                            onClick={() => setTab("gpt")}
                        >
                            GPT
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
                    {tab === "gpt" ? (
                        !data ? (
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
                                    {data.focus.word}
                                </h2>
                                {data.focus.reading ||
                                data.focus.meanings?.length ? (
                                    <div className="mt-1 mb-3 text-neutral-300 text-base leading-relaxed">
                                        {data.focus.reading && (
                                            <span className="mr-2 italic">
                                                {data.focus.reading}
                                            </span>
                                        )}
                                        {data.focus.meanings?.length && (
                                            <span>
                                                {data.focus.meanings.join("；")}
                                            </span>
                                        )}
                                    </div>
                                ) : (
                                    <div className="mt-1 mb-3 text-neutral-300 text-base leading-relaxed">
                                        No Reading/Meaning Found
                                    </div>
                                )}
                                <ReactMarkdown
                                    className="prose prose-sm sm:prose-base prose-invert max-w-none whitespace-pre-wrap"
                                    remarkPlugins={[remarkGfm, remarkBreaks]}
                                >
                                    {data.gpt_explanation}
                                </ReactMarkdown>
                            </>
                        )
                    ) : dictData === undefined ? (
                        <p className="text-neutral-400">Loading dictionary…</p>
                    ) : dictData === null ? (
                        <p className="italic text-neutral-400">
                            No dictionary entry found for "{word}".
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
                                            isLast={
                                                i ===
                                                dictData.jmentries.length - 1
                                            }
                                        />
                                    ))}
                                </div>
                            ) : dictTab === "jmnedict" ? (
                                <div>
                                    {dictData.jmnentries.map((entry, i) => (
                                        <JmnedictEntryDisplay
                                            key={i}
                                            entry={entry}
                                            isLast={
                                                i ===
                                                dictData.jmnentries.length - 1
                                            }
                                        />
                                    ))}
                                </div>
                            ) : dictTab === "kanji" ? (
                                <div>
                                    {dictData.kanji.map((kanji, i) => (
                                        <KanjiInfoDisplay
                                            key={i}
                                            kanjiInfo={kanji}
                                            isLast={
                                                i === dictData.kanji.length - 1
                                            }
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div>
                                    {dictData.examples.map((ex, i) => (
                                        <ExampleDisplay
                                            key={i}
                                            example={ex}
                                            isLast={
                                                i ===
                                                dictData.examples.length - 1
                                            }
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
