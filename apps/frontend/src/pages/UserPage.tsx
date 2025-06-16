// src/pages/UserPage.tsx
import React, { useState, useEffect } from "react";
import { useProfile } from "../contexts/ProfileContext";
import useSWR, { mutate } from "swr";
import { apiFetch, ApiError } from "../utils/api";
import { toast } from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import { GptTemplate, ProfileFile, ProfileTranscript } from "../types";
import {
    getFileExtension,
    truncateFilename,
    formatStaticUrl,
} from "../utils/file_utils";
const tabs = [
    { id: "profile", label: "Profile" },
    { id: "files", label: "Files" },
    { id: "transcripts", label: "Transcripts" },
    { id: "gpt-template", label: "GPT Template" },
];
const API_BASE = "api/";
const defaultSysMsg = `You are a Japanese language API that explains the specific nuance of specified word(s) in a Japanese sentence.\r\n\r\nRespond concisely in no more than 100 words.\r\n\r\nSpecified word(s) MUST be in Japanese\r\n\r\nAll other explanation text MUST be in English\r\n\r\nIn your response:\r\n\r\nDO NOT OUTPUT the language name or the word \'nuance\';\r\n\r\nDO NOT OUTPUT the context sentence ;\r\n\r\nDO NOT OUTPUT romaji/furigana or any notes on pronunciation;\r\n\r\nConclude with the specific nuance within the context sentence.`;
const defaultPrompt = `{sentence}. Explain usage of word : {focus}\r\n`;

