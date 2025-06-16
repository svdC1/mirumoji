// src/components/SettingsDrawer.tsx
import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import { apiFetch, ApiError } from "../utils/api";
import { toastApiError } from "../utils/error_toaster";
import { formatStaticUrl } from "../utils/file_utils";
import { ConvertVideoResponse, GenerateSrtResponse } from "../types";
const API_BASE = "api/";
export interface Props {
    video: File | null;
    srt: File | null;
    onVideo: (file: File | null) => void;
    onVideoUrl?: (url: string) => void;
    onSrt: (file: File | null) => void;
    onClose: () => void;
    showFurigana: boolean;
    onToggleFurigana: () => void;
}

export default function SettingsDrawer({
    video,
    srt,
    onVideo,
    onVideoUrl,
    onSrt,
    onClose,
    showFurigana,
    onToggleFurigana,
}: Props) {
    const videoInputRef = useRef<HTMLInputElement | null>(null);
    const srtInputRef = useRef<HTMLInputElement | null>(null);

    const [generatedSrtDownloadUrl, setGeneratedSrtDownloadUrl] = useState<
        string | null
    >(null);
    const [convertedVideoDownloadUrl, setConvertedVideoDownloadUrl] = useState<
        string | null
    >(null);

    const [generatingSrt, setGeneratingSrt] = useState(false);
    const [convertingVideo, setConvertingVideo] = useState(false);

    const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] ?? null;
        onVideo(file);
        if (onVideoUrl && file) {
            onVideoUrl("");
        }
        setGeneratedSrtDownloadUrl(null);
        setConvertedVideoDownloadUrl(null);
    };

    const handleSrtChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] ?? null;
        onSrt(file);
    };

    const handleGenerateSrt = async () => {
        if (!video) return;
        setGeneratingSrt(true);
        const tId = toast.loading("Generating...");
        try {
            const formData = new FormData();
            formData.append("video_file", video, video.name);

            const result = await apiFetch<GenerateSrtResponse>(
                "/video/generate_srt",
                {
                    method: "POST",
                    body: formData,
                }
            );

            if (result.srt_content) {
                const generatedSrtFile = new File(
                    [result.srt_content],
                    `${video.name}.srt`,
                    { type: "application/x-subrip" }
                );
                onSrt(generatedSrtFile);
                toast.success("Subtitles generated!", { id: tId });
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
        if (video.name.toLowerCase().endsWith(".mp4")) {
            toast.success("File is already MP4 — Skipping conversion");
            if (onVideoUrl) onVideoUrl("");
            onVideo(video);
            return;
        }
        setConvertingVideo(true);
        const tId = toast.loading("Converting...");
        try {
            const formData = new FormData();
            formData.append("video_file", video, video.name);
            const result = await apiFetch<ConvertVideoResponse>(
                "/video/convert_to_mp4",
                {
                    method: "POST",
                    body: formData,
                }
            );

            if (result.converted_video_url) {
                onVideoUrl?.(
                    formatStaticUrl(API_BASE, result.converted_video_url)
                );
                setConvertedVideoDownloadUrl(
                    formatStaticUrl(API_BASE, result.converted_video_url)
                );
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

    const isBusy = generatingSrt || convertingVideo;

    return (
        <motion.aside
            initial={{ width: 0 }}
            animate={{ width: 320 }}
            exit={{ width: 0 }}
            transition={{ type: "tween", duration: 0.3 }}
            className="flex-shrink-0 h-full bg-neutral-900 border-r border-neutral-700 overflow-y-auto"
        >
            <div className="flex flex-col h-full">
                <div className="flex justify-between items-center px-6 py-4 border-b border-neutral-700">
                    <h2 className="text-xl font-semibold text-neutral-100">
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

                <div className="flex-1 px-6 py-4 space-y-8 overflow-y-auto">
                    <section>
                        <h3 className="text-lg font-semibold text-emerald-400 mb-2">
                            Now Playing
                        </h3>
                        <div className="space-y-1">
                            {video ? (
                                <p className="text-neutral-100 text-base truncate">
                                    Video: {video.name}
                                </p>
                            ) : (
                                <p className="text-neutral-500 text-sm italic">
                                    No video loaded
                                </p>
                            )}
                            {srt ? (
                                <p className="text-neutral-100 text-base truncate">
                                    Subtitle: {srt.name}
                                </p>
                            ) : (
                                <p className="text-neutral-500 text-sm italic">
                                    No subtitles loaded
                                </p>
                            )}
                        </div>
                    </section>

                    <section>
                        <h3 className="text-lg font-semibold text-neutral-200 mb-4">
                            Subtitle Display
                        </h3>
                        <div className="flex items-center justify-between">
                            <span className="text-neutral-100">
                                Show Furigana
                            </span>
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
                    </section>

                    <section>
                        <h3 className="text-lg font-semibold text-neutral-200 mb-4">
                            Load Media
                        </h3>
                        <div className="flex flex-col space-y-4">
                            <button
                                onClick={() => videoInputRef.current?.click()}
                                disabled={isBusy}
                                className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {video ? "Change Video" : "Select Video"}
                            </button>
                            <input
                                ref={videoInputRef}
                                type="file"
                                accept="video/*"
                                onChange={handleVideoChange}
                                disabled={isBusy}
                                className="hidden"
                            />

                            <button
                                onClick={() => srtInputRef.current?.click()}
                                disabled={isBusy}
                                className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {srt ? "Change Subtitles" : "Select Subtitles"}
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
                    </section>
                </div>

                <div className="px-6 py-4 border-t border-neutral-700">
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

                    {generatedSrtDownloadUrl && (
                        <a
                            href={generatedSrtDownloadUrl}
                            download={`${video?.name || "generated"}.srt`}
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
                </div>
            </div>
        </motion.aside>
    );
}
