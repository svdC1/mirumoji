/**
 * @packageDocumentation Tracks the active subtitle cue from a video element's
 * playback time. Binds to the element value (callback-ref) so the listener
 * attaches exactly when it mounts, and drives updates from a requestAnimationFrame
 * loop while playing — `timeupdate` alone fires sparsely and can stall, which
 * froze the subtitle on a cue. `setActiveIdx` bails out when unchanged, so the
 * rAF loop costs nothing until the cue actually changes.
 */

import { useEffect, useRef, useState } from "react";
import type { Cue } from "../types";

/**
 * Returns the index of the cue under the video's current time (or `null`).
 *
 * @param {HTMLVideoElement | null} video The video element (from a callback ref).
 * @param {Cue[]} cues The parsed cues.
 * @returns {number | null} The active cue index, or `null`.
 */
export function useActiveCue(video: HTMLVideoElement | null, cues: Cue[]): number | null {
    const [activeIdx, setActiveIdx] = useState<number | null>(null);
    const cuesRef = useRef(cues);
    cuesRef.current = cues;

    useEffect(() => {
        if (!video) return;
        let raf = 0;

        const update = () => {
            const t = video.currentTime;
            const cs = cuesRef.current;
            // Last match wins, so overlapping cues resolve to the latest one.
            let found = -1;
            for (let i = 0; i < cs.length; i++) {
                if (t >= cs[i].start && t <= cs[i].end) found = i;
            }
            setActiveIdx(found === -1 ? null : found);
        };

        const loop = () => {
            update();
            raf = requestAnimationFrame(loop);
        };
        const start = () => {
            if (!raf) raf = requestAnimationFrame(loop);
        };
        const stop = () => {
            if (raf) {
                cancelAnimationFrame(raf);
                raf = 0;
            }
            update();
        };

        update();
        video.addEventListener("play", start);
        video.addEventListener("playing", start);
        video.addEventListener("pause", stop);
        video.addEventListener("ended", stop);
        video.addEventListener("seeked", update);
        video.addEventListener("timeupdate", update);
        if (!video.paused) start();

        return () => {
            if (raf) cancelAnimationFrame(raf);
            video.removeEventListener("play", start);
            video.removeEventListener("playing", start);
            video.removeEventListener("pause", stop);
            video.removeEventListener("ended", stop);
            video.removeEventListener("seeked", update);
            video.removeEventListener("timeupdate", update);
        };
    }, [video]);

    return activeIdx;
}
