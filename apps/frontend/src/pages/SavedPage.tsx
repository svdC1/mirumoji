// src/pages/SavedPage.tsx
import React, { useState, useMemo } from "react";
import { useProfile } from "../contexts/ProfileContext";
import useSWR, { mutate } from "swr";
import { apiFetch, ApiError } from "../utils/api";
import { toast } from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import { toastApiError } from "../utils/error_toaster";
import { formatStaticUrl } from "../utils/file_utils";
import { truncateText } from "../utils/file_utils";
import {
    Clip,
    BreakdownFocus,
    BreakdownData,
    AnkiExportResponse,
} from "../types";

const API_BASE = "api/";
export default function SavedPage() {
    const { profileId } = useProfile();
    const [deletingClipId, setDeletingClipId] = useState<string | null>(null);
    const [selectedClip, setSelectedClip] = useState<Clip | null>(null);
    const [isGeneratingAnki, setIsGeneratingAnki] = useState<boolean>(false);

    const clipsSWRKey = profileId ? `/profiles/clips` : null;

    const {
        data: clips,
        error: clipsError,
        isLoading: clipsLoading,
    } = useSWR<Clip[]>(clipsSWRKey, (url: string) => apiFetch<Clip[]>(url), {
        revalidateOnFocus: false,
        onError: (err) => {
            console.error("Error fetching clips:", err);
            if (profileId) {
                toast.error("Failed to load saved clips.");
            }
        },
    });

    const parsedBreakdownData = useMemo(() => {
        if (selectedClip) {
            try {
                return JSON.parse(
                    selectedClip.breakdown_response
                ) as BreakdownData;
            } catch (error) {
                console.error("Error parsing breakdown_response:", error);
                toast.error("Error displaying clip details.");
                return null;
            }
        }
        return null;
    }, [selectedClip]);

    const handleDeleteClip = async (clipId: string) => {
        if (!profileId) {
            toast.error("Set a profile to manage clips.");
            return;
        }
        setDeletingClipId(clipId);
        const toastId = toast.loading("Deleting clip...");
        try {
            await apiFetch(`/profiles/clips/${clipId}`, { method: "DELETE" });
            toast.success("Clip deleted!", { id: toastId });
            mutate(clipsSWRKey);
            if (selectedClip && selectedClip.id === clipId) {
                setSelectedClip(null);
            }
        } catch (err: any) {
            toastApiError(err, toastId);
        } finally {
            setDeletingClipId(null);
        }
    };

    const handleViewClip = (clip: Clip) => {
        setSelectedClip(clip);
    };

    const handleSaveToAnki = async () => {
        if (!profileId) {
            toast.error("Set a profile to export to Anki.");
            return;
        }
        if (!clips || clips.length === 0) {
            toast.error("No clips available to export.");
            return;
        }
        setIsGeneratingAnki(true);
        const toastId = toast.loading("Generating Anki deck...");

        try {
            const ankiDetails = await apiFetch<AnkiExportResponse>(
                "/profiles/anki_export",
                { method: "GET" }
            );

            if (!ankiDetails || !ankiDetails.anki_deck_url) {
                throw new Error("Anki deck URL not found in response.");
            }

            toast.loading("Downloading Deck...", { id: toastId });

            const response = await fetch(
                formatStaticUrl(API_BASE, ankiDetails.anki_deck_url)
            );
            if (!response.ok) {
                throw new Error(
                    `Failed to download Anki deck: ${response.status} ${response.statusText}`
                );
            }
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = downloadUrl;
            a.download = `${profileId}_anki_deck.apkg`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

            toast.success("Downloaded !", { id: toastId });
        } catch (err: any) {
            console.error("Error generating or downloading Anki deck:", err);
            toastApiError(err, toastId);
        } finally {
            setIsGeneratingAnki(false);
        }
    };

    const showProfileMessage = (message: string) => (
        <div className="p-6 text-center text-gray-500 dark:text-gray-400">
            <p>{message}</p>
            <p>
                Please set or create a profile using the menu (☰) to manage
                saved items.
            </p>
        </div>
    );

    // Main content rendering
    if (!profileId) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">
                <div className="max-w-4xl mx-auto px-4 py-8">
                    <h1 className="text-3xl font-bold text-center mb-6">
                        Saved Clips
                    </h1>
                    {showProfileMessage("No profile selected.")}
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">
            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold">
                        Saved Clips for Profile: {profileId}
                    </h1>
                    {clips && clips.length > 0 && (
                        <button
                            onClick={handleSaveToAnki}
                            disabled={isGeneratingAnki || clipsLoading}
                            className="px-4 py-2 text-sm font-semibold rounded-md transition-colors bg-green-600 hover:bg-green-500 text-white disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
                        >
                            {isGeneratingAnki
                                ? "Generating Anki Deck..."
                                : "Save All to Anki"}
                        </button>
                    )}
                </div>

                {selectedClip && parsedBreakdownData && (
                    <div className="mb-8 p-4 bg-white dark:bg-gray-800 shadow-lg rounded-lg">
                        <video
                            key={formatStaticUrl(
                                API_BASE,
                                selectedClip.get_url
                            )}
                            controls
                            src={formatStaticUrl(
                                API_BASE,
                                selectedClip.get_url
                            )}
                            className="w-full rounded-lg mb-4 aspect-video bg-black"
                        >
                            Your browser does not support the video tag.
                        </video>
                        <h2 className="text-xl font-semibold mb-2">
                            Clip Details
                        </h2>
                        {parsedBreakdownData.focus && (
                            <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-700 rounded">
                                <h3 className="text-lg font-semibold mb-1">
                                    Focus Word
                                </h3>
                                <p className="text-md">
                                    <span className="font-bold">
                                        {parsedBreakdownData.focus.word}
                                    </span>
                                    {parsedBreakdownData.focus.reading &&
                                        ` (${parsedBreakdownData.focus.reading})`}
                                </p>
                                {parsedBreakdownData.focus.meanings &&
                                    parsedBreakdownData.focus.meanings.length >
                                        0 && (
                                        <div className="text-sm text-gray-600 dark:text-gray-300">
                                            <span className="font-semibold">
                                                Meanings:
                                            </span>
                                            <ul className="list-disc list-inside ml-2">
                                                {parsedBreakdownData.focus.meanings.map(
                                                    (meaning, index) => (
                                                        <li key={index}>
                                                            {meaning}
                                                        </li>
                                                    )
                                                )}
                                            </ul>
                                        </div>
                                    )}
                            </div>
                        )}
                        {parsedBreakdownData.sentence && (
                            <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-700 rounded">
                                <h3 className="text-lg font-semibold mb-1">
                                    Sentence
                                </h3>
                                <p className="text-md italic">
                                    {parsedBreakdownData.sentence}
                                </p>
                            </div>
                        )}
                        {parsedBreakdownData.gpt_explanation && (
                            <div className="prose dark:prose-invert prose-sm max-w-none mt-2 p-3 bg-gray-100 dark:bg-gray-700 rounded">
                                <h3 className="text-lg font-semibold mb-1">
                                    GPT Explanation
                                </h3>
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm, remarkBreaks]}
                                >
                                    {parsedBreakdownData.gpt_explanation}
                                </ReactMarkdown>
                            </div>
                        )}
                        <button
                            onClick={() => setSelectedClip(null)}
                            className="mt-4 px-4 py-2 text-sm bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 rounded-md"
                        >
                            Close Details
                        </button>
                    </div>
                )}

                {!selectedClip &&
                    !clipsLoading &&
                    !clipsError &&
                    clips &&
                    clips.length > 0 && (
                        <div className="mb-8 p-6 text-center text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 shadow-lg rounded-lg">
                            <p>
                                Select a clip from the list below to view its
                                details and video.
                            </p>
                        </div>
                    )}

                <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
                    {clipsLoading ? (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-4">
                            Loading clips…
                        </p>
                    ) : clipsError ? (
                        <p className="text-center text-red-500 py-4">
                            Error loading clips. Please ensure your profile is
                            set and backend is running.
                        </p>
                    ) : !clips || clips.length === 0 ? (
                        <p className="text-center text-gray-600 dark:text-gray-400 py-4">
                            No saved clips found for profile:{" "}
                            <strong>{profileId}</strong>. Create some from the
                            Player page!
                        </p>
                    ) : (
                        <div className="grid gap-4 grid-cols-1">
                            {clips.map((clip) => {
                                let previewBreakdown = {
                                    sentence: "N/A",
                                    gpt_explanation: "N/A",
                                };
                                try {
                                    const parsed = JSON.parse(
                                        clip.breakdown_response
                                    ) as Partial<BreakdownData>;
                                    previewBreakdown.sentence =
                                        parsed.sentence || "N/A";
                                    previewBreakdown.gpt_explanation =
                                        parsed.gpt_explanation || "N/A";
                                } catch (e) {
                                    console.error(
                                        "Error parsing breakdown_response for preview:",
                                        e
                                    );
                                }
                                return (
                                    <div
                                        key={clip.id}
                                        className="flex flex-col md:flex-row items-start md:items-center justify-between bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow hover:shadow-md transition-shadow"
                                    >
                                        <div
                                            className="flex-1 mb-4 md:mb-0 md:mr-4 cursor-pointer"
                                            onClick={() => handleViewClip(clip)}
                                        >
                                            <div className="font-semibold text-gray-800 dark:text-gray-100">
                                                {previewBreakdown.sentence}
                                            </div>
                                            <p className="text-sm text-gray-600 dark:text-gray-300">
                                                {truncateText(
                                                    previewBreakdown.gpt_explanation
                                                )}
                                            </p>
                                        </div>
                                        <div className="flex space-x-2 flex-shrink-0">
                                            <button
                                                onClick={() =>
                                                    handleViewClip(clip)
                                                }
                                                className="px-3 py-1 text-sm font-semibold rounded-md transition-colors bg-blue-600 hover:bg-blue-500 text-white"
                                            >
                                                View Clip
                                            </button>
                                            <button
                                                onClick={() =>
                                                    handleDeleteClip(clip.id)
                                                }
                                                disabled={
                                                    deletingClipId === clip.id
                                                }
                                                className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors text-white ${
                                                    deletingClipId === clip.id
                                                        ? "bg-red-700 cursor-not-allowed"
                                                        : "bg-red-600 hover:bg-red-500"
                                                }`}
                                            >
                                                {deletingClipId === clip.id
                                                    ? "Deleting…"
                                                    : "Delete"}
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
