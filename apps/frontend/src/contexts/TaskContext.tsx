/**
 * @packageDocumentation Global task tracking: holds the active profile's jobs
 * (server-side) and in-flight uploads (client-side), polls running jobs, and
 * exposes submit / cancel / dismiss for the task tray and the features that
 * enqueue work. The server is the source of truth, so active jobs survive
 * navigation and reload (re-seeded on mount).
 */

import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
    ReactNode,
} from "react";
import { ApiError, toastApiError } from "@/shared/api/errors";
import { isUploadAborted } from "@/shared/api/client";
import { inferFileType } from "@/shared/format/files";
import { useProfile } from "./ProfileContext";
import {
    cancelJob,
    deleteJob as deleteJobApi,
    getJob,
    listJobs,
    submitBatch as submitBatchApi,
    submitJob,
    uploadProfileFile,
} from "@/shared/jobs/api";
import type {
    BatchSubmitRequest,
    Job,
    JobStatus,
    JobType,
    SubmitJobRequest,
    UploadedFile,
} from "@/shared/jobs/types";

/** How often to re-poll while any job is active. */
const POLL_INTERVAL_MS = 2000;

const ACTIVE_STATUSES: JobStatus[] = ["queued", "running"];

/**
 * Identity key for the upload cache.
 *
 * Keyed by content identity rather than by `File` object identity: re-picking
 * the same file from the OS dialog yields a brand new `File`, which would miss
 * a per-object cache and upload again. It also keeps the cache from retaining a
 * strong reference to every `File` uploaded this session, which pinned
 * multi-hundred-MB blobs in memory for the lifetime of the page.
 *
 * @param {File} file The file to key.
 * @returns {string} A stable key for this file's contents.
 */
function fileKey(file: File): string {
    return `${file.name}|${file.size}|${file.lastModified}`;
}

/** A client-side upload, shown in the tray during its upload. */
export interface UploadTask {
    /** Client-generated id (distinct from server job ids). */
    id: string;
    /** Display name (the uploaded file name, or a folder / file count). */
    name: string;
    /** The job that will be submitted once the upload finishes, if any. */
    jobType?: JobType;
    /** Upload progress in `[0, 100]`. */
    progress: number;
    /** `uploading` while in flight, `error` if the upload failed. */
    status: "uploading" | "error";
    /** Failure message when `status` is `error`. */
    error?: string;
    /** Whether this upload can still be cancelled. */
    cancellable?: boolean;
}

/** Everything a submitted job needs beyond the uploaded file reference. */
export interface SubmitOptions {
    /** The operation to run. */
    jobType: JobType;
    /** Optional file-type tag stored on the uploaded file. */
    fileType?: string;
    /** Operation options (transcription / conversion args). */
    opts?: Record<string, unknown>;
    /** LLM model selector (`fix_srt`). */
    model?: string;
    /** LLM system message (`fix_srt`). */
    sysMsg?: string;
}

export interface TaskContextType {
    jobs: Job[];
    uploads: UploadTask[];
    /** Whether anything is in flight (uploading or an active job). */
    busy: boolean;
    /** Uploads a file then submits a job against it, tracking both phases. */
    uploadAndSubmit: (file: File, options: SubmitOptions) => Promise<Job | null>;
    /** Submits a job against an already-uploaded file. */
    submit: (req: SubmitJobRequest) => Promise<Job | null>;
    /** Submits a batch job over several already-uploaded files. */
    submitBatch: (req: BatchSubmitRequest) => Promise<Job | null>;
    /**
     * Uploads several files into the profile (no job), tracked in the tray as a
     * single aggregate task. Returns how many uploaded successfully.
     */
    uploadFiles: (files: File[], folder?: string) => Promise<number>;
    /** Resolves once the given job reaches a terminal state (polls it). */
    waitFor: (id: string) => Promise<Job>;
    /** Cancels a queued or running job. */
    cancel: (id: string) => Promise<void>;
    /** Aborts an in-flight upload by its tray id. */
    cancelUpload: (id: string) => void;
    /** Permanently deletes a finished job (server-side) and drops it locally. */
    deleteJob: (id: string) => Promise<void>;
    /** Removes a finished job or a failed upload from the tray. */
    dismiss: (id: string) => void;
    /** Forgets the cached profile file ids for the given ids. */
    forgetUploaded: (fileIds: string[]) => void;
    /** Re-fetches the active jobs immediately. */
    refresh: () => Promise<void>;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

function isActive(status: JobStatus): boolean {
    return ACTIVE_STATUSES.includes(status);
}

function byNewest(a: Job, b: Job): number {
    return b.created_at.localeCompare(a.created_at);
}

/**
 * The TaskProvider component.
 *
 * @param {{ children: ReactNode }} props The provider children.
 * @returns {JSX.Element} The provider.
 */
export const TaskProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { profileId } = useProfile();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [uploads, setUploads] = useState<UploadTask[]>([]);

