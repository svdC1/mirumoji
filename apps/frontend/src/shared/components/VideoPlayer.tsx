/**
 * @packageDocumentation A styled, reusable video player: an `object-contain`
 * video on a black stage with the on-theme {@link VideoControls} (auto-hiding
 * while playing). Used wherever a plain video is shown without the subtitle
 * overlay so it matches the player's look instead
 * of the unstyled native `controls`
 */

import { useEffect, useRef, useState } from "react";
import { cn } from "@/shared/ui";
import { VideoControls } from "./VideoControls";

export interface VideoPlayerProps {
    src: string;
    className?: string;
}

/**
 * The VideoPlayer component.
 *
 * @param {VideoPlayerProps} props The video source + optional container classes.
 * @returns {JSX.Element} The styled video player.
 */
export function VideoPlayer({ src, className }: VideoPlayerProps) {
    const [el, setEl] = useState<HTMLVideoElement | null>(null);
    const [controlsVisible, setControlsVisible] = useState(true);
    const [paused, setPaused] = useState(true);
    const hideRef = useRef<number | undefined>(undefined);

    // Mirror the element's play/pause so the controls stay visible while paused.
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

    return (
        <div
            className={cn(
                "relative aspect-video w-full bg-black",
                !controlsShown && "cursor-none",
                className
            )}
            onMouseMove={revealControls}
            onMouseLeave={() => !paused && setControlsVisible(false)}
        >
            <video
                ref={setEl}
                src={src}
                playsInline
                onClick={togglePlay}
                {...{ "webkit-playsinline": "true" }}
                className="h-full w-full object-contain focus:outline-none"
            />
            <VideoControls video={el} visible={controlsShown} />
        </div>
    );
}
