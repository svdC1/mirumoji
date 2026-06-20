/**
 * @packageDocumentation The Tasks tab: the durable record of the profile's jobs.
 * Lists the full job history (server) overlaid with the live task state, expands
 * a batch job to its per-file children, applies a finished result, and deletes
 * tasks. Files are the source of truth, so deleting a file cascades its jobs
 * away server-side rather than leaving stale rows to detect here.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import useSWR, { mutate } from "swr";
import { toast } from "react-hot-toast";
import { ArrowRight, ChevronDown, ChevronRight, Trash2, X } from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";
import { useTasks } from "@/contexts/TaskContext";
import { listJobChildren, listJobs } from "@/shared/jobs/api";
import { isActive, RESULT_LABELS, statusText, typeLabel } from "@/shared/jobs/labels";
import { ProgressBar, StatusGlyph } from "@/shared/jobs/JobBits";
import { useJobResult } from "@/shared/jobs/useJobResult";
import { toastApiError } from "@/shared/api/errors";
import type { Job } from "@/shared/jobs/types";
import { Card, EmptyState, IconButton, cn } from "@/shared/ui";
import { NoProfile, PanelLoading } from "./panelStates";

function byNewest(a: Job, b: Job): number {
    return b.created_at.localeCompare(a.created_at);
}

function isBatch(job: Job): boolean {
    return job.type.startsWith("batch_") || job.total > 1;
}

/** The expandable per-file children of a batch job. */
function BatchChildren({ parent }: { parent: Job }) {
    const { data, isLoading } = useSWR(
        `jobs/${parent.id}/children`,
        () => listJobChildren(parent.id),
        { refreshInterval: isActive(parent.status) ? 2000 : 0 }
    );
    const applyResult = useJobResult();

    if (isLoading && !data) {
        return <p className="px-3 py-2 pl-9 text-2xs text-ink-faint">Loading Files…</p>;
    }
    if (!data || data.length === 0) {
        return <p className="px-3 py-2 pl-9 text-2xs text-ink-faint">No Files</p>;
    }
    return (
        <ul className="divide-y divide-ink/5 border-t border-ink/5 bg-ink/[0.02]">
            {data.map((child, i) => {
                const resultLabel =
                    child.status === "succeeded" ? RESULT_LABELS[child.type] : undefined;
                return (
                    <li key={child.id} className="flex items-center gap-2.5 px-3 py-2 pl-9">
                        <StatusGlyph status={child.status} />
                        <span
                            className={cn(
                                "min-w-0 flex-1 truncate text-2xs",
                                child.status === "failed" ? "text-danger" : "text-ink-muted"
                            )}
                        >
                            <span className="text-ink">File {i + 1}</span> · {statusText(child)}
                        </span>
                        {resultLabel && (
                            <button
                                type="button"
                                onClick={() => applyResult(child)}
                                className="flex shrink-0 items-center gap-1 rounded-control px-2 py-1 text-2xs font-medium text-shu hover:bg-shu/10"
                            >
                                {resultLabel}
                                <ArrowRight size={12} />
                            </button>
                        )}
                    </li>
                );
            })}
        </ul>
    );
}

