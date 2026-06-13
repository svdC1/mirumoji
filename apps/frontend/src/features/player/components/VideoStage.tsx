/**
 * @packageDocumentation The video surface: the video fills the stage via
 * `object-contain` (so it's as large as possible, up- or down-scaled, never
 * distorted), with custom on-theme controls (VideoControls) and click-through
 * overlay subtitles anchored to the *painted* frame (computed by useVideoBox).
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import TokenizedText from "@/shared/components/TokenizedText";
import { hexToRgba } from "@/shared/format/color";
import { useSubtitleSettings } from "@/contexts/SubtitleSettingsContext";
import { cn } from "@/shared/ui";
import { useVideoBox } from "../hooks/useVideoBox";
import { VideoControls } from "@/shared/components/VideoControls";
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
 * @returns {JSX.Element} The video + custom controls + overlay subtitles.
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

    // Controls auto-hide while playing; stay shown while paused.
    const [controlsVisible, setControlsVisible] = useState(true);
    const [paused, setPaused] = useState(true);
    const hideRef = useRef<number | undefined>(undefined);

    useEffect(() => {
        if (!el) return;
        const onPlay = () => setPaused(false);
        const onPause = () => setPaused(true);
        setPaused(el.paused);
        el.addEventListener("play", onPlay);
        el.addEventListener("pause", onPause);
        return () => {
            el.removeEventListener("play", onPlay);
            el.removeEventListener("pause", onPause);
        };
    }, [el]);

    const revealControls = () => {
        setControlsVisible(true);
        if (hideRef.current) window.clearTimeout(hideRef.current);
        hideRef.current = window.setTimeout(() => setControlsVisible(false), 2600);
    };

    const togglePlay = () => {
        if (!el) return;
        if (el.paused) el.play().catch(() => undefined);
        else el.pause();
    };

    const controlsShown = controlsVisible || paused;

    const textStyle: React.CSSProperties = {
        color: subtitleStyle.fontColor,
        fontSize: `${subtitleStyle.fontSize}px`,
        backgroundColor: hexToRgba(subtitleStyle.backgroundColor, subtitleStyle.backgroundOpacity),
        textShadow: subtitleStyle.textShadow,
    };

    // Anchor the overlay to the painted frame when known, else the element box.
    // While the controls are shown, lift the subtitle clear of the control bar
    // (~84px tall) so it never drops onto / gets covered by the controls, even
    // when the user sets a very low subtitle position.
    const lift = controlsShown ? 88 : 0;
    const overlayPos: React.CSSProperties = box
        ? {
              left: box.left,
              width: box.width,
              bottom: box.top + (subtitleStyle.position / 100) * box.height + lift,
              transition: "bottom 200ms ease",
          }
        : {
              left: 0,
              right: 0,
              bottom: `calc(${subtitleStyle.position}% + ${lift}px)`,
              transition: "bottom 200ms ease",
          };

    return (
        <div
            className={cn("relative h-full w-full bg-black", !controlsShown && "cursor-none")}
            onMouseMove={revealControls}
            onMouseLeave={() => !paused && setControlsVisible(false)}
        >
            <video
                id="mirumoji-player"
                ref={setRef}
                src={blobUrl ?? undefined}
                playsInline
                crossOrigin="anonymous"
                onClick={togglePlay}
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

            <VideoControls video={el} visible={controlsShown} />
        </div>
    );
}