    // A ref mirror so the poller reads current jobs without re-subscribing.
    const jobsRef = useRef<Job[]>([]);
    jobsRef.current = jobs;

    // Re-upload elimination: remembers the in-flight upload for each file
    // uploaded this session, so a second job on the same file joins it instead
    // of starting its own. The promise is stored (not the resolved id) and it is
    // stored *before* the first await, so two actions fired together on one
    // local file share a single upload rather than each uploading the whole
    // file. Keyed by content identity, see `fileKey`.
    const uploadedRef = useRef(new Map<string, Promise<UploadedFile>>());

    // Abort controllers for in-flight uploads, keyed by their tray id.
    const abortersRef = useRef(new Map<string, AbortController>());

    const refresh = useCallback(async () => {
        if (!profileId) return;
        let active: Job[];
        try {
            active = await listJobs(true);
        } catch {
            // Transient failure: keep the last known state and retry next tick.
            return;
        }
        const activeIds = new Set(active.map((j) => j.id));
        // Jobs we were tracking as active but that dropped off the active list
        // just reached a terminal state; fetch each once for its final result.
        const justFinished = jobsRef.current.filter(
            (j) => isActive(j.status) && !activeIds.has(j.id)
        );
        const finished = await Promise.all(justFinished.map((j) => getJob(j.id).catch(() => null)));

        // Surface failures through the same code -> friendly-message mapping the
        // synchronous endpoints used (toastApiError), via the job's error_code.
        for (const j of finished) {
            if (j?.status === "failed") {
                toastApiError(
                    new ApiError(
                        500,
                        j.error ?? "A Task Failed",
                        j.error_code ?? undefined,
                        j.error_details ?? undefined
                    )
                );
            }
        }

        // A job we were tracking that neither appears as active nor could be
        // fetched has been removed server-side (deleting a file cascades its
        // jobs away), so it is dropped rather than kept forever. Without this
        // the tray and the tasks list resurrect jobs that no longer exist.
        const gone = new Set(justFinished.filter((j, i) => finished[i] === null).map((j) => j.id));

        setJobs((prev) => {
            const byId = new Map(prev.filter((j) => !gone.has(j.id)).map((j) => [j.id, j]));
            for (const j of active) byId.set(j.id, j);
            for (const j of finished) if (j) byId.set(j.id, j);
            return [...byId.values()].sort(byNewest);
        });
    }, [profileId]);

    // Seed (and reset) on mount / profile change.
    useEffect(() => {
        setJobs([]);
        setUploads([]);
        // Abort anything still streaming, otherwise a switched-away profile
        // keeps uploading into the profile the user just left.
        for (const controller of abortersRef.current.values()) controller.abort();
        abortersRef.current.clear();
        uploadedRef.current.clear();
        if (!profileId) return;
        let cancelled = false;
        listJobs(true)
            .then((active) => {
                if (!cancelled) setJobs([...active].sort(byNewest));
            })
            .catch(() => undefined);
        return () => {
            cancelled = true;
        };
    }, [profileId]);

