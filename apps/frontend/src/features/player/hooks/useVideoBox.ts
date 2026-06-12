/**
 * @packageDocumentation Computes the painted video rectangle inside an
 * `object-contain` video element (the element fills the stage, but the actual
 * frame is letterboxed within it). Used to anchor overlay subtitles to the
 * frame rather than the element box.
 */

import { useEffect, useState } from "react";

export interface VideoBox {
    /** Offset from the element's left edge to the painted frame, in px. */
    left: number;
    /** Offset from the element's top edge to the painted frame, in px. */
    top: number;
    /** Painted frame width, in px. */
    width: number;
    /** Painted frame height, in px. */
    height: number;
}

/**
 * Tracks the painted (contained) video rect, recomputing on metadata load and
 * element resize.
 *
 * @param {HTMLVideoElement | null} video The video element.
 * @returns {VideoBox | null} The painted rect, or `null` until known.
 */
export function useVideoBox(video: HTMLVideoElement | null): VideoBox | null {
    const [box, setBox] = useState<VideoBox | null>(null);

    useEffect(() => {
        if (!video) return;
        const compute = () => {
            const cw = video.clientWidth;
            const ch = video.clientHeight;
            const vw = video.videoWidth;
            const vh = video.videoHeight;
            if (!cw || !ch || !vw || !vh) {
                setBox(null);
                return;
            }
            const ar = vw / vh;
            const car = cw / ch;
            let width: number;
            let height: number;
            if (car > ar) {
                // Element wider than the frame → bars left/right.
                height = ch;
                width = ch * ar;
            } else {
                // Element taller than the frame → bars top/bottom.
                width = cw;
                height = cw / ar;
            }
            setBox({ width, height, left: (cw - width) / 2, top: (ch - height) / 2 });
        };

        compute();
        video.addEventListener("loadedmetadata", compute);
        const ro = new ResizeObserver(compute);
        ro.observe(video);
        return () => {
            video.removeEventListener("loadedmetadata", compute);
            ro.disconnect();
        };
    }, [video]);

    return box;
}