export default function UserPage() {
    const [activeTab, setActiveTab] = useState<string>("profile");
    const { profileId } = useProfile();
    const [deletingFileId, setDeletingFileId] = useState<string | null>(null);
    const [deletingTranscriptId, setDeletingTranscriptId] = useState<
        string | null
    >(null);
    const [downloadingTranscriptId, setDownloadingTranscriptId] = useState<
        string | null
    >(null);

    // GPT Template states
    const [gptSysMsg, setGptSysMsg] = useState("");
    const [gptPrompt, setGptPrompt] = useState("");
    const [currentGptTemplate, setCurrentGptTemplate] =
        useState<GptTemplate | null>(null); // Store the fetched template object
    const [isSavingGptTemplate, setIsSavingGptTemplate] = useState(false);
    const [isDeletingGptTemplate, setIsDeletingGptTemplate] = useState(false);

    // SWR fetch keys - will use profileId
    const filesSWRKey =
        profileId && activeTab === "files" ? `/profiles/files` : null;
    const transcriptsSWRKey =
        profileId && activeTab === "transcripts"
            ? `/profiles/transcripts`
            : null;
    const gptTemplateSWRKey =
        profileId && activeTab === "gpt-template"
            ? `/profiles/gpt_template`
            : null;

    // Fetch files
    const {
        data: files,
        error: filesError,
        isLoading: filesLoading,
    } = useSWR<ProfileFile[]>(filesSWRKey, apiFetch, {
        revalidateOnFocus: false,
        onError: (err) => {
            console.error("Error fetching files:", err);
            toast.error("Failed to load files.");
        },
    });

    // Fetch transcripts
    const {
        data: transcripts,
        error: transcriptsError,
        isLoading: transcriptsLoading,
    } = useSWR<ProfileTranscript[]>(transcriptsSWRKey, apiFetch, {
        revalidateOnFocus: false,
        onError: (err) => {
            console.error("Error fetching transcripts:", err);
            toast.error("Failed to load transcripts.");
        },
    });

    // Fetch GPT template
    const {
        data: gptTemplateData,
        error: gptTemplateError,
        isLoading: gptTemplateLoading,
    } = useSWR<GptTemplate | null>(gptTemplateSWRKey, apiFetch, {
        revalidateOnFocus: false,
        onError: (err: ApiError) => {
            if (err.status !== 404) {
                // 404 means no template set, which is fine
                console.error("Error fetching GPT template:", err);
                toast.error("Failed to load GPT template.");
            }
        },
    });

    useEffect(() => {
        if (gptTemplateData) {
            setGptSysMsg(gptTemplateData.sysMsg);
            setGptPrompt(gptTemplateData.prompt);
            setCurrentGptTemplate(gptTemplateData);
        } else if (
            profileId &&
            activeTab === "gpt-template" &&
            !gptTemplateLoading
        ) {
            // If no template data but profile active
            setGptSysMsg(defaultSysMsg); // Clear or set to defaults for new template creation
            setGptPrompt(defaultPrompt);
            setCurrentGptTemplate(null);
        }
    }, [gptTemplateData, profileId, activeTab, gptTemplateLoading]);

    const handleDeleteFile = async (fileId: string) => {
        if (!profileId) {
            toast.error("Set a profile to manage files.");
            return;
        }
        setDeletingFileId(fileId);
        try {
            await apiFetch(`/profiles/files/${fileId}`, { method: "DELETE" });
            toast.success("File deleted!");
            mutate(filesSWRKey);
        } catch (err: any) {
            console.error("Error deleting file:", err);
            toast.error("Failed to delete file. Please try again.");
        } finally {
            setDeletingFileId(null);
        }
    };

    const handleDeleteTranscript = async (transcriptId: string) => {
        if (!profileId) {
            toast.error("Set a profile to manage transcripts.");
            return;
        }
        setDeletingTranscriptId(transcriptId);
        try {
            await apiFetch(`/profiles/transcripts/${transcriptId}`, {
                method: "DELETE",
            });
            toast.success("Transcript deleted.");
            mutate(transcriptsSWRKey);
        } catch (err: any) {
            console.error("Error deleting transcript:", err);
            toast.error("Failed to delete transcript. Please try again.");
        } finally {
            setDeletingTranscriptId(null);
        }
    };

    const handleDownloadTranscript = async (transcript: ProfileTranscript) => {
        if (!profileId) {
            toast.error("Set a profile to download items.");
            return;
        }
        setDownloadingTranscriptId(transcript.id);
        try {
            const response = await fetch(
                formatStaticUrl(API_BASE, transcript.get_url)
            );
            if (!response.ok)
                throw new Error(`HTTP error! status: ${response.status}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            const fileExtension =
                getFileExtension(transcript.get_url) ||
                getFileExtension(transcript.original_file_name) ||
                "audio";
            const baseFileName = truncateFilename(
                transcript.original_file_name || transcript.id,
                10,
                5
            );
            a.download = `${baseFileName}.${fileExtension}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            toast.success("Downloaded audio!");
        } catch (err: any) {
            console.error("Error downloading transcript audio:", err);
            toast.error("Failed to download audio.");
        } finally {
            setDownloadingTranscriptId(null);
        }
    };

    const handleSaveGptTemplate = async () => {
        if (!profileId) {
            toast.error("Set a profile to save a GPT template.");
            return;
        }
        setIsSavingGptTemplate(true);
        try {
            const method = "POST";
            const payload: Partial<GptTemplate> = {
                sysMsg: gptSysMsg,
                prompt: gptPrompt,
            };
            if (currentGptTemplate?.id) {
                payload.id = currentGptTemplate.id;
            }

            await apiFetch(`/profiles/gpt_template`, {
                method: method,
                body: JSON.stringify(payload),
            });
            toast.success(
                currentGptTemplate?.id
                    ? "Template updated!"
                    : "Template created!"
            );
            mutate(gptTemplateSWRKey);
        } catch (error) {
            console.error("Error saving GPT template:", error);
            toast.error("Failed to save template. Please try again.");
        } finally {
            setIsSavingGptTemplate(false);
        }
    };

    const handleRevertToDefaultGptTemplate = async () => {
        if (!profileId) {
            toast.error("Set a profile to manage templates.");
            return;
        }
        setIsSavingGptTemplate(true);
        try {
            await apiFetch(`/profiles/gpt_template`, {
                method: "POST",
                body: JSON.stringify({
                    sysMsg: defaultSysMsg,
                    prompt: defaultPrompt,
                }),
            });
            setGptSysMsg(defaultSysMsg);
            setGptPrompt(defaultPrompt);
            toast.success("Template reverted to default!");
            mutate(gptTemplateSWRKey);
        } catch (error) {
            console.error("Error reverting GPT template:", error);
            toast.error("Failed to revert template. Please try again.");
        } finally {
            setIsSavingGptTemplate(false);
        }
    };

    const handleDeleteGptTemplate = async () => {
        if (!profileId || !currentGptTemplate?.id) {
            toast.error("No template to delete or profile not set.");
            return;
        }
        setIsDeletingGptTemplate(true);
        try {
            await apiFetch(`/profiles/gpt_template`, { method: "DELETE" });
            toast.success("Template deleted!");
            setGptSysMsg("");
            setGptPrompt("");
            setCurrentGptTemplate(null);
            mutate(gptTemplateSWRKey);
        } catch (error) {
            console.error("Error deleting GPT template:", error);
            toast.error("Failed to delete template. Please try again.");
        } finally {
            setIsDeletingGptTemplate(false);
        }
    };

    const showProfileMessage = (message: string) => (
        <div className="p-6 text-center text-gray-500 dark:text-gray-400">
            <p>{message}</p>
            <p>Please set or create a profile using the menu (☰).</p>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">
            <div className="max-w-4xl mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold mb-6 text-center sm:text-left">
                    Profile Dashboard
                </h1>

                <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg">
                    <nav className="flex flex-wrap border-b border-gray-200 dark:border-gray-700">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`py-3 px-6 -mb-px font-medium text-sm transition-colors focus:outline-none ${
                                    activeTab === tab.id
                                        ? "text-indigo-600 border-b-2 border-indigo-600"
                                        : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </nav>

                    <div className="p-6">
                        {activeTab === "profile" &&
                            (profileId ? (
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                    <div className="text-gray-600 dark:text-gray-400 sm:col-span-1">
                                        Active Profile:
                                    </div>
                                    <div className="col-span-1 sm:col-span-2 break-all font-semibold">
                                        {profileId}
                                    </div>
                                </div>
                            ) : (
                                showProfileMessage("No active profile.")
                            ))}
                        {activeTab === "files" &&
                            (!profileId ? (
                                showProfileMessage(
                                    "Set a profile to view your files."
                                )
                            ) : filesLoading ? (
                                <p>Loading files…</p>
                            ) : filesError ? (
                                <p className="text-red-500">
                                    Error loading files.
                                </p>
                            ) : files && files.length > 0 ? (
                                <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                                    {files.map((file) => (
                                        <div
                                            key={file.id}
                                            className="flex items-center justify-between bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow"
                                        >
                                            <a
                                                href={formatStaticUrl(
                                                    API_BASE,
                                                    file.get_url
                                                )}
                                                download={file.file_name}
                                                className="flex-1 mr-4 overflow-hidden"
                                            >
                                                <div className="font-medium text-gray-800 dark:text-gray-100 truncate">
                                                    {truncateFilename(
                                                        file.file_name
                                                    )}
                                                </div>
                                            </a>
                                            <button
                                                onClick={() =>
                                                    handleDeleteFile(file.id)
                                                }
                                                disabled={
                                                    deletingFileId === file.id
                                                }
                                                className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors ${
                                                    deletingFileId === file.id
                                                        ? "bg-red-800 cursor-not-allowed"
                                                        : "bg-red-600 hover:bg-red-500"
                                                }`}
                                            >
                                                {deletingFileId === file.id
                                                    ? "Deleting…"
                                                    : "Delete"}
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p>No files found for this profile.</p>
                            ))}
                        {activeTab === "transcripts" &&
                            (!profileId ? (
                                showProfileMessage(
                                    "Set a profile to view your transcripts."
                                )
                            ) : transcriptsLoading ? (
                                <p>Loading transcripts…</p>
                            ) : transcriptsError ? (
                                <p className="text-red-500">
                                    Error loading transcripts.
                                </p>
                            ) : transcripts && transcripts.length > 0 ? (
                                <div className="grid gap-4 grid-cols-1">
                                    {transcripts.map((transcript) => (
                                        <div
                                            key={transcript.id}
                                            className="flex flex-col bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow"
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 flex-1 mr-4 break-all">
                                                    Transcript ID:{" "}
                                                    {truncateFilename(
                                                        transcript.id,
                                                        4,
                                                        4
                                                    )}
                                                    {transcript.original_file_name &&
                                                        ` (from ${truncateFilename(
                                                            transcript.original_file_name
                                                        )})`}
                                                </div>
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() =>
                                                            handleDownloadTranscript(
                                                                transcript
                                                            )
                                                        }
                                                        disabled={
                                                            downloadingTranscriptId ===
                                                            transcript.id
                                                        }
                                                        className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors ${
                                                            downloadingTranscriptId ===
                                                            transcript.id
                                                                ? "bg-blue-800 cursor-not-allowed"
                                                                : "bg-blue-600 hover:bg-blue-500"
                                                        }`}
                                                    >
                                                        {downloadingTranscriptId ===
                                                        transcript.id
                                                            ? "Downloading…"
                                                            : "Download Audio"}
                                                    </button>
                                                    <button
                                                        onClick={() =>
                                                            handleDeleteTranscript(
                                                                transcript.id
                                                            )
                                                        }
                                                        disabled={
                                                            deletingTranscriptId ===
                                                            transcript.id
                                                        }
                                                        className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors ${
                                                            deletingTranscriptId ===
                                                            transcript.id
                                                                ? "bg-red-800 cursor-not-allowed"
                                                                : "bg-red-600 hover:bg-red-500"
                                                        }`}
                                                    >
                                                        {deletingTranscriptId ===
                                                        transcript.id
                                                            ? "Deleting…"
                                                            : "Delete"}
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="text-gray-800 dark:text-gray-100 mb-2 whitespace-pre-wrap">
                                                {transcript.transcript}
                                            </div>
                                            {transcript.gpt_explanation && (
                                                <div className="prose dark:prose-invert prose-sm max-w-none border-t border-zinc-700 pt-3 mt-3">
                                                    <ReactMarkdown
                                                        remarkPlugins={[
                                                            remarkBreaks,
                                                        ]}
                                                    >
                                                        {
                                                            transcript.gpt_explanation
                                                        }
                                                    </ReactMarkdown>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p>No transcripts found for this profile.</p>
                            ))}

                        {activeTab === "gpt-template" &&
                            (!profileId ? (
                                showProfileMessage(
                                    "Set a profile to manage GPT templates."
                                )
                            ) : gptTemplateLoading ? (
                                <p>Loading GPT Template...</p>
                            ) : gptTemplateError &&
                              (gptTemplateError as ApiError).status !== 404 ? (
                                <p className="text-red-500">
                                    Error loading GPT Template.
                                </p>
                            ) : (
                                <div className="space-y-6 flex flex-col">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        Customize your GPT template for word
                                        explanations. Use{" "}
                                        <code>{"{sentence}"}</code> and{" "}
                                        <code>{"{focus}"}</code> placeholders.
                                    </p>
                                    <div>
                                        <label
                                            htmlFor="gptSysMsg"
                                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                        >
                                            System Message
                                        </label>
                                        <textarea
                                            id="gptSysMsg"
                                            value={gptSysMsg}
                                            onChange={(e) =>
                                                setGptSysMsg(e.target.value)
                                            }
                                            rows={6}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 resize-none overflow-auto"
                                            placeholder={
                                                currentGptTemplate
                                                    ? ""
                                                    : defaultSysMsg
                                            }
                                        />
                                    </div>
                                    <div>
                                        <label
                                            htmlFor="gptPrompt"
                                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                        >
                                            User Prompt
                                        </label>
                                        <textarea
                                            id="gptPrompt"
                                            value={gptPrompt}
                                            onChange={(e) =>
                                                setGptPrompt(e.target.value)
                                            }
                                            rows={8}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 resize-none overflow-auto"
                                            placeholder={
                                                currentGptTemplate
                                                    ? ""
                                                    : defaultPrompt
                                            }
                                        />
                                    </div>
                                    <div className="flex flex-col sm:flex-row justify-center items-center space-y-3 sm:space-y-0 sm:space-x-4 mt-4">
                                        <button
                                            onClick={handleSaveGptTemplate}
                                            disabled={
                                                isSavingGptTemplate ||
                                                isDeletingGptTemplate
                                            }
                                            className="w-full sm:w-auto px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50"
                                        >
                                            {isSavingGptTemplate
                                                ? "Saving..."
                                                : currentGptTemplate
                                                ? "Update Template"
                                                : "Create Template"}
                                        </button>
                                        {currentGptTemplate && (
                                            <>
                                                <button
                                                    onClick={
                                                        handleRevertToDefaultGptTemplate
                                                    }
                                                    disabled={
                                                        isSavingGptTemplate ||
                                                        isDeletingGptTemplate
                                                    }
                                                    className="w-full sm:w-auto px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-md shadow-sm disabled:opacity-50"
                                                >
                                                    Revert to Default
                                                </button>
                                                <button
                                                    onClick={
                                                        handleDeleteGptTemplate
                                                    }
                                                    disabled={
                                                        isDeletingGptTemplate ||
                                                        isSavingGptTemplate
                                                    }
                                                    className="w-full sm:w-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50"
                                                >
                                                    {isDeletingGptTemplate
                                                        ? "Deleting..."
                                                        : "Delete Template"}
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
