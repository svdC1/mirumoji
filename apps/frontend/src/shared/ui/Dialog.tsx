/**
 * @packageDocumentation Modal overlay rendered in a portal.
 */

import React from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "./cn";

export interface DialogProps {
    open: boolean;
    onClose: () => void;
    children: React.ReactNode;
    className?: string;
    /** Hide the backdrop click-to-close (e.g. destructive confirms). */
    disableBackdropClose?: boolean;
}

/**
 * A centered modal with a blurred backdrop and a spring entrance. For the
 * draggable word lookup we keep a custom implementation. This covers the
 * common confirm/edit modal
 */
export function Dialog({ open, onClose, children, className, disableBackdropClose }: DialogProps) {
    // Portal to <body> so a transformed ancestor (e.g. the sliding sidebar)
    // never becomes the containing block for these fixed-positioned layers.
    return createPortal(
        <AnimatePresence>
            {open && (
                <motion.div
                    className="fixed inset-0 z-50 flex items-center justify-center p-4"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                >
                    <div
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        onClick={disableBackdropClose ? undefined : onClose}
                    />
                    <motion.div
                        role="dialog"
                        aria-modal="true"
                        className={cn(
                            "relative z-10 w-full max-w-lg overflow-hidden rounded-card border border-ink/10 bg-surface shadow-lift",
                            className
                        )}
                        initial={{ scale: 0.96, y: 8, opacity: 0 }}
                        animate={{ scale: 1, y: 0, opacity: 1 }}
                        exit={{ scale: 0.98, opacity: 0 }}
                        transition={{ type: "spring", stiffness: 320, damping: 28 }}
                    >
                        {children}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>,
        document.body
    );
}
