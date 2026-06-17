/**
 * @packageDocumentation The player's video surface: composes the shared
 * {@link VideoPlayer} and layers click-through overlay subtitles on top,
 * anchored to the *painted* frame (computed by useVideoBox) rather than the
 * element box.
 */

import { type CSSProperties, useCallback, useState } from "react";
import TokenizedText from "@/shared/components/TokenizedText";
import { hexToRgba } from "@/shared/format/color";
import { useSubtitleSettings } from "@/contexts/SubtitleSettingsContext";
import { VideoPlayer } from "@/shared/components/VideoPlayer";
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
 * @returns {JSX.Element} The shared player with overlay subtitles on top.
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
    const handleVideoEl = useCallback(
        (node: HTMLVideoElement | null) => {
            setEl(node);
            onVideoEl(node);
        },
        [onVideoEl]
    );
    const box = useVideoBox(el);

    const textStyle: CSSProperties = {
        color: subtitleStyle.fontColor,
        fontSize: `${subtitleStyle.fontSize}px`,
        backgroundColor: hexToRgba(subtitleStyle.backgroundColor, subtitleStyle.backgroundOpacity),
        textShadow: subtitleStyle.textShadow,
    };

    return (
        <VideoPlayer
            src={blobUrl}
            id="mirumoji-player"
            crossOrigin="anonymous"
            className="h-full w-full"
            onVideoEl={handleVideoEl}
            keyboardControls
            overlay={({ controlsShown }) => {
                // Anchor the overlay to the painted frame when known, else the
                // element box. While the controls are shown, lift the subtitle
                // clear of the control bar (~84px tall) so it never drops onto /
                // gets covered by the controls, even at a very low position.
                const lift = controlsShown ? 88 : 0;
                const overlayPos: CSSProperties = box
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
                    <>
                        {preparing && (
                            <div
                                className="pointer-events-none absolute flex justify-center px-4"
                                style={overlayPos}
                            >
                                <span className="inline-flex items-center gap-2 rounded-control bg-surface/90 px-3 py-1.5 text-xs font-medium text-ink-muted shadow-soft ring-1 ring-ink/10 backdrop-blur">
                                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-shu" />
                                    Loading Subs
                                </span>
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
                    </>
                );
            }}
        />
    );
}
