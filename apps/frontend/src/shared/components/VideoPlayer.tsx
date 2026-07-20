/**
 * @packageDocumentation A styled, reusable video player: an `object-contain`
 * video on a black stage with the on-theme {@link VideoControls} (auto-hiding
 * while playing). Used on its own (e.g. clip preview) so a plain video matches
 * the player's look instead of the unstyled native `controls`, and composed by
 * the player feature, which layers its subtitle overlay on top via `overlay`.
 */

import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/shared/ui";
import { VideoControls } from "./VideoControls";

/** How far the arrow keys and the double-tap zones skip, in seconds. */
const SKIP_SECONDS = 5;

/**
 * How long to wait for a second tap before treating the first as a plain click.
 *
 * Roughly the platform double-click threshold: long enough that a real double
 * tap is never split, short enough that play/pause still feels immediate.
 */
const DOUBLE_TAP_MS = 250;

/** Context passed to a {@link VideoPlayerProps.overlay} render function. */
export interface VideoPlayerOverlayContext {
    /** Whether the control bar is currently shown (overlays lift above it). */
    controlsShown: boolean;
}

export interface VideoPlayerProps {
    src: string | null | undefined;
    /** Container (sizing) classes; defaults to a 16:9 box. */
    className?: string;
    /** `id` for the `<video>` (the player uses it to record clips). */
    id?: string;
    /** `crossOrigin` for the `<video>` (needed to record cross-origin media). */
    crossOrigin?: "" | "anonymous" | "use-credentials";
    /** Receives the `<video>` element as it mounts / unmounts. */
    onVideoEl?: (el: HTMLVideoElement | null) => void;
    /** Toggle play/pause on the spacebar (for the primary, on-page player). */
    keyboardControls?: boolean;
    /**
     * Skip 5s by double-tapping the left / right edge of the video.
     *
     * Off by default so a small embedded preview (a clip) keeps a plain
     * click-to-toggle with no tap-detection delay.
     */
    tapToSeek?: boolean;
    /** Renders an overlay above the video (e.g. subtitles). */
    overlay?: (ctx: VideoPlayerOverlayContext) => ReactNode;
}

/**
 * The VideoPlayer component.
 *
 * @param {VideoPlayerProps} props The player props.
 * @returns {JSX.Element} The styled video player.
 */
export function VideoPlayer({
    src,
    className = "aspect-video w-full",
    id,
    crossOrigin,
    onVideoEl,
    keyboardControls = false,
    tapToSeek = false,
    overlay,
}: VideoPlayerProps) {
    const [el, setEl] = useState<HTMLVideoElement | null>(null);
    const setRef = useCallback(
        (node: HTMLVideoElement | null) => {
            setEl(node);
            onVideoEl?.(node);
        },
        [onVideoEl]
    );

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

    // Seeks by `delta` seconds, clamped to the media. Shared by the arrow keys
    // and the double-tap zones so both skip by exactly the same amount.
    const seekBy = useCallback(
        (delta: number) => {
            if (!el) return;
            const duration = Number.isFinite(el.duration) ? el.duration : Infinity;
            el.currentTime = Math.min(Math.max(el.currentTime + delta, 0), duration);
        },
        [el]
    );

    // Keyboard controls for the primary, on-page player: the spacebar toggles
    // play/pause and the arrows skip by 5s. Ignored while typing so they never
    // hijack a form control.
    useEffect(() => {
        if (!el || !keyboardControls) return;
        const onKey = (e: KeyboardEvent) => {
            const target = e.target as HTMLElement | null;
            if (
                target &&
                (target.tagName === "INPUT" ||
                    target.tagName === "TEXTAREA" ||
                    target.tagName === "SELECT" ||
                    target.isContentEditable)
            ) {
                return;
            }
            if (e.code === "Space" || e.key === " ") {
                e.preventDefault();
                if (el.paused) el.play().catch(() => undefined);
                else el.pause();
            } else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                seekBy(e.key === "ArrowRight" ? SKIP_SECONDS : -SKIP_SECONDS);
            }
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [el, keyboardControls, seekBy]);

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

    // A single tap toggles play/pause and a double tap seeks, so the first tap
    // has to wait to find out which it was. Without the delay a double tap
    // would toggle twice on its way to seeking.
    const tapRef = useRef<number | undefined>(undefined);
    useEffect(() => () => window.clearTimeout(tapRef.current), []);

    const onZoneClick = (direction: -1 | 1) => {
        revealControls();
        if (tapRef.current !== undefined) {
            window.clearTimeout(tapRef.current);
            tapRef.current = undefined;
            seekBy(direction * SKIP_SECONDS);
            return;
        }
        tapRef.current = window.setTimeout(() => {
            tapRef.current = undefined;
            togglePlay();
        }, DOUBLE_TAP_MS);
    };

    const controlsShown = controlsVisible || paused;

    return (
        <div
            className={cn("relative bg-black", className, !controlsShown && "cursor-none")}
            onMouseMove={revealControls}
            onMouseLeave={() => !paused && setControlsVisible(false)}
        >
            <video
                id={id}
                ref={setRef}
                src={src ?? undefined}
                playsInline
                crossOrigin={crossOrigin}
                onClick={tapToSeek ? undefined : togglePlay}
                {...{ "webkit-playsinline": "true" }}
                className="h-full w-full object-contain focus:outline-none"
            />
            {tapToSeek && (
                // Sits below the overlay so a subtitle token still takes its own
                // tap, and stops short of the control bar so scrubbing is not
                // swallowed. `touch-action: manipulation` suppresses iOS's
                // double-tap-to-zoom, which would otherwise eat the second tap.
                <div className="absolute inset-x-0 bottom-[88px] top-0 flex touch-manipulation">
                    <button
                        type="button"
                        aria-label={`Back ${SKIP_SECONDS} Seconds`}
                        className="h-full flex-1 cursor-default focus:outline-none"
                        onClick={() => onZoneClick(-1)}
                    />
                    <button
                        type="button"
                        aria-label={`Forward ${SKIP_SECONDS} Seconds`}
                        className="h-full flex-1 cursor-default focus:outline-none"
                        onClick={() => onZoneClick(1)}
                    />
                </div>
            )}
            {overlay?.({ controlsShown })}
            <VideoControls video={el} visible={controlsShown} />
        </div>
    );
}