    // Poll while anything is active.
    const hasActiveJobs = jobs.some((j) => isActive(j.status));
    useEffect(() => {
        if (!profileId || !hasActiveJobs) return;
        const handle = window.setInterval(refresh, POLL_INTERVAL_MS);
        return () => window.clearInterval(handle);
    }, [profileId, hasActiveJobs, refresh]);

    const submit = useCallback(async (req: SubmitJobRequest): Promise<Job | null> => {
        const job = await submitJob(req);
        setJobs((prev) => [job, ...prev.filter((j) => j.id !== job.id)].sort(byNewest));
        return job;
    }, []);

    const submitBatch = useCallback(async (req: BatchSubmitRequest): Promise<Job | null> => {
        const job = await submitBatchApi(req);
        setJobs((prev) => [job, ...prev.filter((j) => j.id !== job.id)].sort(byNewest));
        return job;
    }, []);

    const uploadFiles = useCallback(async (files: File[], folder?: string): Promise<number> => {
        if (files.length === 0) return 0;
        const uploadId = `lib-${Date.now()}`;
        const name = folder ?? `${files.length} File(s)`;
        const controller = new AbortController();
        abortersRef.current.set(uploadId, controller);
        setUploads((prev) => [
            ...prev,
            { id: uploadId, name, progress: 0, status: "uploading", cancellable: true },
        ]);
        const patch = (changes: Partial<UploadTask>) =>
            setUploads((prev) => prev.map((u) => (u.id === uploadId ? { ...u, ...changes } : u)));

        let ok = 0;
        for (let i = 0; i < files.length; i++) {
            // Cancelling the set stops before the next file rather than only
            // aborting the one in flight.
            if (controller.signal.aborted) break;
            try {
                await uploadProfileFile(
                    files[i],
                    inferFileType(files[i].name),
                    // Overall progress across the whole set.
                    (percent) => patch({ progress: ((i + percent / 100) / files.length) * 100 }),
                    () => undefined,
                    folder,
                    controller.signal
                );
                ok += 1;
            } catch (e) {
                if (isUploadAborted(e)) break;
                // Keep going; the panel reports the final success count.
            }
            patch({ progress: ((i + 1) / files.length) * 100 });
        }
        abortersRef.current.delete(uploadId);
        setUploads((prev) => prev.filter((u) => u.id !== uploadId));
        return ok;
    }, []);

    const uploadAndSubmit = useCallback(
        async (file: File, options: SubmitOptions): Promise<Job | null> => {
            const key = fileKey(file);
            const pending = uploadedRef.current.get(key);
            // Join the existing upload for this file, whether it already
            // finished or is still streaming. Both branches are inside the try
            // so a rejection (a stale file id the server no longer has) is
            // reported rather than becoming an unhandled rejection.
            if (pending) {
                try {
                    const uploaded = await pending;
                    return await submit({
                        type: options.jobType,
                        file_id: uploaded.id,
                        opts: options.opts,
                        model: options.model,
                        sys_msg: options.sysMsg,
                    });
                } catch (e) {
                    // A rejected upload must not poison the cache, otherwise
                    // every later action on this file replays the same failure.
                    if (uploadedRef.current.get(key) === pending) {
                        uploadedRef.current.delete(key);
                    }
                    throw e;
                }
            }

            const uploadId = `upload-${file.name}-${Date.now()}`;
            const controller = new AbortController();
            abortersRef.current.set(uploadId, controller);
            setUploads((prev) => [
                ...prev,
                {
                    id: uploadId,
                    name: file.name,
                    jobType: options.jobType,
                    progress: 0,
                    status: "uploading",
                    cancellable: true,
                },
            ]);
            const patch = (changes: Partial<UploadTask>) =>
                setUploads((prev) =>
                    prev.map((u) => (u.id === uploadId ? { ...u, ...changes } : u))
                );

            // Registered synchronously, before the first await, so a second
            // action fired in the same tick finds it and joins.
            const upload = uploadProfileFile(
                file,
                options.fileType,
                (percent) => patch({ progress: percent }),
                () => patch({ progress: 100, cancellable: false }),
                undefined,
                controller.signal
            );
            uploadedRef.current.set(key, upload);

            try {
                const uploaded: UploadedFile = await upload;
                const job = await submit({
                    type: options.jobType,
                    file_id: uploaded.id,
                    opts: options.opts,
                    model: options.model,
                    sys_msg: options.sysMsg,
                });
                setUploads((prev) => prev.filter((u) => u.id !== uploadId));
                return job;
            } catch (e) {
                if (uploadedRef.current.get(key) === upload) {
                    uploadedRef.current.delete(key);
                }
                // A cancel is a deliberate action, so the row is dropped rather
                // than left behind as a failure the user has to dismiss.
                if (isUploadAborted(e)) {
                    setUploads((prev) => prev.filter((u) => u.id !== uploadId));
                    return null;
                }
                const message = e instanceof Error ? e.message : "Upload Failed";
                patch({ status: "error", error: message, cancellable: false });
                throw e;
            } finally {
                abortersRef.current.delete(uploadId);
            }
        },
        [submit]
    );

