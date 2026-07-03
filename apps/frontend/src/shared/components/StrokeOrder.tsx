/**
 * @packageDocumentation Draws a kanji stroke by stroke from its KanjiVG
 * diagram (fetched as an inline SVG). Each stroke path is revealed by
 * animating its dash offset in stroke order. Honors reduced motion by
 * rendering the finished diagram statically, and falls back to the plain
 * glyph when no stroke data exists.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Pause, Play, StepForward } from "lucide-react";
import { apiKanjiStrokes } from "@/shared/dict/api";
import { cn } from "@/shared/ui";

/** In-memory SVG cache so re-opened kanji never refetch. */
const svgCache = new Map<string, Promise<string | null>>();

function fetchStrokes(literal: string): Promise<string | null> {
    let cached = svgCache.get(literal);
    if (!cached) {
        cached = apiKanjiStrokes(literal).catch(() => null);
        svgCache.set(literal, cached);
    }
    return cached;
}

/**
 * A kanji rendered as an SVG glyph that scales to fill its container, used
 * when no stroke-order data exists so the literal never renders tiny inside a
 * large diagram slot.
 *
 * @param {{ literal: string; className?: string }} props The glyph + sizing.
 * @returns {JSX.Element} The scalable glyph.
 */
export function KanjiGlyph({ literal, className }: { literal: string; className?: string }) {
    return (
        <div className={cn("grid place-items-center", className)}>
            <svg viewBox="0 0 109 109" width="100%" height="100%" role="img" aria-label={literal}>
                <text
                    x="50%"
                    y="50%"
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize="88"
                    fill="currentColor"
                    lang="ja"
                    className="font-jp"
                >
                    {literal}
                </text>
            </svg>
        </div>
    );
}

/** The available playback speeds, cycled by the speed control. */
const SPEEDS = [1, 1.5, 2] as const;

/** Per-stroke reveal duration from its path length, in ms at 1x speed. */
function strokeDuration(length: number): number {
    return Math.min(900, Math.max(250, length * 8));
}

export interface StrokeOrderProps {
    /** The kanji to draw. */
    literal: string;
    /** Show replay / step / speed controls (the hub's kanji view). */
    controls?: boolean;
    /** Replay when the diagram itself is clicked (compact surfaces). */
    replayOnClick?: boolean;
    /** Reveal the stroke-number markers once drawing settles. */
    numbers?: boolean;
    /** Wrapper sizing classes (the SVG fills it). */
    className?: string;
}

/**
 * The StrokeOrder component.
 *
 * @param {StrokeOrderProps} props The props.
 * @returns {JSX.Element} The animated stroke-order diagram.
 */
