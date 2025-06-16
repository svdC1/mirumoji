import React, { useEffect, useRef, useState } from "react";
import SrtParser2 from "srt-parser-2";
import { getTokenizer } from "../tokenizer";
import WordDialog from "./WordDialog";
import { isKanji, toHiragana } from "../utils/languageUtils";
import { IpadicFeatures } from "kuromoji";

interface Cue {
    start: number;
    end: number;
    tokens: IpadicFeatures[];
    raw: string;
}

interface Props {
    video: File;
    videoUrl?: string;
    srt: File | null;
    showFurigana: boolean;
}

const toSec = (t: string): number => {
    const [h, m, rest] = t.split(":");
    const [s, ms] = rest.split(",");
    return +h * 3600 + +m * 60 + +s + +ms / 1000;
};

export default function SubtitlePlayer({
    video,
    srt,
    videoUrl,
    showFurigana,
}: Props) {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const [blobUrl, setBlobUrl] = useState<string>(() =>
        videoUrl ? videoUrl : URL.createObjectURL(video)
    );
    const [cues, setCues] = useState<Cue[]>([]);
    const [activeIdx, setActiveIdx] = useState<number | null>(null);
    const [dialog, setDialog] = useState<{
        sentence: string;
        word: string;
        cueStart: number;
        cueEnd: number;
    } | null>(null);

    useEffect(() => {
        if (videoUrl) {
            setBlobUrl(videoUrl);
        } else if (video) {
            const url = URL.createObjectURL(video);
            setBlobUrl(url);
            return () => URL.revokeObjectURL(url);
        }
    }, [video, videoUrl]);

    useEffect(() => {
        videoRef.current?.load();
    }, [blobUrl]);

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
                console.error("Tokenizer failed, falling back", err);
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

            {activeIdx !== null && cues[activeIdx] && (
                <div className="absolute bottom-4 w-full px-2 text-center pointer-events-none">
                    <span className="inline-block mx-auto bg-black/60 px-2 sm:px-4 md:px-6 py-1 sm:py-2 md:py-3 rounded-lg pointer-events-auto font-semibold shadow-xl max-w-[95%] break-words text-xl sm:text-2xl md:text-3xl lg:text-4xl">
                        {cues[activeIdx].tokens.map((token, i) => {
                            const shouldDisplayFurigana =
                                showFurigana &&
                                token.reading &&
                                token.surface_form !== token.reading &&
                                token.surface_form.split("").some(isKanji);
                            const furiganaText = shouldDisplayFurigana
                                ? toHiragana(token.reading!)
                                : null;

                            return (
                                <button
                                    key={i}
                                    className="inline-flex flex-col items-center mx-1 group align-bottom hover:text-yellow-300"
                                    onClick={() => {
                                        const currentCue = cues[activeIdx];
                                        if (currentCue) {
                                            setDialog({
                                                sentence: currentCue.raw,
                                                word: token.surface_form,
                                                cueStart: currentCue.start,
                                                cueEnd: currentCue.end,
                                            });
                                        }
                                    }}
                                >
                                    {shouldDisplayFurigana && furiganaText && (
                                        <span className="text-xs text-gray-400 group-hover:text-yellow-300">
                                            {furiganaText}
                                        </span>
                                    )}
                                    <span className="underline group-hover:text-yellow-300">
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
