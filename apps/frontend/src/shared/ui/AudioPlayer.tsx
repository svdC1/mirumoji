/**
 * @packageDocumentation A small, on-theme audio player built on a bare <audio>
 * element — a play/pause control, a scrub bar, and a time readout. Replaces the
 * off-theme react-h5-audio-player.
 */

import React, { useEffect, useRef, useState } from "react";
import { Play, Pause } from "lucide-react";
import { cn } from "./cn";
import { formatClock } from "@/shared/format/time";

export interface AudioPlayerProps {
    src: string;
    className?: string;
}

/**
 * The AudioPlayer component.
 *
 * @param {AudioPlayerProps} props The props.
 * @returns {JSX.Element} The audio player.
 */
export function AudioPlayer({ src, className }: AudioPlayerProps) {
    const ref = useRef<HTMLAudioElement | null>(null);
    const [playing, setPlaying] = useState(false);
    const [current, setCurrent] = useState(0);
    const [duration, setDuration] = useState(0);

    useEffect(() => {
        const a = ref.current;
        if (!a) return;
        const onTime = () => setCurrent(a.currentTime);
        const onMeta = () => setDuration(Number.isFinite(a.duration) ? a.duration : 0);
        const onEnd = () => setPlaying(false);
        const onPlay = () => setPlaying(true);
        const onPause = () => setPlaying(false);
        a.addEventListener("timeupdate", onTime);
        a.addEventListener("loadedmetadata", onMeta);
        a.addEventListener("ended", onEnd);
        a.addEventListener("play", onPlay);
        a.addEventListener("pause", onPause);
        return () => {
            a.removeEventListener("timeupdate", onTime);
            a.removeEventListener("loadedmetadata", onMeta);
            a.removeEventListener("ended", onEnd);
            a.removeEventListener("play", onPlay);
            a.removeEventListener("pause", onPause);
        };
    }, []);

    // Reset when the source changes.
    useEffect(() => {
        setCurrent(0);
        setPlaying(false);
    }, [src]);

    const toggle = () => {
        const a = ref.current;
        if (!a) return;
        if (a.paused) a.play().catch(() => undefined);
        else a.pause();
    };

    const onSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        const a = ref.current;
        if (!a) return;
        const t = Number(e.target.value);
        a.currentTime = t;
        setCurrent(t);
    };

    const pct = duration ? (current / duration) * 100 : 0;

    return (
        <div
            className={cn(
                "flex items-center gap-3 rounded-control border border-ink/10 bg-surface-2 px-3 py-2",
                className
            )}
        >
            <audio ref={ref} src={src} preload="metadata" />
            <button
                type="button"
                onClick={toggle}
                aria-label={playing ? "Pause" : "Play"}
                className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-shu text-ink transition-colors hover:bg-shu-soft"
            >
                {playing ? <Pause size={16} /> : <Play size={16} className="translate-x-px" />}
            </button>
            <input
                type="range"
                min={0}
                max={duration || 0}
                step="0.01"
                value={current}
                onChange={onSeek}
                aria-label="Seek"
                className="h-1 flex-1 cursor-pointer appearance-none rounded-full outline-none"
                style={{
                    background: `linear-gradient(to right, rgb(var(--shu)) ${pct}%, rgb(var(--ink) / 0.15) ${pct}%)`,
                }}
            />
            <span className="shrink-0 text-2xs tabular-nums text-ink-faint">
                {formatClock(current)} / {formatClock(duration)}
            </span>
        </div>
    );
}
