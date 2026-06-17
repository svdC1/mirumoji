/**
 * @packageDocumentation The task tray: a discrete floating dock (bottom-right)
 * that surfaces the active profile's uploads and jobs from the TaskContext. It
 * collapses to a small pill (hidden entirely when there is nothing to show) and
 * expands into a panel with per-task progress, cancel, and dismiss. Reuses the
 * shell's Sumi & Shu surface language so it reads as part of the chrome.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    ArrowRight,
    Ban,
    CheckCircle2,
    ChevronDown,
    Clock,
    ListChecks,
    UploadCloud,
    X,
    XCircle,
} from "lucide-react";
import { usePlayer } from "@/contexts/PlayerContext";
import { useTasks, type UploadTask } from "@/contexts/TaskContext";
import { staticUrl } from "@/shared/format/files";
import type { ConvertResult, Job, JobStatus, SrtResult } from "@/shared/jobs/types";
import { cn, IconButton, Spinner } from "@/shared/ui";

const RESULT_LABELS: Record<string, string> = {
    generate_srt: "Load Subtitles",
    fix_srt: "Load Subtitles",
    convert: "Open Video",
    transcribe: "View Transcript",
};

const TYPE_LABELS: Record<string, string> = {
    generate_srt: "Generate Subtitles",
    transcribe: "Transcribe",
    convert: "Convert To MP4",
    fix_srt: "Fix Subtitles",
};

function typeLabel(type: string): string {
    return TYPE_LABELS[type] ?? type;
}

function isActive(status: JobStatus): boolean {
    return status === "queued" || status === "running";
}

/** A thin determinate progress bar in the Shu accent. */
function ProgressBar({ percent }: { percent: number }) {
    return (
        <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-ink/10">
            <div
                className="h-full rounded-full bg-shu transition-[width] duration-300"
                style={{ width: `${Math.max(0, Math.min(100, percent))}%` }}
            />
        </div>
    );
}

/** A row for a client-side upload that is feeding a job. */
function UploadRow({ task, onDismiss }: { task: UploadTask; onDismiss: () => void }) {
    const failed = task.status === "error";
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
                        {typeLabel(task.jobType)} ·{" "}
                        {failed
                            ? (task.error ?? "Upload Failed")
                            : `Uploading ${Math.round(task.progress)}%`}
                    </p>
                    {!failed && <ProgressBar percent={task.progress} />}
                </div>
                {failed && (
                    <IconButton label="Dismiss" onClick={onDismiss} className="shrink-0">
                        <X size={15} />
                    </IconButton>
                )}
            </div>
        </li>
    );
}

function StatusGlyph({ status }: { status: JobStatus }) {
    if (status === "running") return <Spinner className="h-4 w-4" />;
    if (status === "queued") return <Clock size={16} className="text-ink-muted" />;
    if (status === "succeeded") return <CheckCircle2 size={16} className="text-matcha" />;
    if (status === "failed") return <XCircle size={16} className="text-danger" />;
    return <Ban size={16} className="text-ink-faint" />;
}

function statusText(job: Job): string {
    switch (job.status) {
        case "queued":
            return "Queued";
        case "running":
            return job.total > 1 ? `Running · ${job.completed} / ${job.total}` : "Running";
        case "succeeded":
            return "Done";
        case "failed":
            return job.error ?? "Failed";
        case "cancelled":
            return "Cancelled";
        default:
            return job.status;
    }
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
                        title={job.status === "failed" ? (job.error ?? undefined) : undefined}
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
                            className="mt-2 inline-flex items-center gap-1 rounded-control bg-shu/10 px-2 py-1 text-2xs font-medium text-shu transition-colors hover:bg-shu/20"
                        >
                            {resultLabel}
                            <ArrowRight size={12} />
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
    const { jobs, uploads, busy, cancel, dismiss } = useTasks();
    const player = usePlayer();
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);

    /** Applies a finished job's result (load it into the player / open it). */
    const runResult = (job: Job) => {
        const result = job.result;
        if (!result) return;
        if (job.type === "generate_srt" || job.type === "fix_srt") {
            const srt = result as unknown as SrtResult;
            const file = new File([srt.srt_content], "subtitles.srt", {
                type: "application/x-subrip",
            });
            player.setSrt(file);
            player.setSrtFileName(file.name);
            player.setSrtFileId(srt.srt_file_id);
            navigate("/player");
        } else if (job.type === "convert") {
            const conv = result as unknown as ConvertResult;
            player.setVideoUrl(staticUrl(conv.video_url));
            navigate("/player");
        } else if (job.type === "transcribe") {
            navigate("/dashboard");
        }
        setOpen(false);
    };

    if (jobs.length + uploads.length === 0) return null;

    const activeCount =
        uploads.filter((u) => u.status === "uploading").length +
        jobs.filter((j) => isActive(j.status)).length;

    return (
        <div className="fixed bottom-4 right-4 z-40 print:hidden">
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
                            <UploadRow key={u.id} task={u} onDismiss={() => dismiss(u.id)} />
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
