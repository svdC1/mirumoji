/**
 * @packageDocumentation Small presentational job pieces shared by the task tray
 * and the dashboard Tasks tab: the status glyph and the determinate progress
 * bar.
 */

import { Ban, CheckCircle2, Clock, XCircle } from "lucide-react";
import { Spinner } from "@/shared/ui";
import type { JobStatus } from "./types";

/** The glyph for a job status. */
export function StatusGlyph({ status }: { status: JobStatus }) {
    if (status === "running") return <Spinner className="h-4 w-4" />;
    if (status === "queued") return <Clock size={16} className="text-ink-muted" />;
    if (status === "succeeded") return <CheckCircle2 size={16} className="text-matcha" />;
    if (status === "failed") return <XCircle size={16} className="text-danger" />;
    return <Ban size={16} className="text-ink-faint" />;
}

/** A thin determinate progress bar in the Shu accent. */
export function ProgressBar({ percent }: { percent: number }) {
    return (
        <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-ink/10">
            <div
                className="h-full rounded-full bg-shu transition-[width] duration-300"
                style={{ width: `${Math.max(0, Math.min(100, percent))}%` }}
            />
        </div>
    );
}
