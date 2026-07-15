/**
 * @packageDocumentation Custom, on-theme video controls (the native ones can't
 * be themed cross-browser). Renders over the bottom of the video: scrub bar,
 * play/pause, volume, time, and playback speed. No fullscreen -> native
 * fullscreen would drop the overlay subtitles. Reads/writes the <video> element
 * directly and mirrors its events into local state.
 */

import { useEffect, useState } from "react";
import { Play, Pause, Volume2, VolumeX } from "lucide-react";
import { formatClock } from "@/shared/format/time";
import { cn } from "@/shared/ui";
import { isIOS } from "@/shared/platform";

const RATES = [0.5, 0.75, 1, 1.25, 1.5, 2];

// iOS Safari makes HTMLMediaElement.volume read-only (hardware buttons own it),
// so the volume slider is a dead control there. Hide it and keep the mute
// toggle, which video.muted still honors. Constant per session, so read once.
const IS_IOS = isIOS();

export interface VideoControlsProps {
    video: HTMLVideoElement | null;
    /** Whether the bar is shown (parent handles auto-hide). */
    visible: boolean;
}

/**
 * The VideoControls component.
 *
 * @param {VideoControlsProps} props The props.
 * @returns {JSX.Element | null} The control bar, or `null` without a video.
 */
export function VideoControls({ video, visible }: VideoControlsProps) {
    const [playing, setPlaying] = useState(false);
    const [current, setCurrent] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [muted, setMuted] = useState(false);
    const [rate, setRate] = useState(1);

    useEffect(() => {
        if (!video) return;
        const onTime = () => setCurrent(video.currentTime);
        const onMeta = () => setDuration(Number.isFinite(video.duration) ? video.duration : 0);
        const onPlay = () => setPlaying(true);
        const onPause = () => setPlaying(false);
        const onVol = () => {
            setVolume(video.volume);
            setMuted(video.muted);
        };
        const onRate = () => setRate(video.playbackRate);

        // Sync initial state.
        onMeta();
        onVol();
        onRate();
        setCurrent(video.currentTime);
        setPlaying(!video.paused);

        video.addEventListener("timeupdate", onTime);
        video.addEventListener("loadedmetadata", onMeta);
        video.addEventListener("play", onPlay);
        video.addEventListener("pause", onPause);
        video.addEventListener("volumechange", onVol);
        video.addEventListener("ratechange", onRate);
        return () => {
            video.removeEventListener("timeupdate", onTime);
            video.removeEventListener("loadedmetadata", onMeta);
            video.removeEventListener("play", onPlay);
            video.removeEventListener("pause", onPause);
            video.removeEventListener("volumechange", onVol);
            video.removeEventListener("ratechange", onRate);
        };
    }, [video]);

    if (!video) return null;

    const seekPct = duration ? (current / duration) * 100 : 0;
    const volPct = (muted ? 0 : volume) * 100;
    const rangeBase =
        "h-1 cursor-pointer appearance-none rounded-full outline-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-shu";

    return (
        <div
            // Absorb clicks when visible (so clicking the bar doesn't toggle the
            // video). Pass them through to the video when hidden.
            onClick={(e) => e.stopPropagation()}
            className={cn(
                "absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/85 via-black/40 to-transparent px-3 pb-2.5 pt-8 transition-opacity duration-200",
                visible ? "opacity-100" : "pointer-events-none opacity-0"
            )}
        >
            <div>
                <input
                    type="range"
                    min={0}
                    max={duration || 0}
                    step="0.01"
                    value={current}
                    onChange={(e) => {
                        video.currentTime = Number(e.target.value);
                        setCurrent(Number(e.target.value));
                    }}
                    aria-label="Seek"
                    className={cn(rangeBase, "w-full")}
                    style={{
                        background: `linear-gradient(to right, rgb(var(--shu)) ${seekPct}%, rgb(var(--ink) / 0.25) ${seekPct}%)`,
                    }}
                />

                <div className="mt-2 flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() =>
                            video.paused ? video.play().catch(() => undefined) : video.pause()
                        }
                        aria-label={playing ? "Pause" : "Play"}
                        className="text-ink transition-colors hover:text-shu"
                    >
                        {playing ? <Pause size={20} /> : <Play size={20} />}
                    </button>

                    <button
                        type="button"
                        onClick={() => (video.muted = !video.muted)}
                        aria-label={muted ? "Unmute" : "Mute"}
                        className="text-ink transition-colors hover:text-shu"
                    >
                        {muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
                    </button>
                    {!IS_IOS && (
                        <input
                            type="range"
                            min={0}
                            max={1}
                            step="0.05"
                            value={muted ? 0 : volume}
                            onChange={(e) => {
                                video.muted = false;
                                video.volume = Number(e.target.value);
                            }}
                            aria-label="Volume"
                            className={cn(rangeBase, "w-20")}
                            style={{
                                background: `linear-gradient(to right, rgb(var(--ink)) ${volPct}%, rgb(var(--ink) / 0.25) ${volPct}%)`,
                            }}
                        />
                    )}

                    <span className="text-xs tabular-nums text-ink-muted">
                        {formatClock(current)} / {formatClock(duration)}
                    </span>

                    <select
                        value={rate}
                        onChange={(e) => (video.playbackRate = Number(e.target.value))}
                        aria-label="Playback speed"
                        className="ml-auto cursor-pointer rounded-control border border-ink/15 bg-black/40 px-2 py-1 text-xs text-ink outline-none"
                    >
                        {RATES.map((r) => (
                            <option key={r} value={r} className="bg-surface text-ink">
                                {r}×
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
}
