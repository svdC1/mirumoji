import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "./cn";

export interface TooltipProps {
    /**
     * The bubble content. A string renders as a light hover/tap tooltip; rich
     * content (any element) renders as a click-to-open popover, so a longer
     * explanation stays put while it is read.
     */
    label: React.ReactNode;
    /** The trigger the bubble is anchored to. */
    children: React.ReactNode;
    /** Extra classes for the inline trigger wrapper. */
    className?: string;
    /** Widen a string bubble for sentence-length text. */
    wide?: boolean;
}

/**
 * A tooltip / info popover that renders into a portal and positions itself from
 * the trigger's rect, clamped into the viewport. Portalling escapes `overflow`
 * clipping, and the clamp keeps it on-screen on mobile (fixing the old CSS
 * bubble that bled off small screens or was swallowed by a scroll container).
 *
 * @param {TooltipProps} props The bubble content, trigger, and options.
 * @returns {JSX.Element} The trigger with its portalled bubble.
 */
export function Tooltip({ label, children, className, wide }: TooltipProps) {
    const rich = typeof label !== "string";
    const [open, setOpen] = useState(false);
    const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);
    const triggerRef = useRef<HTMLSpanElement>(null);
    const panelRef = useRef<HTMLDivElement>(null);

    // Position from the trigger's rect once the panel is measured, clamped so
    // it never leaves the viewport. Flips above the trigger when there is no
    // room below.
    useLayoutEffect(() => {
        if (!open) {
            setCoords(null);
            return;
        }
        const t = triggerRef.current?.getBoundingClientRect();
        const p = panelRef.current?.getBoundingClientRect();
        if (!t || !p) return;
        const margin = 8;
        let left = t.left + t.width / 2 - p.width / 2;
        left = Math.max(margin, Math.min(left, window.innerWidth - p.width - margin));
        let top = t.bottom + 6;
        if (top + p.height > window.innerHeight - margin) top = t.top - p.height - 6;
        top = Math.max(margin, top);
        setCoords({ top, left });
    }, [open]);

    // Dismiss on outside pointer, Escape, or scroll.
    useEffect(() => {
        if (!open) return;
        const onDown = (e: MouseEvent) => {
            const target = e.target as Node;
            if (!triggerRef.current?.contains(target) && !panelRef.current?.contains(target)) {
                setOpen(false);
            }
        };
        const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
        const onScroll = () => setOpen(false);
        document.addEventListener("mousedown", onDown);
        document.addEventListener("keydown", onKey);
        window.addEventListener("scroll", onScroll, true);
        return () => {
            document.removeEventListener("mousedown", onDown);
            document.removeEventListener("keydown", onKey);
            window.removeEventListener("scroll", onScroll, true);
        };
    }, [open]);

    // A string bubble follows hover / focus; a rich one is pinned by a click so
    // it can be read without hovering it.
    const triggerProps = rich
        ? { onClick: () => setOpen((v) => !v) }
        : {
              onMouseEnter: () => setOpen(true),
              onMouseLeave: () => setOpen(false),
              onFocus: () => setOpen(true),
              onBlur: () => setOpen(false),
          };

    return (
        <span ref={triggerRef} className={cn("inline-flex", className)} {...triggerProps}>
            {children}
            {open &&
                createPortal(
                    <div
                        ref={panelRef}
                        role="tooltip"
                        style={
                            coords
                                ? { position: "fixed", top: coords.top, left: coords.left }
                                : { position: "fixed", top: 0, left: 0, visibility: "hidden" }
                        }
                        className={cn(
                            "z-[60] rounded-card border border-ink/10 bg-surface text-ink-muted shadow-lift",
                            rich
                                ? "max-w-[min(24rem,calc(100vw-1rem))] p-3"
                                : cn(
                                      "pointer-events-none px-2.5 py-1.5 text-xs",
                                      wide
                                          ? "max-w-[min(18rem,calc(100vw-1rem))]"
                                          : "max-w-[min(14rem,calc(100vw-1rem))]"
                                  )
                        )}
                    >
                        {label}
                    </div>,
                    document.body
                )}
        </span>
    );
}

/**
 * A small "?" trigger that reveals `content` in a {@link Tooltip}. Replaces the
 * per-panel info-dot copies. A string shows on hover / tap; rich content opens
 * a click popover.
 *
 * @param {{ content: React.ReactNode; wide?: boolean; className?: string }} props
 *   The bubble content and options.
 * @returns {JSX.Element} The info dot.
 */
export function InfoTip({
    content,
    wide,
    className,
}: {
    content: React.ReactNode;
    wide?: boolean;
    className?: string;
}) {
    return (
        <Tooltip label={content} wide={wide} className={className}>
            <button
                type="button"
                aria-label="More information"
                className="grid h-4 w-4 place-items-center rounded-full border border-ink/30 text-2xs leading-none text-ink-faint transition-colors hover:border-shu/60 hover:text-shu"
            >
                ?
            </button>
        </Tooltip>
    );
}
