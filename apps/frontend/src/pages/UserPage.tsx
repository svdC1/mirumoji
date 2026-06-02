/**
 * @packageDocumentation This component is the user page of the application.
 * It allows the user to view their profile, files, transcripts, and LLM template.
 */

import React, { useState, useEffect } from "react";
import { useProfile } from "../contexts/ProfileContext";
import useSWR, { mutate } from "swr";
import { apiFetch } from "../services/api";
import { apiProviders, parseModel, formatModel } from "../services/llmApi";
import { toast } from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import {
    LlmTemplate,
    ProviderStatus,
    ProfileFile,
    ProfileTranscript,
    ApiError,
} from "../types/types";
import { getFileExtension, truncateFilename, formatStaticUrl } from "../utils/fileUtils";
import { tabs, API_BASE, defaultSysMsg, defaultPrompt, defaultModel } from "../constants/user-page";

/**
 * The UserPage component.
 *
 * This component is responsible for the following:
 * - Displaying the user's profile, files, and transcripts.
 * - Managing the profile's LLM template (system message, prompt, and
 *   provider:model selector, with the provider list driven by /llm/providers).
 * - Allowing the user to delete/download files and transcripts.
 *
 * @returns {JSX.Element} The UserPage component.
 */
export default function UserPage() {
    const [activeTab, setActiveTab] = useState<string>("profile");
    const { profileId } = useProfile();
    const [deletingFileId, setDeletingFileId] = useState<string | null>(null);
    const [deletingTranscriptId, setDeletingTranscriptId] = useState<string | null>(null);
    const [downloadingTranscriptId, setDownloadingTranscriptId] = useState<string | null>(null);

    // LLM template states
    const [sysMsg, setSysMsg] = useState("");
    const [promptText, setPromptText] = useState("");
    const defaults = parseModel(defaultModel);
    const [provider, setProvider] = useState(defaults.provider);
    const [modelName, setModelName] = useState(defaults.name);
    const [currentTemplate, setCurrentTemplate] = useState<LlmTemplate | null>(null);
    const [isSavingTemplate, setIsSavingTemplate] = useState(false);
    const [isDeletingTemplate, setIsDeletingTemplate] = useState(false);

    // SWR fetch keys - will use profileId
    const filesSWRKey = profileId && activeTab === "files" ? `profiles/files` : null;
    const transcriptsSWRKey =
        profileId && activeTab === "transcripts" ? `profiles/transcripts` : null;
    const templateSWRKey = profileId && activeTab === "gpt-template" ? `profiles/template` : null;
    const providersSWRKey = activeTab === "gpt-template" ? `llm/providers` : null;

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

    // Fetch the available LLM providers (drives the provider picker)
    const { data: providers } = useSWR<ProviderStatus[]>(providersSWRKey, () => apiProviders(), {
        revalidateOnFocus: false,
        onError: (err) => {
            console.error("Error fetching providers:", err);
        },
    });

    // Fetch the profile's LLM template
    const {
        data: templateData,
        error: templateError,
        isLoading: templateLoading,
    } = useSWR<LlmTemplate | null>(templateSWRKey, apiFetch, {
        revalidateOnFocus: false,
        onError: (err: ApiError) => {
            if (err.status !== 404) {
                // 404 means no template set, which is fine
                console.error("Error fetching LLM template:", err);
                toast.error("Failed to load LLM template.");
            }
        },
    });

    useEffect(() => {
        if (templateData) {
            setSysMsg(templateData.sys_msg);
            setPromptText(templateData.prompt);
            const parsed = parseModel(templateData.model);
            setProvider(parsed.provider);
            setModelName(parsed.name);
            setCurrentTemplate(templateData);
        } else if (profileId && activeTab === "gpt-template" && !templateLoading) {
            // No template yet: seed the form with defaults for creation
            setSysMsg(defaultSysMsg);
            setPromptText(defaultPrompt);
            const parsed = parseModel(defaultModel);
            setProvider(parsed.provider);
            setModelName(parsed.name);
            setCurrentTemplate(null);
        }
    }, [templateData, profileId, activeTab, templateLoading]);

    const handleDeleteFile = async (fileId: string) => {
        if (!profileId) {
            toast.error("Set a profile to manage files.");
            return;
        }
        setDeletingFileId(fileId);
        try {
            await apiFetch(`profiles/files/${fileId}`, { method: "DELETE" });
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
            await apiFetch(`profiles/transcripts/${transcriptId}`, {
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
        if (!transcript.url) {
            toast.error("No audio available for this transcript.");
            return;
        }
        setDownloadingTranscriptId(transcript.id);
        try {
            const response = await fetch(formatStaticUrl(API_BASE, transcript.url));
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            const fileExtension = getFileExtension(transcript.url) || "audio";
            const baseFileName = truncateFilename(transcript.id, 10, 5);
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

    const handleSaveTemplate = async () => {
        if (!profileId) {
            toast.error("Set a profile to save an LLM template.");
            return;
        }
        setIsSavingTemplate(true);
        try {
            await apiFetch(`profiles/template`, {
                method: "POST",
                body: JSON.stringify({
                    sys_msg: sysMsg,
                    prompt: promptText,
                    model: formatModel(provider, modelName),
                }),
            });
            toast.success(currentTemplate ? "Template updated!" : "Template created!");
            mutate(templateSWRKey);
        } catch (error) {
            console.error("Error saving LLM template:", error);
            toast.error("Failed to save template. Please try again.");
        } finally {
            setIsSavingTemplate(false);
        }
    };

    const handleRevertToDefaultTemplate = async () => {
        if (!profileId) {
            toast.error("Set a profile to manage templates.");
            return;
        }
        setIsSavingTemplate(true);
        try {
            await apiFetch(`profiles/template`, {
                method: "POST",
                body: JSON.stringify({
                    sys_msg: defaultSysMsg,
                    prompt: defaultPrompt,
                    model: defaultModel,
                }),
            });
            setSysMsg(defaultSysMsg);
            setPromptText(defaultPrompt);
            const parsed = parseModel(defaultModel);
            setProvider(parsed.provider);
            setModelName(parsed.name);
            toast.success("Template reverted to default!");
            mutate(templateSWRKey);
        } catch (error) {
            console.error("Error reverting LLM template:", error);
            toast.error("Failed to revert template. Please try again.");
        } finally {
            setIsSavingTemplate(false);
        }
    };

    const handleDeleteTemplate = async () => {
        if (!profileId || !currentTemplate?.id) {
            toast.error("No template to delete or profile not set.");
            return;
        }
        setIsDeletingTemplate(true);
        try {
            await apiFetch(`profiles/template`, { method: "DELETE" });
            mutate(templateSWRKey, null, { revalidate: false });
            toast.success("Template deleted!");
            setSysMsg(defaultSysMsg);
            setPromptText(defaultPrompt);
            const parsed = parseModel(defaultModel);
            setProvider(parsed.provider);
            setModelName(parsed.name);
            setCurrentTemplate(null);
        } catch (error) {
            console.error("Error deleting LLM template:", error);
            toast.error("Failed to delete template. Please try again.");
        } finally {
            setIsDeletingTemplate(false);
        }
    };

    // The provider options always include the current provider, even if it
    // isn't configured in this deployment, so the select stays in sync.
    const providerOptions: ProviderStatus[] = providers ?? [];
    const hasCurrentProvider = providerOptions.some((p) => p.provider === provider);

    const showProfileMessage = (message: string) => (
        <div className="p-6 text-center text-gray-500 dark:text-gray-400">
            <p>{message}</p>
            <p>Please set or create a profile using the menu (☰).</p>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">
            <div className="max-w-4xl mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold mb-6 text-center sm:text-center">
                    Profile Dashboard
                </h1>

                <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg">
                    <nav className="flex flex-wrap -mb-px justify-center space-x-4 border-b border-gray-200 dark:border-gray-700">
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
                                <div className="flex flex-col gap-4">
                                    <div className="flex-1 text-center text-gray-600 dark:text-gray-400">
                                        Active Profile
                                    </div>
                                    <div className="flex-1 text-center font-semibold">
                                        {profileId}
                                    </div>
                                </div>
                            ) : (
                                showProfileMessage("No active profile.")
                            ))}
                        {activeTab === "files" &&
                            (!profileId ? (
                                showProfileMessage("Set a profile to view your files.")
                            ) : filesLoading ? (
                                <p className="text-center">Loading files…</p>
                            ) : filesError ? (
                                <p className="text-red-500 text-center">Error loading files.</p>
                            ) : files && files.length > 0 ? (
                                <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                                    {files.map((file) => (
                                        <div
                                            key={file.id}
                                            className="flex items-center justify-between bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow"
                                        >
                                            <a
                                                href={formatStaticUrl(API_BASE, file.url)}
                                                download={file.name}
                                                className="flex-1 mr-4 overflow-hidden"
                                            >
                                                <div className="font-medium text-gray-800 dark:text-gray-100 truncate">
                                                    {truncateFilename(file.name)}
                                                </div>
                                            </a>
                                            <button
                                                onClick={() => handleDeleteFile(file.id)}
                                                disabled={deletingFileId === file.id}
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
                                <p className="text-center">No files found for this profile.</p>
                            ))}
                        {activeTab === "transcripts" &&
                            (!profileId ? (
                                showProfileMessage("Set a profile to view your transcripts.")
                            ) : transcriptsLoading ? (
                                <p className="text-center">Loading transcripts…</p>
                            ) : transcriptsError ? (
                                <p className="text-red-500 text-center">
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
                                                    {truncateFilename(transcript.id, 4, 4)}
                                                </div>
                                                <div className="flex space-x-2">
                                                    {transcript.url && (
                                                        <button
                                                            onClick={() =>
                                                                handleDownloadTranscript(transcript)
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
                                                    )}
                                                    <button
                                                        onClick={() =>
                                                            handleDeleteTranscript(transcript.id)
                                                        }
                                                        disabled={
                                                            deletingTranscriptId === transcript.id
                                                        }
                                                        className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors ${
                                                            deletingTranscriptId === transcript.id
                                                                ? "bg-red-800 cursor-not-allowed"
                                                                : "bg-red-600 hover:bg-red-500"
                                                        }`}
                                                    >
                                                        {deletingTranscriptId === transcript.id
                                                            ? "Deleting…"
                                                            : "Delete"}
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="text-gray-800 dark:text-gray-100 mb-2 whitespace-pre-wrap">
                                                {transcript.text}
                                            </div>
                                            {transcript.llm_explanation && (
                                                <div className="prose dark:prose-invert prose-sm max-w-none border-t border-zinc-700 pt-3 mt-3">
                                                    <ReactMarkdown remarkPlugins={[remarkBreaks]}>
                                                        {transcript.llm_explanation}
                                                    </ReactMarkdown>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-center">
                                    No transcripts found for this profile.
                                </p>
                            ))}

                        {activeTab === "gpt-template" &&
                            (!profileId ? (
                                showProfileMessage("Set a profile to manage LLM templates.")
                            ) : templateLoading ? (
                                <p className="text-center">Loading LLM Template...</p>
                            ) : templateError && (templateError as ApiError).status !== 404 ? (
                                <p className="text-red-500 text-center">
                                    Error loading LLM Template.
                                </p>
                            ) : (
                                <div className="space-y-6 flex flex-col">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        Customize your LLM template for word explanations. Use{" "}
                                        <code>{"{sentence}"}</code> and <code>{"{focus}"}</code>{" "}
                                        placeholders.
                                    </p>
                                    <div className="grid gap-4 sm:grid-cols-2">
                                        <div>
                                            <label
                                                htmlFor="provider"
                                                className="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
                                            >
                                                Provider
                                            </label>
                                            <select
                                                id="provider"
                                                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                                value={provider}
                                                onChange={(e) => setProvider(e.target.value)}
                                            >
                                                {!hasCurrentProvider && (
                                                    <option value={provider}>{provider}</option>
                                                )}
                                                {providerOptions.map((p) => (
                                                    <option
                                                        key={p.provider}
                                                        value={p.provider}
                                                        disabled={!p.available}
                                                    >
                                                        {p.provider}
                                                        {p.available ? "" : " (not configured)"}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label
                                                htmlFor="modelName"
                                                className="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
                                            >
                                                Model
                                            </label>
                                            <input
                                                id="modelName"
                                                type="text"
                                                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                                value={modelName}
                                                onChange={(e) => setModelName(e.target.value)}
                                                placeholder="e.g. gpt-4.1-mini"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label
                                            htmlFor="sysMsg"
                                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                        >
                                            System Message
                                        </label>
                                        <textarea
                                            id="sysMsg"
                                            value={sysMsg}
                                            onChange={(e) => setSysMsg(e.target.value)}
                                            rows={6}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 resize-none overflow-auto"
                                            placeholder={currentTemplate ? "" : defaultSysMsg}
                                        />
                                    </div>
                                    <div>
                                        <label
                                            htmlFor="promptText"
                                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                        >
                                            User Prompt
                                        </label>
                                        <textarea
                                            id="promptText"
                                            value={promptText}
                                            onChange={(e) => setPromptText(e.target.value)}
                                            rows={8}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 resize-none overflow-auto"
                                            placeholder={currentTemplate ? "" : defaultPrompt}
                                        />
                                    </div>
                                    <div className="flex flex-col sm:flex-row justify-center items-center space-y-3 sm:space-y-0 sm:space-x-4 mt-4">
                                        <button
                                            onClick={handleSaveTemplate}
                                            disabled={isSavingTemplate || isDeletingTemplate}
                                            className="w-full sm:w-auto px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50"
                                        >
                                            {isSavingTemplate
                                                ? "Saving..."
                                                : currentTemplate
                                                  ? "Update Template"
                                                  : "Create Template"}
                                        </button>
                                        {currentTemplate && (
                                            <>
                                                <button
                                                    onClick={handleRevertToDefaultTemplate}
                                                    disabled={
                                                        isSavingTemplate || isDeletingTemplate
                                                    }
                                                    className="w-full sm:w-auto px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-md shadow-sm disabled:opacity-50"
                                                >
                                                    Revert to Default
                                                </button>
                                                <button
                                                    onClick={handleDeleteTemplate}
                                                    disabled={
                                                        isDeletingTemplate || isSavingTemplate
                                                    }
                                                    className="w-full sm:w-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md shadow-sm disabled:opacity-50"
                                                >
                                                    {isDeletingTemplate
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