    const waitFor = useCallback(async (id: string): Promise<Job> => {
        for (;;) {
            const job = await getJob(id);
            if (!isActive(job.status)) return job;
            await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        }
    }, []);

    const cancel = useCallback(async (id: string) => {
        try {
            const updated = await cancelJob(id);
            setJobs((prev) => prev.map((j) => (j.id === id ? updated : j)));
        } catch {
            // Ignore: the next poll reconciles the status.
        }
    }, []);

    const cancelUpload = useCallback((id: string) => {
        abortersRef.current.get(id)?.abort();
    }, []);

    const deleteJob = useCallback(async (id: string) => {
        try {
            await deleteJobApi(id);
        } catch (e) {
            // A job that is already gone is the desired end state, so the row is
            // dropped either way. Without this the tray can never shed a job the
            // server removed (deleting a file cascades its jobs away), leaving a
            // phantom row that 404s on every click.
            if (!(e instanceof ApiError) || e.status !== 404) throw e;
        } finally {
            setJobs((prev) => prev.filter((j) => j.id !== id));
        }
    }, []);

    const dismiss = useCallback((id: string) => {
        setJobs((prev) => prev.filter((j) => j.id !== id));
        setUploads((prev) => prev.filter((u) => u.id !== id));
    }, []);

    const forgetUploaded = useCallback((fileIds: string[]) => {
        if (fileIds.length === 0) return;
        const dropped = new Set(fileIds);
        // Resolved entries pointing at a deleted profile file are dropped, so a
        // later action on the same local file re-uploads instead of submitting
        // against an id the server no longer has.
        for (const [key, pending] of uploadedRef.current.entries()) {
            void pending
                .then((uploaded) => {
                    if (dropped.has(uploaded.id) && uploadedRef.current.get(key) === pending) {
                        uploadedRef.current.delete(key);
                    }
                })
                .catch(() => undefined);
        }
    }, []);

    const busy = uploads.some((u) => u.status === "uploading") || hasActiveJobs;

    const value = useMemo(
        () => ({
            jobs,
            uploads,
            busy,
            uploadAndSubmit,
            submit,
            submitBatch,
            uploadFiles,
            waitFor,
            cancel,
            cancelUpload,
            deleteJob,
            dismiss,
            forgetUploaded,
            refresh,
        }),
        [
            jobs,
            uploads,
            busy,
            uploadAndSubmit,
            submit,
            submitBatch,
            uploadFiles,
            waitFor,
            cancel,
            cancelUpload,
            deleteJob,
            dismiss,
            forgetUploaded,
            refresh,
        ]
    );

    return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
};

/**
 * Hook for consuming the task context.
 *
 * @returns {TaskContextType} The task context.
 */
export const useTasks = (): TaskContextType => {
    const ctx = useContext(TaskContext);
    if (ctx === undefined) {
        throw new Error("useTasks must be used within a TaskProvider");
    }
    return ctx;
};