export default function StrokeOrder({
    literal,
    controls = false,
    replayOnClick = false,
    numbers = true,
    className,
}: StrokeOrderProps) {
    const [svg, setSvg] = useState<string | null | undefined>(undefined);
    const [playing, setPlaying] = useState(false);
    const [speedIdx, setSpeedIdx] = useState(0);
    const hostRef = useRef<HTMLDivElement>(null);
    const timerRef = useRef<number | null>(null);
    const strokeRef = useRef(0);

    const reducedMotion =
        typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    useEffect(() => {
        let cancelled = false;
        setSvg(undefined);
        fetchStrokes(literal).then((markup) => !cancelled && setSvg(markup));
        return () => {
            cancelled = true;
        };
    }, [literal]);

    const paths = useCallback((): SVGPathElement[] => {
        return Array.from(hostRef.current?.querySelectorAll("path") ?? []);
    }, []);

    const stopTimer = useCallback(() => {
        if (timerRef.current !== null) {
            window.clearTimeout(timerRef.current);
            timerRef.current = null;
        }
    }, []);

    const setNumbersVisible = useCallback(
        (visible: boolean) => {
            const texts = hostRef.current?.querySelectorAll("text") ?? [];
            texts.forEach((t) => {
                (t as SVGTextElement).style.opacity = visible && numbers ? "0.45" : "0";
            });
        },
        [numbers]
    );

    /** Instantly show the finished diagram (static / reduced-motion state). */
    const settle = useCallback(() => {
        stopTimer();
        setPlaying(false);
        paths().forEach((p) => {
            p.style.transition = "none";
            p.style.strokeDasharray = "";
            p.style.strokeDashoffset = "";
        });
        strokeRef.current = paths().length;
        setNumbersVisible(true);
    }, [paths, setNumbersVisible, stopTimer]);

    /** Hide every stroke so a fresh drawing can start. */
    const resetStrokes = useCallback(() => {
        stopTimer();
        strokeRef.current = 0;
        setNumbersVisible(false);
        paths().forEach((p) => {
            const len = p.getTotalLength();
            p.style.transition = "none";
            p.style.strokeDasharray = String(len);
            p.style.strokeDashoffset = String(len);
        });
    }, [paths, setNumbersVisible, stopTimer]);

    /** Reveal one stroke, optionally chaining the next while playing. */
    const revealNext = useCallback(
        (chain: boolean) => {
            const all = paths();
            const i = strokeRef.current;
            if (i >= all.length) {
                setPlaying(false);
                setNumbersVisible(true);
                return;
            }
            const p = all[i];
            const len = p.getTotalLength();
            const dur = strokeDuration(len) / SPEEDS[speedIdx];
            p.style.transition = `stroke-dashoffset ${dur}ms linear`;
            p.style.strokeDashoffset = "0";
            strokeRef.current = i + 1;
            if (chain) {
                timerRef.current = window.setTimeout(() => {
                    if (strokeRef.current >= all.length) {
                        setPlaying(false);
                        setNumbersVisible(true);
                        return;
                    }
                    revealNext(true);
                }, dur + 80);
            } else if (strokeRef.current >= all.length) {
                setNumbersVisible(true);
            }
        },
        [paths, setNumbersVisible, speedIdx]
    );

    const play = useCallback(() => {
        resetStrokes();
        setPlaying(true);
        // Give the reset styles a frame to apply before transitioning
        window.requestAnimationFrame(() => window.requestAnimationFrame(() => revealNext(true)));
    }, [resetStrokes, revealNext]);

    // Parse, sanitize, and inject the SVG (sizing + theme color), then draw
    // or settle. The markup is first-party (KanjiVG baked into the server's
    // database), but scripts, foreignObject, and event handlers are stripped
    // anyway as defense in depth.
    useEffect(() => {
        const host = hostRef.current;
        if (!svg || !host) return;
        const doc = new DOMParser().parseFromString(svg, "image/svg+xml");
        const root = doc.documentElement;
        if (root.nodeName.toLowerCase() !== "svg") return;
        root.querySelectorAll("script, foreignObject").forEach((el) => el.remove());
        root.querySelectorAll("*").forEach((el) => {
            Array.from(el.attributes).forEach((attr) => {
                if (attr.name.toLowerCase().startsWith("on")) {
                    el.removeAttribute(attr.name);
                }
            });
        });
        root.setAttribute("width", "100%");
        root.setAttribute("height", "100%");
        host.replaceChildren(root);
        paths().forEach((p) => {
            p.style.stroke = "currentColor";
        });
        host.querySelectorAll("text").forEach((t) => {
            (t as SVGTextElement).style.fill = "currentColor";
        });
        if (reducedMotion) {
            settle();
        } else {
            play();
        }
        return () => {
            stopTimer();
            host.replaceChildren();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [svg]);

    if (svg === undefined) {
        return <div className={cn("animate-pulse rounded-control bg-ink/5", className)} />;
    }

    // No stroke data: fall back to the plain glyph at the same size
    if (svg === null) {
        return <KanjiGlyph literal={literal} className={cn("text-ink", className)} />;
    }

    return (
        <div className={cn("flex flex-col items-center gap-1.5", className)}>
            <div
                ref={hostRef}
                aria-label={
                    replayOnClick
                        ? `Replay stroke order for ${literal}`
                        : `Stroke order for ${literal}`
                }
                role={replayOnClick ? "button" : "img"}
                tabIndex={replayOnClick ? 0 : undefined}
                title={replayOnClick ? "Replay Strokes" : undefined}
                onClick={replayOnClick ? () => !playing && play() : undefined}
                onKeyDown={
                    replayOnClick
                        ? (e) => {
                              if ((e.key === "Enter" || e.key === " ") && !playing) {
                                  e.preventDefault();
                                  play();
                              }
                          }
                        : undefined
                }
                className={cn(
                    "min-h-0 w-full flex-1 text-ink",
                    replayOnClick &&
                        "cursor-pointer rounded-control transition-colors hover:bg-ink/5 focus:outline-none focus-visible:bg-ink/5"
                )}
            />
            {/* Reduced motion only disables the automatic drawing on load;
                these controls are user-initiated, so they always show */}
            {controls && (
                <div className="flex items-center gap-1">
                    <button
                        type="button"
                        onClick={playing ? settle : play}
                        aria-label={playing ? "Skip to finished diagram" : "Replay strokes"}
                        title={playing ? "Skip" : "Replay"}
                        className="rounded-control p-1.5 text-ink-muted transition-colors hover:bg-ink/5 hover:text-ink"
                    >
                        {playing ? <Pause size={15} /> : <Play size={15} />}
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            if (playing) return;
                            if (strokeRef.current >= paths().length) resetStrokes();
                            revealNext(false);
                        }}
                        disabled={playing}
                        aria-label="Draw next stroke"
                        title="Next Stroke"
                        className="rounded-control p-1.5 text-ink-muted transition-colors hover:bg-ink/5 hover:text-ink disabled:opacity-40"
                    >
                        <StepForward size={15} />
                    </button>
                    <button
                        type="button"
                        onClick={() => setSpeedIdx((i) => (i + 1) % SPEEDS.length)}
                        aria-label="Cycle playback speed"
                        title="Speed"
                        className="rounded-control px-1.5 py-1 text-2xs font-semibold text-ink-muted transition-colors hover:bg-ink/5 hover:text-ink"
                    >
                        {SPEEDS[speedIdx]}x
                    </button>
                </div>
            )}
        </div>
    );
}
