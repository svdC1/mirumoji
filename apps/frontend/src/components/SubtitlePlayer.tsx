/**
 * @packageDocumentation This component is a video player with interactive subtitles.
 * It displays subtitles on top of the video, and allows the user to click on
 * words to get more information about them.
 */

import React, { useEffect, useRef, useState } from "react";
import SrtParser2 from "srt-parser-2";
import { getTokenizer } from "../services/tokenizer";
import WordDialog from "./WordDialog";
import { isKanji, toHiragana } from "../utils/languageUtils";
import { useSubtitleSettings } from "../contexts/SubtitleSettingsContext";
import { IpadicFeatures } from "kuromoji";
import { Cue, SubtitlePlayerProps } from "../types/types";
import { toSec, hexToRgba } from "../utils/formatters";

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

    // Parse SRT file and tokenize cues
    useEffect(() => {
        (async () => {
            if (!srt) {
                setCues([]);
                return;
            }
            const txt = await srt.text();
            const parser = new SrtParser2();
            const raw = parser.fromSrt(txt.trim());
            try {
                const tokenizer = await getTokenizer();
                // Tokenize raw Cues with Kurmoji
                const processed: Cue[] = raw.map((c) => {
                    const sentence = c.text.replace(/<[^>]+>/g, "").trim();
                    const tokens = tokenizer.tokenize(sentence);
                    return {
                        start: toSec(c.startTime),
                        end: toSec(c.endTime),
                        tokens,
                        raw: sentence,
                    };
                });
                setCues(processed);
            } catch (err) {
                console.error("Tokenizer Failed, falling back", err);
                // Empty Fallback Cue Array Which Splits on Every Character
                const fallback: Cue[] = raw.map((c) => ({
                    start: toSec(c.startTime),
                    end: toSec(c.endTime),
                    tokens: c.text
                        .trim()
                        .split("")
                        .map((char) => ({
                            surface_form: char,
                            reading: char,
                            word_type: "UNKNOWN",
                            pos: "名詞",
                            pos_detail_1: "一般",
                            pos_detail_2: "*",
                            pos_detail_3: "*",
                            conjugated_type: "*",
                            conjugated_form: "*",
                            basic_form: char,
                            pronunciation: char,
                        })) as IpadicFeatures[],
                    raw: c.text.trim(),
                }));
                setCues(fallback);
            }
        })();
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

    const activeCue = activeIdx !== null ? cues[activeIdx] : null;

    // Set Subtitle CSS Properties based on Style Context
    const computedSubtitleStyle: React.CSSProperties = {
        color: subtitleStyle.fontColor,
        fontSize: `${subtitleStyle.fontSize}px`,
        backgroundColor: hexToRgba(
            subtitleStyle.backgroundColor,
            subtitleStyle.backgroundOpacity
        ),
        textShadow: subtitleStyle.textShadow,
        bottom: `${subtitleStyle.position}%`,
    };
    // Set Furigana CSS Properties based on Style Context
    const computedFuriganaStyle: React.CSSProperties = {
        fontSize: `${Math.trunc(subtitleStyle.fontSize / 2.5)}px`,
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
                webkit-playsinline="true"
                className="w-full max-h-[92vh] bg-black rounded-xl overflow-hidden"
            />

            {activeCue && (
                <div
                    className="absolute w-full px-2 text-center pointer-events-none"
                    style={{ bottom: `${subtitleStyle.position}%` }}
                >
                    <span
                        className="inline-block mx-auto px-2 sm:px-4 md:px-6 py-1 sm:py-2 md:py-3 rounded-lg pointer-events-auto font-semibold shadow-xl max-w-[95%] break-words"
                        style={computedSubtitleStyle}
                    >
                        {activeCue.tokens.map((token, i) => {
                            const shouldDisplayFurigana =
                                showFurigana &&
                                token.reading &&
                                token.surface_form !== token.reading &&
                                token.surface_form.split("").some(isKanji);
                            const furiganaText = shouldDisplayFurigana
                                ? toHiragana(token.reading!)
                                : null;

                            return (
                                // Clickable Subtitle Tokens
                                <button
                                    key={i}
                                    className="inline-flex flex-col items-center mx-1 group align-bottom hover:text-yellow-300"
                                    onClick={() => {
                                        setDialog({
                                            sentence: activeCue.raw,
                                            word: !(token.basic_form === "*")
                                                ? token.basic_form
                                                : token.surface_form,
                                            cueStart: activeCue.start,
                                            cueEnd: activeCue.end,
                                        });
                                    }}
                                >
                                    {/*Furigana*/}
                                    {shouldDisplayFurigana && furiganaText && (
                                        <span
                                            className=" text-gray-400 group-hover:text-yellow-300"
                                            style={computedFuriganaStyle}
                                        >
                                            {furiganaText}
                                        </span>
                                    )}
                                    {/*Token*/}
                                    <span className="group-hover:text-yellow-300">
                                        {token.surface_form}
                                    </span>
                                </button>
                            );
                        })}
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
