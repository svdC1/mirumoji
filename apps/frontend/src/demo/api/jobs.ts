/**
 * @packageDocumentation The demo job-lifecycle simulator. The sample's long-ops
 * (generate_srt / transcribe / convert / fix_srt) are submitted for real by the
 * reused UI, so this advances a submitted job queued -> running -> succeeded over
 * a few of `TaskContext`'s 2000 ms polls and attaches the canned result.
 */

import { jobResult } from "./fixtures";

interface SimJob {
    id: string;
    type: string;
    parentId: string | null;
    childIds: string[];
    createdAt: number;
    cancelled: boolean;
}

const jobs = new Map<string, SimJob>();
const order: string[] = [];
let counter = 0;

// Tuned so a job visibly runs then completes within two polls (poll = 2000 ms).
const RUN_MS = 400;
const DONE_MS = 2600;

type JobResponse = Record<string, unknown>;

function snapshot(j: SimJob): JobResponse {
    const elapsed = Date.now() - j.createdAt;
    const isBatch = j.childIds.length > 0;
    let status = "queued";
    let progress = 0;
    let result: unknown = null;

    if (j.cancelled) {
        status = "cancelled";
    } else if (elapsed >= DONE_MS) {
        status = "succeeded";
        progress = 1;
        result = isBatch ? batchResult(j) : (jobResult(j.type) ?? null);
    } else if (elapsed >= RUN_MS) {
        status = "running";
        progress = Math.min(0.95, (elapsed - RUN_MS) / (DONE_MS - RUN_MS));
    }

    return {
        id: j.id,
        type: j.type,
        status,
        progress,
        total: isBatch ? j.childIds.length : 1,
        completed: status === "succeeded" ? (isBatch ? j.childIds.length : 1) : 0,
        parent_id: j.parentId,
        result,
        error: null,
        error_code: null,
        error_details: null,
        created_at: new Date(j.createdAt).toISOString(),
        updated_at: new Date().toISOString(),
    };
}

function batchResult(parent: SimJob): JobResponse {
    const done = parent.childIds.filter((id) => {
        const c = jobs.get(id);
        return c && Date.now() - c.createdAt >= DONE_MS && !c.cancelled;
    }).length;
    return {
        total: parent.childIds.length,
        succeeded: done,
        failed: 0,
        cancelled: 0,
        children: [...parent.childIds],
    };
}

function create(type: string, parentId: string | null): SimJob {
    const job: SimJob = {
        id: `demo-job-${++counter}`,
        type,
        parentId,
        childIds: [],
        createdAt: Date.now(),
        cancelled: false,
    };
    jobs.set(job.id, job);
    if (parentId === null) order.unshift(job.id);
    return job;
}

/** Splits a batch type (`batch_transcribe`) into its per-child singular. */
function childType(batchType: string): string {
    return batchType.startsWith("batch_") ? batchType.slice("batch_".length) : batchType;
}

/**
 * Handles a `/jobs` request, returning the response value `apiFetch` would give
 * (a job, a list, or `undefined` for a 204 delete).
 */
export function handleJobs(method: string, url: string, body?: unknown): unknown {
    const [rawPath, rawQuery = ""] = url.split("?");
    const path = rawPath.replace(/^\/+/, "");
    const segments = path.split("/"); // ["jobs"], ["jobs", id], ["jobs", id, "children"|"cancel"], ["jobs","batch"]
    const req = (typeof body === "string" ? JSON.parse(body || "null") : body) as Record<
        string,
        unknown
    > | null;

    if (method === "POST" && path === "jobs") {
        return snapshot(create(String(req?.type ?? "generate_srt"), null));
    }
    if (method === "POST" && path === "jobs/batch") {
        const parent = create(String(req?.type ?? "batch_generate_srt"), null);
        const fileIds = Array.isArray(req?.file_ids) ? (req!.file_ids as unknown[]) : [];
        fileIds.forEach(() => {
            parent.childIds.push(create(childType(parent.type), parent.id).id);
        });
        return snapshot(parent);
    }
    if (method === "POST" && segments[2] === "cancel") {
        const j = jobs.get(segments[1]);
        if (j) j.cancelled = true;
        return j ? snapshot(j) : undefined;
    }
    if (method === "DELETE" && segments.length === 2) {
        jobs.delete(segments[1]);
        const i = order.indexOf(segments[1]);
        if (i !== -1) order.splice(i, 1);
        return undefined; // 204
    }
    if (method === "GET" && segments[2] === "children") {
        const parent = jobs.get(segments[1]);
        return (parent?.childIds ?? []).map((id) => snapshot(jobs.get(id)!));
    }
    if (method === "GET" && segments.length === 2) {
        const j = jobs.get(segments[1]);
        return j ? snapshot(j) : undefined;
    }
    // GET /jobs (list), honouring ?active=true
    const activeOnly = new URLSearchParams(rawQuery).get("active") === "true";
    return order
        .map((id) => snapshot(jobs.get(id)!))
        .filter((j) => !activeOnly || j.status === "queued" || j.status === "running");
}
