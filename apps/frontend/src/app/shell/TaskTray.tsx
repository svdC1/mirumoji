/**
 * @packageDocumentation The task tray: a discrete floating dock (bottom-right)
 * that surfaces the active profile's uploads and jobs from the TaskContext. It
 * collapses to a small pill (hidden entirely when there is nothing to show) and
 * expands into a panel with per-task progress, cancel, and dismiss. Reuses the
 * shell's Sumi & Shu surface language so it reads as part of the chrome.
 */

import { useEffect, useRef, useState } from "react";
import { ArrowRight, ChevronDown, ListChecks, UploadCloud, X, XCircle } from "lucide-react";
import { useTasks, type UploadTask } from "@/contexts/TaskContext";
import { isActive, RESULT_LABELS, statusText, typeLabel } from "@/shared/jobs/labels";
import { ProgressBar, StatusGlyph } from "@/shared/jobs/JobBits";
import { useJobResult } from "@/shared/jobs/useJobResult";
import type { Job } from "@/shared/jobs/types";
import { cn, IconButton, Spinner } from "@/shared/ui";

/** A row for a client-side upload that is feeding a job. */
function UploadRow({
    task,
    onCancel,
    onDismiss,
}: {
    task: UploadTask;
    onCancel: () => void;
    onDismiss: () => void;
}) {
    const failed = task.status === "error";
    const cancellable = !failed && task.cancellable === true;
    return (
        <li className="px-3 py-2.5">
            <div className="flex items-start gap-2.5">
                <span className="mt-0.5 shrink-0 text-ink-muted">
                    {failed ? (
                        <XCircle size={16} className="text-danger" />
                    ) : (
                        <UploadCloud size={16} />
                    )}
                </span>
                <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink" title={task.name}>
                        {task.name}
                    </p>
                    <p className="text-2xs text-ink-muted">
                        {task.jobType ? typeLabel(task.jobType) : "Upload"} ·{" "}
                        {failed
                            ? (task.error ?? "Upload Failed")
                            : `Uploading ${Math.round(task.progress)}%`}
                    </p>
                    {!failed && <ProgressBar percent={task.progress} />}
                </div>
                {(failed || cancellable) && (
                    <IconButton
                        label={cancellable ? "Cancel" : "Dismiss"}
                        onClick={cancellable ? onCancel : onDismiss}
                        className="shrink-0"
                    >
                        <X size={15} />
                    </IconButton>
                )}
            </div>
        </li>
    );
}

/** A row for a server-side job. */
function JobRow({
    job,
    onCancel,
    onDismiss,
    onResult,
}: {
    job: Job;
    onCancel: () => void;
    onDismiss: () => void;
    onResult?: () => void;
}) {
    const active = isActive(job.status);
    const resultLabel = job.status === "succeeded" ? RESULT_LABELS[job.type] : undefined;
    return (
        <li className="px-3 py-2.5">
            <div className="flex items-start gap-2.5">
                <span className="mt-0.5 shrink-0">
                    <StatusGlyph status={job.status} />
                </span>
                <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{typeLabel(job.type)}</p>
                    <p
                        className={cn(
                            "truncate text-2xs",
                            job.status === "failed" ? "text-danger" : "text-ink-muted"
                        )}
                    >
                        {statusText(job)}
                    </p>
                    {job.status === "running" && job.total > 1 && (
                        <ProgressBar percent={(job.completed / job.total) * 100} />
                    )}
                    {resultLabel && onResult && (
                        <button
                            type="button"
                            onClick={onResult}
                            className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-control bg-shu/10 px-3 py-1.5 text-xs font-medium text-shu transition-colors hover:bg-shu/20"
                        >
                            {resultLabel}
                            <ArrowRight size={13} />
                        </button>
                    )}
                </div>
                <IconButton
                    label={active ? "Cancel" : "Dismiss"}
                    onClick={active ? onCancel : onDismiss}
                    className="shrink-0"
                >
                    <X size={15} />
                </IconButton>
            </div>
        </li>
    );
}

/**
 * The TaskTray component.
 *
 * @returns {JSX.Element | null} The floating tray, or `null` when idle/empty.
 */
export function TaskTray() {
    const { jobs, uploads, busy, cancel, cancelUpload, dismiss } = useTasks();
    const applyResult = useJobResult();
    const [open, setOpen] = useState(false);

    // Pop the tray open when a new upload starts (player or Files tab), so its
    // progress surfaces instead of hiding in the collapsed pill. Only a brand
    // new upload id triggers it, so progress ticks don't fight a manual
    // collapse.
    const seenUploads = useRef<Set<string>>(new Set());
    useEffect(() => {
        const isNew = uploads.some((u) => !seenUploads.current.has(u.id));
        seenUploads.current = new Set(uploads.map((u) => u.id));
        if (isNew) setOpen(true);
    }, [uploads]);

    /** Applies a finished job's result, then collapses the tray. */
    const runResult = (job: Job) => {
        applyResult(job);
        setOpen(false);
    };

    if (jobs.length + uploads.length === 0) return null;

    const activeCount =
        uploads.filter((u) => u.status === "uploading").length +
        jobs.filter((j) => isActive(j.status)).length;

    return (
        <div className="fixed bottom-[calc(1rem_+_var(--sab))] right-[calc(1rem_+_var(--sar))] z-40 print:hidden">
            {open ? (
                <div className="flex max-h-[60vh] w-[min(20rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-card bg-surface shadow-lift ring-1 ring-ink/10 backdrop-blur">
                    <header className="flex items-center justify-between border-b border-ink/10 px-3 py-2">
                        <div className="flex items-center gap-2">
                            {busy ? (
                                <Spinner className="h-4 w-4" />
                            ) : (
                                <ListChecks size={16} className="text-ink-muted" />
                            )}
                            <span className="font-display text-sm text-ink">Tasks</span>
                        </div>
                        <IconButton label="Collapse" onClick={() => setOpen(false)}>
                            <ChevronDown size={16} />
                        </IconButton>
                    </header>
                    <ul className="min-h-0 flex-1 divide-y divide-ink/5 overflow-y-auto">
                        {uploads.map((u) => (
                            <UploadRow
                                key={u.id}
                                task={u}
                                onCancel={() => cancelUpload(u.id)}
                                onDismiss={() => dismiss(u.id)}
                            />
                        ))}
                        {jobs.map((j) => (
                            <JobRow
                                key={j.id}
                                job={j}
                                onCancel={() => cancel(j.id)}
                                onDismiss={() => dismiss(j.id)}
                                onResult={() => runResult(j)}
                            />
                        ))}
                    </ul>
                </div>
            ) : (
                <button
                    type="button"
                    onClick={() => setOpen(true)}
                    className="inline-flex items-center gap-2 rounded-full bg-surface px-3.5 py-2 text-sm font-medium text-ink shadow-lift ring-1 ring-ink/10 backdrop-blur transition-colors hover:bg-ink/5"
                >
                    {busy ? (
                        <Spinner className="h-4 w-4" />
                    ) : (
                        <ListChecks size={16} className="text-shu" />
                    )}
                    <span>Tasks</span>
                    <span className="grid h-5 min-w-5 place-items-center rounded-full bg-shu/15 px-1 text-2xs font-semibold text-shu">
                        {busy ? activeCount : jobs.length + uploads.length}
                    </span>
                </button>
            )}
        </div>
    );
}
