/**
 * @packageDocumentation A dismissible ribbon marking the app as the backend-free
 * live demo, so a visitor understands why uploads, search, and edits are limited
 */

import { useState } from "react";
import { X } from "lucide-react";

/** A fixed, dismissible "Demo" pill. */
export function DemoBanner() {
    const [show, setShow] = useState(true);
    if (!show) return null;

    return (
        <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
            <div className="pointer-events-auto flex max-w-[92vw] items-center gap-2.5 rounded-full border border-shu/40 bg-surface/95 py-2 pl-4 pr-2 text-sm text-ink shadow-[0_16px_36px_-14px_rgb(0_0_0/0.75)] backdrop-blur">
                <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-shu" />
                <span className="truncate">
                    <span className="font-semibold text-shu">Limited Demo</span>
                </span>
                <button
                    type="button"
                    onClick={() => setShow(false)}
                    aria-label="Dismiss"
                    className="grid h-6 w-6 shrink-0 place-items-center rounded-full text-ink-faint transition-colors hover:bg-ink/10 hover:text-ink"
                >
                    <X size={14} />
                </button>
            </div>
        </div>
    );
}
