/**
 * @packageDocumentation The video surface: the video fills the stage via
 * `object-contain` (so it's as large as possible, up- or down-scaled, never
 * distorted), and click-through overlay subtitles are anchored to the *painted*
 * frame (computed by useVideoBox) rather than the element box.
 */

import React, { useCallback, useState } from "react";
import TokenizedText from "@/shared/components/TokenizedText";
import { hexToRgba } from "@/shared/format/color";
import { useSubtitleSettings } from "@/contexts/SubtitleSettingsContext";
import { useVideoBox } from "../hooks/useVideoBox";
import type { Cue } from "../types";

export interface VideoStageProps {
    onVideoEl: (el: HTMLVideoElement | null) => void;
    blobUrl: string | null;
    activeCue: Cue | null;
    showFurigana: boolean;
    preparing: boolean;
    onWordClick: (sentence: string, word: string) => void;
}

/**
 * The VideoStage component.
 *
 * @param {VideoStageProps} props The props.
 * @returns {JSX.Element} The video + overlay subtitles.
 */
export function VideoStage({
    onVideoEl,
    blobUrl,
    activeCue,
    showFurigana,
    preparing,
    onWordClick,
}: VideoStageProps) {
    const { subtitleStyle } = useSubtitleSettings();
    const [el, setEl] = useState<HTMLVideoElement | null>(null);
    const setRef = useCallback(
        (node: HTMLVideoElement | null) => {
            setEl(node);
            onVideoEl(node);
        },
        [onVideoEl]
    );
    const box = useVideoBox(el);

    // Click the video body to toggle play/pause, but leave the native control
    // strip (bottom ~48px) to the browser so its buttons keep working.
    const togglePlay = (e: React.MouseEvent<HTMLVideoElement>) => {
        const v = e.currentTarget;
        if (e.clientY > v.getBoundingClientRect().bottom - 48) return;
        if (v.paused) v.play().catch(() => undefined);
        else v.pause();
    };

    const textStyle: React.CSSProperties = {
        color: subtitleStyle.fontColor,
        fontSize: `${subtitleStyle.fontSize}px`,
        backgroundColor: hexToRgba(subtitleStyle.backgroundColor, subtitleStyle.backgroundOpacity),
        textShadow: subtitleStyle.textShadow,
    };

    // Anchor the overlay to the painted frame when known, else the element box.
    const overlayPos: React.CSSProperties = box
        ? {
              left: box.left,
              width: box.width,
              bottom: box.top + (subtitleStyle.position / 100) * box.height,
          }
        : { left: 0, right: 0, bottom: `${subtitleStyle.position}%` };

    return (
        <div className="relative h-full w-full bg-black">
            <video
                id="mirumoji-player"
                ref={setRef}
                src={blobUrl ?? undefined}
                controls
                playsInline
                crossOrigin="anonymous"
                onClick={togglePlay}
                // Native fullscreen would show only the <video>, dropping the
                // overlay subtitles, so disable it (+ PiP).
                controlsList="nofullscreen noremoteplayback"
                disablePictureInPicture
                {...{ "webkit-playsinline": "true" }}
                className="h-full w-full object-contain focus:outline-none"
            />

            {preparing && (
                <div className="pointer-events-none absolute right-3 top-3 animate-pulse rounded-md bg-black/70 px-3 py-1 text-xs text-ink">
                    Loading Subs ...
                </div>
            )}

            {activeCue && (
                <div
                    className="pointer-events-none absolute flex justify-center px-4 text-center"
                    style={overlayPos}
                >
                    <span
                        lang="ja"
                        className="inline-block max-w-[95%] break-words rounded-lg px-3 py-1.5 font-semibold leading-relaxed shadow-xl sm:px-5 sm:py-2.5"
                        style={textStyle}
                    >
                        {activeCue.words && activeCue.words.length > 0 ? (
                            <TokenizedText
                                words={activeCue.words}
                                sentence={activeCue.raw}
                                showFurigana={showFurigana}
                                onWordClick={onWordClick}
                            />
                        ) : (
                            activeCue.raw
                        )}
                    </span>
                </div>
            )}
        </div>
    );
}
