/**
 * @packageDocumentation This component provides a settings drawer for the video player.
 * It allows the user to load video and subtitle files, generate subtitles,
 * convert videos to MP4, and customize the appearance of the subtitles.
 */

import React, { useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import { apiFetch } from "../services/api";
import { toastApiError } from "../utils/apiErrorToaster";
import { formatStaticUrl, uploadFile } from "../utils/fileUtils";
import {
    ConvertVideoResponse,
    GenerateSrtResponse,
    SettingsDrawerProps,
    ProfileFile,
} from "../types/types";
import { useProfile } from "../contexts/ProfileContext";
import { useSubtitleSettings } from "../contexts/SubtitleSettingsContext";
import { usePlayer } from "../contexts/PlayerContext";
import { API_BASE } from "../constants/user-page";

const comprehensiveVideoAcceptList = [
    // Common Formats
    "video/mp4",
    ".mp4",
    "video/quicktime",
    ".mov",
    "video/x-matroska",
    ".mkv",
    "video/webm",
    ".webm",
    "video/x-msvideo",
    ".avi",
    "video/x-flv",
    ".flv",
    "video/x-ms-wmv",
    ".wmv",
    "video/mpeg",
    ".mpeg",
    ".mpg",
    "video/x-m4v",
    ".m4v",
    // More Specific
    "video/3gpp",
    ".3gp",
    "video/3gpp2",
    ".3g2",
    "video/ogg",
    ".ogv",
    "video/mp2t",
    ".ts",
    // Other formats FFMPEG can handle
    ".asf",
    ".divx",
    ".f4v",
    ".rmvb",
    ".vob",
    ".mts",
    ".m2ts",
].join(",");

/**
 * The SettingsDrawer component.
 *
 * This component is responsible for the following:
 * - Allowing the user to load video and subtitle files.
 * - Generating subtitles from a video file.
 * - Converting a video file to MP4 format.
 * - Customizing the appearance of the subtitles.
 *
 * @param {SettingsDrawerProps} props The props for the component.
 * @returns {JSX.Element} The SettingsDrawer component.
 */
export default function SettingsDrawer({
    video,
    srt,
    onVideo,
    onVideoUrl,
    onSrt,
    onClose,
    showFurigana,
    onToggleFurigana,
}: SettingsDrawerProps): JSX.Element {
    // Reference to Video
    const videoInputRef = useRef<HTMLInputElement | null>(null);
    // Reference to Subtitles
    const srtInputRef = useRef<HTMLInputElement | null>(null);
    // Subtitle Style Context
    const { subtitleStyle, setSubtitleStyle, resetSubtitleStyle } =
        useSubtitleSettings();
    // Download Subtitle File URL
    const [generatedSrtDownloadUrl, setGeneratedSrtDownloadUrl] = useState<
        string | null
    >(null);
    // Downlod Video File URL
    const [convertedVideoDownloadUrl, setConvertedVideoDownloadUrl] = useState<
        string | null
    >(null);

    // Active Tab State
    const [activeTab, setActiveTab] = useState<
        "nowPlayingTab" | "subtitleSettingsTab" | "loadTab"
    >("loadTab");

    // Generating Subtitle State
    const [generatingSrt, setGeneratingSrt] = useState(false);
    // Converting Video State
    const [convertingVideo, setConvertingVideo] = useState(false);
    // Get Saved Profile Files
    const [profileFiles, setProfileFiles] = useState<ProfileFile[]>([]);
    // Set Profile Context
    const { profileId } = useProfile();
    const {
        videoFileName,
        setVideoFileName,
        srtFileName,
        setSrtFileName,
        clearPlayerState,
    } = usePlayer();

    const fetchProfileFiles = async () => {
        try {
            const files = await apiFetch<ProfileFile[]>("/profiles/files", {
                method: "GET",
            });
            setProfileFiles(files);
        } catch (error) {
            toastApiError(error);
        }
    };
    useEffect(() => {
        if (activeTab === "loadTab" && profileId) {
            fetchProfileFiles();
        }
    }, [activeTab, profileId]);

    const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] ?? null;
        onVideo(file);
        if (file) {
            setVideoFileName(file.name);
        }

        if (onVideoUrl && file) {
            onVideoUrl("");
        }
        setGeneratedSrtDownloadUrl(null);
        setConvertedVideoDownloadUrl(null);
    };

    const handleSrtChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] ?? null;
        if (file) {
            setSrtFileName(file.name);
        }
        onSrt(file);
    };

    const handleProfileFileSelect = async (file: ProfileFile) => {
        const fullUrl = formatStaticUrl(API_BASE, file.get_url);
        if (file.file_type === "mp4") {
            onVideoUrl?.(fullUrl);
            setVideoFileName(file.get_url);
        } else if (file.file_type === "srt") {
            try {
                const response = await fetch(fullUrl);
                const srtContent = await response.text();
                const srtFile = new File([srtContent], file.file_name, {
                    type: "application/x-subrip",
                });
                onSrt(srtFile);
                setSrtFileName(srtFile.name);
            } catch (error) {
                toast.error("Error loading subtitle file.");
            }
        }
    };
    const handleGenerateSrt = async () => {
        if (!video) return;
        setGeneratingSrt(true);
        const tId = toast.loading("Uploading...");
        try {
            // Send Request
            const result: GenerateSrtResponse = await uploadFile(video, `${API_BASE}video/generate_srt`, (progress) => {toast.loading(`Uploading... ${progress.toFixed(0)}%`, {id: tId})});
            toast.loading("Generating...", {id: tId})


            if (result.srt_content) {
                // Create SRT File from string response
                const generatedSrtFile = new File(
                    [result.srt_content],
                    `${video.name}.srt`,
                    { type: "application/x-subrip" }
                );
                onSrt(generatedSrtFile);
                setSrtFileName(generatedSrtFile.name);
                toast.success("Subtitles Generated!", { id: tId });
                const blob = new Blob([result.srt_content], {
                    type: "application/x-subrip",
                });
                setGeneratedSrtDownloadUrl(URL.createObjectURL(blob));
            } else {
                throw new Error("SRT content not found in response.");
            }
        } catch (err: any) {
            toastApiError(err, tId);
        } finally {
            setGeneratingSrt(false);
        }
    };

    const handleConvertToMp4 = async () => {
        if (!video) return;
        // Skip if video name contains `.mp4`
        if (video.name.toLowerCase().endsWith(".mp4")) {
            toast.success("Skipping - Already MP4");
            if (onVideoUrl) onVideoUrl("");
            onVideo(video);
            return;
        }
        setConvertingVideo(true);
        const tId = toast.loading("Uploading...");
        try {
            const result: ConvertVideoResponse = await uploadFile(video, `${API_BASE}video/convert_to_mp4`, (progress) => {toast.loading(`Uploading... ${progress.toFixed(0)}%`, {id: tId})});
            toast.loading("Converting...", {id: tId})

            if (result.converted_video_url) {
                onVideoUrl?.(
                    formatStaticUrl(API_BASE, result.converted_video_url)
                );
                setConvertedVideoDownloadUrl(
                    formatStaticUrl(API_BASE, result.converted_video_url)
                );
                setVideoFileName(result.converted_video_url);
                toast.success("Conversion complete!", { id: tId });
            } else {
                throw new Error("Converted video URL not found in response.");
            }
        } catch (err: any) {
            toastApiError(err, tId);
        } finally {
            setConvertingVideo(false);
        }
    };

    // Disable UI request elements while True
    const isBusy = generatingSrt || convertingVideo;
    // Converted videos from profile
    const videoFiles = profileFiles.filter((f) => f.file_type === "mp4");
    // Generated SRT files from profile
    const subtitleFiles = profileFiles.filter((f) => f.file_type === "srt");
    return (
        <motion.aside
            initial={{ width: 0 }}
            animate={{ width: 320 }}
            exit={{ width: 0 }}
            transition={{ type: "tween", duration: 0.2 }}
            className="flex-shrink-0 h-full bg-neutral-900 border-r border-neutral-700 overflow-y-auto"
        >
            <div className="flex flex-col h-full">
                <div className="flex justify-center space-x-5 items-center px-6 py-4 border-b border-neutral-700">
                    <h2 className="text-xl font-semibold text-neutral-100 text-center flex-1">
                        Settings
                    </h2>
                    <button
                        onClick={onClose}
                        disabled={isBusy}
                        className="text-neutral-400 hover:text-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        ✕
                    </button>
                </div>
                <div className={"flex border-b border-neutral-700 mb-4"}>
                    <button
                        className={`flex-1 py-2 px-2 text-xs text-center sm:text-base ${
                            activeTab === "nowPlayingTab"
                                ? "border-b-2 border-emerald-400 text-white"
                                : "text-neutral-400 hover:text-neutral-200"
                        }`}
                        onClick={() => setActiveTab("nowPlayingTab")}
                    >
                        Playing
                    </button>
                    <button
                        className={`flex-1 py-2 text-sm sm:text-base ${
                            activeTab === "subtitleSettingsTab"
                                ? "border-b-2 border-emerald-400 text-white"
                                : "text-neutral-400 hover:text-neutral-200"
                        }`}
                        onClick={() => setActiveTab("subtitleSettingsTab")}
                    >
                        Subtitles
                    </button>
                    <button
                        className={`flex-1 py-2 text-sm sm:text-base ${
                            activeTab === "loadTab"
                                ? "border-b-2 border-emerald-400 text-white"
                                : "text-neutral-400 hover:text-neutral-200"
                        }`}
                        onClick={() => setActiveTab("loadTab")}
                    >
                        Load
                    </button>
                </div>
                <div className="flex-1 px-6 py-4 space-y-8 overflow-y-auto">
                    {activeTab === "nowPlayingTab" ? (
                        <section className="space-y-10">
                            <div className="space-y-3">
                                <h3 className="text-lg font-semibold text-center mb-2">
                                    Video
                                </h3>
                                {videoFileName ? (
                                    <p className="text-neutral-500 text-center text-base italic truncate">
                                        {videoFileName}
                                    </p>
                                ) : (
                                    <p className="text-neutral-500 text-center text-sm italic">
                                        No video loaded
                                    </p>
                                )}
                            </div>

                            <div className="space-y-3">
                                <h3 className="text-lg font-semibold mb-2 text-center">
                                    Subtitles
                                </h3>
                                {srtFileName ? (
                                    <p className="text-neutral-500 text-center text-base truncate">
                                        {srtFileName}
                                    </p>
                                ) : (
                                    <p className="text-neutral-500 text-center text-sm italic">
                                        No subtitles loaded
                                    </p>
                                )}
                            </div>
                            <div className="space-y-3">
                                <h3 className="text-lg font-semibold mb-2 text-center">
                                    Utilities
                                </h3>
                                <button
                                    onClick={handleGenerateSrt}
                                    disabled={!video || isBusy}
                                    className="w-full mb-3 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {generatingSrt
                                        ? "Generating..."
                                        : "Generate SRT from Video"}
                                </button>

                                <button
                                    onClick={handleConvertToMp4}
                                    disabled={!video || isBusy}
                                    className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {convertingVideo
                                        ? "Converting…"
                                        : "Convert Video to MP4"}
                                </button>
                                <button
                                    onClick={clearPlayerState}
                                    disabled={isBusy}
                                    className="w-full py-2 bg-red-600 text-white rounded hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Reset Player
                                </button>
                            </div>
                            {generatedSrtDownloadUrl && (
                                <a
                                    href={generatedSrtDownloadUrl}
                                    download={`${
                                        video?.name || "generated"
                                    }.srt`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="mt-3 block text-center text-sm text-emerald-400 hover:underline"
                                >
                                    Download Generated SRT
                                </a>
                            )}

                            {convertedVideoDownloadUrl && (
                                <a
                                    href={convertedVideoDownloadUrl}
                                    download
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="mt-3 block text-center text-sm text-blue-400 hover:underline"
                                >
                                    Download Converted Video
                                </a>
                            )}
                        </section>
                    ) : activeTab === "subtitleSettingsTab" ? (
                        <>
                            <section>
                                <h3 className="text-lg font-semibold text-center text-neutral-200 mb-4">
                                    Options
                                </h3>
                                <div className="flex flex-col text-center justify-center space-y-3">
                                    <span className="block mb-2 text-sm font-medium text-neutral-500 italic">
                                        Show Furigana
                                    </span>
                                    <div className="flex justify-center">
                                        <button
                                            onClick={onToggleFurigana}
                                            disabled={isBusy}
                                            className={`px-4 py-2 rounded-md font-semibold transition-colors text-sm ${
                                                showFurigana
                                                    ? "bg-green-600 hover:bg-green-500 text-white"
                                                    : "bg-neutral-700 hover:bg-neutral-600 text-neutral-300"
                                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                                        >
                                            {showFurigana ? "On" : "Off"}
                                        </button>
                                    </div>
                                </div>
                            </section>
                            <section className="space-y-5 items-center justify-center">
                                <h3 className="text-lg text-center font-semibold text-neutral-200 mb-4">
                                    Style
                                </h3>
                                <div className="flex flex-col text-center space-y-3">
                                    <label
                                        htmlFor="font-size"
                                        className="block mb-2 text-sm font-medium text-neutral-500 italic"
                                    >
                                        Font Size : {subtitleStyle.fontSize} px
                                    </label>
                                    <div className="flex items-center justify-between">
                                        <input
                                            id="font-size"
                                            type="range"
                                            min="12"
                                            max="48"
                                            value={subtitleStyle.fontSize}
                                            onChange={(e) =>
                                                setSubtitleStyle({
                                                    ...subtitleStyle,
                                                    fontSize: Number(
                                                        e.target.value
                                                    ),
                                                })
                                            }
                                            className="w-full h-1 mb-6 bg-gray-200 rounded-lg appearance-none cursor-pointer range-sm dark:bg-gray-700"
                                        />
                                    </div>
                                </div>
                                <div className="flex flex-col text-center space-y-3">
                                    <label
                                        htmlFor="bg-opacity"
                                        className="block mb-2 text-sm font-medium text-neutral-500 italic"
                                    >
                                        Background Opacity :{" "}
                                        {(
                                            subtitleStyle.backgroundOpacity *
                                            100
                                        ).toFixed(0)}
                                        %
                                    </label>
                                    <div className="flex items-center justify-between">
                                        <input
                                            id="bg-opacity"
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.1"
                                            value={
                                                subtitleStyle.backgroundOpacity
                                            }
                                            onChange={(e) =>
                                                setSubtitleStyle({
                                                    ...subtitleStyle,
                                                    backgroundOpacity: Number(
                                                        e.target.value
                                                    ),
                                                })
                                            }
                                            className="w-full h-1 mb-6 bg-gray-200 rounded-lg appearance-none cursor-pointer range-sm dark:bg-gray-700"
                                        />
                                    </div>
                                </div>
                                <div className="flex flex-col text-center space-y-3">
                                    <label
                                        htmlFor="position"
                                        className="block mb-2 text-sm font-medium text-neutral-500 italic"
                                    >
                                        Position : {subtitleStyle.position}%
                                    </label>
                                    <div className="flex items-center justify-between">
                                        <input
                                            id="position"
                                            type="range"
                                            min="0"
                                            max="90"
                                            step="1"
                                            value={subtitleStyle.position}
                                            onChange={(e) =>
                                                setSubtitleStyle({
                                                    ...subtitleStyle,
                                                    position: Number(
                                                        e.target.value
                                                    ),
                                                })
                                            }
                                            className="w-full h-1 mb-6 bg-gray-200 rounded-lg appearance-none cursor-pointer range-sm dark:bg-gray-700"
                                        />
                                    </div>
                                </div>
                                <div className="flex flex-col text-center justify-center space-y-3">
                                    <label
                                        htmlFor="font-color"
                                        className="block mb-2 text-sm font-medium text-neutral-500 italic"
                                    >
                                        Font Color
                                    </label>
                                    <div className="flex justify-center">
                                        <input
                                            id="font-color"
                                            type="color"
                                            value={subtitleStyle.fontColor}
                                            onChange={(e) =>
                                                setSubtitleStyle({
                                                    ...subtitleStyle,
                                                    fontColor: e.target.value,
                                                })
                                            }
                                            className="w-12 h-8 rounded-md bg-inherit"
                                        />
                                    </div>
                                </div>
                                <div className="flex flex-col text-center justify-center space-y-3">
                                    <label
                                        htmlFor="bg-color"
                                        className="block mb-2 text-sm font-medium text-neutral-500 italic"
                                    >
                                        Background Color
                                    </label>
                                    <div className="flex justify-center">
                                        <input
                                            id="bg-color"
                                            type="color"
                                            value={
                                                subtitleStyle.backgroundColor
                                            }
                                            onChange={(e) =>
                                                setSubtitleStyle({
                                                    ...subtitleStyle,
                                                    backgroundColor:
                                                        e.target.value,
                                                })
                                            }
                                            className="w-12 h-8 rounded-md bg-inherit"
                                        />
                                    </div>
                                </div>
                                <button
                                    onClick={resetSubtitleStyle}
                                    className="w-full py-2 bg-gray-600 hover:bg-gray-500 text-white rounded"
                                >
                                    Reset Styles
                                </button>
                            </section>
                        </>
                    ) : (
                        <section className="space-y-10">
                            <div className="flex flex-col space-y-4">
                                <h3 className="text-lg font-semibold mb-2 text-center">
                                    From Device
                                </h3>
                                <button
                                    onClick={() =>
                                        videoInputRef.current?.click()
                                    }
                                    disabled={isBusy}
                                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {videoFileName
                                        ? "Change Video"
                                        : "Select Video"}
                                </button>
                                <input
                                    ref={videoInputRef}
                                    type="file"
                                    accept={comprehensiveVideoAcceptList}
                                    onChange={handleVideoChange}
                                    disabled={isBusy}
                                    className="hidden"
                                />

                                <button
                                    onClick={() => srtInputRef.current?.click()}
                                    disabled={isBusy}
                                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {srtFileName
                                        ? "Change Subtitles"
                                        : "Select Subtitles"}
                                </button>
                                <input
                                    ref={srtInputRef}
                                    type="file"
                                    accept=".srt"
                                    onChange={handleSrtChange}
                                    disabled={isBusy}
                                    className="hidden"
                                />
                            </div>
                            <div className="flex flex-col space-y-4">
                                <h3 className="text-lg font-semibold mb-2 text-center">
                                    From Profile
                                </h3>
                                <div className="space-y-2">
                                    <h4 className="text-md text-center font-semibold text-neutral-300">
                                        Videos
                                    </h4>
                                    <ul className="max-h-32 overflow-y-auto text-sm text-neutral-400 space-y-1">
                                        {videoFiles.length > 0 ? (
                                            videoFiles.map((file) => (
                                                <li
                                                    key={file.id}
                                                    onClick={() =>
                                                        handleProfileFileSelect(
                                                            file
                                                        )
                                                    }
                                                    className="cursor-pointer hover:text-emerald-400 truncate p-1 rounded bg-neutral-800"
                                                >
                                                    {file.file_name}
                                                </li>
                                            ))
                                        ) : (
                                            <li className=" text-center italic p-1 rounded bg-neutral-800">
                                                Profile has no videos
                                            </li>
                                        )}
                                    </ul>
                                </div>
                                <div className="space-y-2">
                                    <h4 className="text-md text-center font-semibold text-neutral-300">
                                        Subtitles
                                    </h4>
                                    <ul className="max-h-32 overflow-y-auto text-sm text-neutral-400 space-y-1">
                                        {subtitleFiles.length > 0 ? (
                                            subtitleFiles.map((file) => (
                                                <li
                                                    key={file.id}
                                                    onClick={() =>
                                                        handleProfileFileSelect(
                                                            file
                                                        )
                                                    }
                                                    className="cursor-pointer hover:text-emerald-400 truncate p-1 rounded bg-neutral-800"
                                                >
                                                    {file.file_name}
                                                </li>
                                            ))
                                        ) : (
                                            <li className=" text-center italic p-1 rounded bg-neutral-800">
                                                Profile has no subtitles
                                            </li>
                                        )}
                                    </ul>
                                </div>
                            </div>
                        </section>
                    )}
                </div>
            </div>
        </motion.aside>
    );
}
