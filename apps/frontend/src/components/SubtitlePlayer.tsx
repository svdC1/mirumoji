/**
 * @packageDocumentation This component is a video player with interactive subtitles.
 * It displays subtitles on top of the video, and allows the user to click on
 * words to get more information about them.
 */

import React, { useEffect, useRef, useState } from "react";
import SrtParser2 from "srt-parser-2";
import { apiTokenizeBatch } from "../services/dictApi";
import WordDialog from "./WordDialog";
import TokenizedText from "./TokenizedText";
import { useSubtitleSettings } from "../contexts/SubtitleSettingsContext";
import { Cue, SubtitlePlayerProps } from "../types/types";
import { toSec, hexToRgba } from "../utils/formatters";
import { usePlayer } from "../contexts/PlayerContext";

/**
 * The SubtitlePlayer component.
 *
 * This component is responsible for the following:
 * - Playing a video with subtitles.
 * - Parsing and displaying subtitles.
 * - Allowing the user to click on words in the subtitles to get more information.
 *
 * @param {SubtitlePlayerProps} props The props for the component.
 * @returns {JSX.Element} The SubtitlePlayer component.
 */
export default function SubtitlePlayer({
    video,
    srt,
    videoUrl,
    showFurigana,
}: SubtitlePlayerProps) {
    const { timestamp, setTimestamp } = usePlayer();
    // Video reference
    const videoRef = useRef<HTMLVideoElement | null>(null);
    // Video Blob URL for Download
    const [blobUrl, setBlobUrl] = useState<string>(() =>
        videoUrl ? videoUrl : URL.createObjectURL(video)
    );
    // Subtitle Cues
    const [cues, setCues] = useState<Cue[]>([]);
    // Active Cue Index in the Cues Array
    const [activeIdx, setActiveIdx] = useState<number | null>(null);
    // Word Dialog Information
    const [dialog, setDialog] = useState<{
        sentence: string;
        word: string;
        cueStart: number;
        cueEnd: number;
    } | null>(null);

    const { subtitleStyle } = useSubtitleSettings();

    // Set Blob URL
    useEffect(() => {
        if (videoUrl) {
            setBlobUrl(videoUrl);
        } else if (video) {
            const url = URL.createObjectURL(video);
            setBlobUrl(url);
            return () => URL.revokeObjectURL(url);
        }
    }, [video, videoUrl]);

    // Load video when blobUrl changes
    useEffect(() => {
        videoRef.current?.load();
    }, [blobUrl]);

    // Whether the SRT is being parsed + tokenized
    const [preparing, setPreparing] = useState(false);

    // Parse the SRT and pre-tokenize every cue in a single batch request, so
    // playback never tokenizes per-cue (no mid-video lag/flicker).
    useEffect(() => {
        let cancelled = false;
        (async () => {
            if (!srt) {
                setCues([]);
                return;
            }
            const txt = await srt.text();
            const parser = new SrtParser2();
            const parsed: Cue[] = parser.fromSrt(txt.trim()).map((c) => ({
                start: toSec(c.startTime),
                end: toSec(c.endTime),
                raw: c.text.replace(/<[^>]+>/g, "").trim(),
            }));

            setPreparing(true);
            try {
                const wordsList = await apiTokenizeBatch(parsed.map((c) => c.raw));
                if (cancelled) return;
                setCues(parsed.map((cue, i) => ({ ...cue, words: wordsList[i] })));
            } catch (err) {
                console.error("Failed to tokenize subtitles:", err);
                if (!cancelled) setCues(parsed); // fall back to raw text
            } finally {
                if (!cancelled) setPreparing(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [srt]);

    // Sync Cues with Video
    useEffect(() => {
        const v = videoRef.current;
        if (!v) return;
        const onTime = () => {
            const t = v.currentTime;
            const idx = cues.findIndex((q) => t >= q.start && t <= q.end);
            setActiveIdx(idx === -1 ? null : idx);
        };
        v.addEventListener("timeupdate", onTime);
        return () => v.removeEventListener("timeupdate", onTime);
    }, [cues]);

    useEffect(() => {
        const videoElement = videoRef.current;
        if (videoElement && timestamp) {
            videoElement.currentTime = timestamp;
        }

        const interval = setInterval(() => {
            if (videoElement) {
                setTimestamp(videoElement.currentTime);
            }
        }, 5000); // Save timestamp every 5 seconds

        return () => {
            clearInterval(interval);
            if (videoElement) {
                setTimestamp(videoElement.currentTime);
            }
        };
    }, [setTimestamp]);

    const activeCue = activeIdx !== null ? cues[activeIdx] : null;

    // Set Subtitle CSS Properties based on Style Context
    const computedSubtitleStyle: React.CSSProperties = {
        color: subtitleStyle.fontColor,
        fontSize: `${subtitleStyle.fontSize}px`,
        backgroundColor: hexToRgba(subtitleStyle.backgroundColor, subtitleStyle.backgroundOpacity),
        textShadow: subtitleStyle.textShadow,
        bottom: `${subtitleStyle.position}%`,
    };

    return (
        <div className="relative w-full flex flex-col items-center">
            <video
                id="mirumoji-player"
                ref={videoRef}
                src={blobUrl}
                controls
                playsInline
                crossOrigin="anonymous"
                {...{ "webkit-playsinline": "true" }}
                className="w-full max-h-[92vh] bg-black rounded-xl overflow-hidden"
            />

            {preparing && (
                <div className="absolute top-2 right-2 px-3 py-1 rounded-md bg-black/70 text-white text-xs animate-pulse pointer-events-none">
                    Preparing subtitles…
                </div>
            )}

            {activeCue && (
                <div
                    className="absolute select-none w-full px-2 text-center pointer-events-none"
                    style={{ bottom: `${subtitleStyle.position}%` }}
                >
                    <span
                        className="inline-block mx-auto px-2 sm:px-4 md:px-6 py-1 sm:py-2 md:py-3 rounded-lg pointer-events-auto font-semibold shadow-xl max-w-[95%] break-words"
                        style={computedSubtitleStyle}
                    >
                        {activeCue.words && activeCue.words.length > 0 ? (
                            <TokenizedText
                                words={activeCue.words}
                                sentence={activeCue.raw}
                                showFurigana={showFurigana}
                                onWordClick={(sentence, word) =>
                                    setDialog({
                                        sentence,
                                        word,
                                        cueStart: activeCue.start,
                                        cueEnd: activeCue.end,
                                    })
                                }
                            />
                        ) : (
                            activeCue.raw
                        )}
                    </span>
                </div>
            )}

            {dialog && (
                <WordDialog
                    sentence={dialog.sentence}
                    word={dialog.word}
                    onClose={() => setDialog(null)}
                    cueStart={dialog.cueStart}
                    cueEnd={dialog.cueEnd}
                    videoFile={video}
                    videoUrl={videoUrl}
                />
            )}
        </div>
    );
}
