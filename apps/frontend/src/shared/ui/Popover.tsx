import React, { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "./cn";

export interface PopoverProps {
    open: boolean;
    onClose: () => void;
    children: React.ReactNode;
    className?: string;
    align?: "left" | "right";
}

/**
 * A panel anchored to its parent (which must be `position: relative`). Closes
 * on outside click or Escape. Pair with a trigger button inside the same
 * relative wrapper.
 */
export function Popover({ open, onClose, children, className, align = "left" }: PopoverProps) {
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;
        const onDoc = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) onClose();
        };
        const onEsc = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };
        document.addEventListener("mousedown", onDoc);
        document.addEventListener("keydown", onEsc);
        return () => {
            document.removeEventListener("mousedown", onDoc);
            document.removeEventListener("keydown", onEsc);
        };
    }, [open, onClose]);

    return (
        <AnimatePresence>
            {open && (
                <motion.div
                    ref={ref}
                    initial={{ opacity: 0, y: -4, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.98 }}
                    transition={{ duration: 0.12 }}
                    className={cn(
                        // `max-w` keeps the panel within the viewport on small
                        // screens so it can never push the page horizontally.
                        "absolute z-50 mt-2 max-w-[calc(100vw-1rem)] rounded-card border border-ink/10 bg-surface shadow-lift",
                        align === "right" ? "right-0" : "left-0",
                        className
                    )}
                >
                    {children}
                </motion.div>
            )}
        </AnimatePresence>
    );
}