/** A single job row. A batch row's body toggles its per-file children. */
function JobRow({
    job,
    onCancel,
    onDelete,
    onResult,
}: {
    job: Job;
    onCancel: () => void;
    onDelete: () => void;
    onResult: () => void;
}) {
    const [expanded, setExpanded] = useState(false);
    const active = isActive(job.status);
    const batch = isBatch(job);
    const resultLabel = job.status === "succeeded" && !batch ? RESULT_LABELS[job.type] : undefined;
    const toggle = () => setExpanded((v) => !v);

    const label = (
        <span className="block truncate text-sm font-medium text-ink">{typeLabel(job.type)}</span>
    );
    const status = (
        <span
            className={cn(
                "block truncate text-2xs",
                job.status === "failed" ? "text-danger" : "text-ink-muted"
            )}
        >
            {statusText(job)}
        </span>
    );

    return (
        <Card className="overflow-hidden p-0">
            <div className="p-3">
                <div className="flex items-center gap-3">
                    {batch ? (
                        <button
                            type="button"
                            onClick={toggle}
                            aria-expanded={expanded}
                            className="flex min-w-0 flex-1 items-center gap-3 text-left"
                        >
                            <StatusGlyph status={job.status} />
                            <span className="min-w-0 flex-1">
                                {label}
                                {status}
                            </span>
                        </button>
                    ) : (
                        <div className="flex min-w-0 flex-1 items-center gap-3">
                            <StatusGlyph status={job.status} />
                            <span className="min-w-0 flex-1">
                                {label}
                                {status}
                            </span>
                        </div>
                    )}
                    {resultLabel && (
                        <button
                            type="button"
                            onClick={onResult}
                            className="flex shrink-0 items-center gap-1 rounded-control bg-shu/10 px-2.5 py-1.5 text-xs font-medium text-shu hover:bg-shu/20"
                        >
                            {resultLabel}
                            <ArrowRight size={13} />
                        </button>
                    )}
                    {active ? (
                        <IconButton
                            label="Cancel"
                            size="sm"
                            onClick={onCancel}
                            className="shrink-0"
                        >
                            <X size={15} />
                        </IconButton>
                    ) : (
                        <IconButton
                            label="Delete"
                            size="sm"
                            onClick={onDelete}
                            className="shrink-0 hover:text-danger"
                        >
                            <Trash2 size={15} />
                        </IconButton>
                    )}
                    {batch && (
                        <button
                            type="button"
                            onClick={toggle}
                            className="shrink-0 text-ink-faint hover:text-ink"
                            aria-label={expanded ? "Collapse files" : "Expand files"}
                        >
                            {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                        </button>
                    )}
                </div>
                {active && batch && <ProgressBar percent={(job.completed / job.total) * 100} />}
            </div>
            {batch && expanded && <BatchChildren parent={job} />}
        </Card>
    );
}

/**
 * The TasksPanel component.
 *
 * @returns {JSX.Element} The tasks panel.
 */
export function TasksPanel() {
    const { profileId } = useProfile();
    const { jobs: liveJobs, cancel, deleteJob } = useTasks();
    const applyResult = useJobResult();
    const { data: history, isLoading } = useSWR(
        profileId ? "jobs/history" : null,
        () => listJobs(false),
        { revalidateOnFocus: false, keepPreviousData: true }
    );

    // Full history (server) overlaid with the live task state, so active jobs
    // tick over while past ones stay listed.
    const merged = useMemo(() => {
        const byId = new Map<string, Job>();
        for (const j of history ?? []) byId.set(j.id, j);
        for (const j of liveJobs) byId.set(j.id, j);
        return [...byId.values()].sort(byNewest);
    }, [history, liveJobs]);

    // When a live job finishes, refetch history so a job later dismissed from
    // the tray (dropping it from liveJobs) doesn't fall back to a stale running
    // copy here.
    const prevActive = useRef<Set<string>>(new Set());
    useEffect(() => {
        const active = new Set(liveJobs.filter((j) => isActive(j.status)).map((j) => j.id));
        let finished = false;
        for (const id of prevActive.current) {
            if (!active.has(id)) {
                finished = true;
                break;
            }
        }
        prevActive.current = active;
        if (finished) void mutate("jobs/history");
    }, [liveJobs]);

    const onDelete = async (id: string) => {
        try {
            await deleteJob(id);
            void mutate("jobs/history");
            toast.success("Task Deleted");
        } catch (e) {
            toastApiError(e);
        }
    };

    if (!profileId) return <NoProfile what="view your tasks" />;
    if (isLoading && !history) return <PanelLoading />;
    if (merged.length === 0) {
        return <EmptyState title="No Tasks" description="Jobs You Run Appear Here" />;
    }

    return (
        <div className="space-y-3">
            {merged.map((job) => (
                <JobRow
                    key={job.id}
                    job={job}
                    onCancel={() => cancel(job.id)}
                    onDelete={() => onDelete(job.id)}
                    onResult={() => applyResult(job)}
                />
            ))}
        </div>
    );
}
