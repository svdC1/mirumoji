/**
 * @packageDocumentation Groups profile files by lineage: each source video (or
 * standalone file) becomes a head with its derived variants (generated / fixed
 * SRTs, converted MP4) nested under it. Shared by the Files panel and the
 * player's Load Media popover.
 */

import { inferFileType } from "@/shared/format/files";
import type { ProfileFile } from "./types";

/** A source file (head) with its derived variants nested under it. */
export type VideoGroup = { head: ProfileFile; variants: ProfileFile[] };

/** Order variants stably: generated, then fixed, then saved, then converted. */
const ORIGIN_RANK: Record<string, number> = {
    generated: 0,
    fixed: 1,
    subtitle: 2,
    converted: 3,
};

/** The media class of a file, from its extension (matches the player). */
export function fileKind(f: ProfileFile): "video" | "audio" | "srt" | "other" {
    const t = inferFileType(f.name);
    return t === "video" || t === "audio" || t === "srt" ? t : "other";
}

/**
 * Groups files into source heads with their derived variants nested under them.
 *
 * A head is a root file (no `source_file_id`) or a dangling derivative whose
 * source is no longer in the set (its source was deleted). Every other file is
 * a variant sorted under its head.
 *
 * @param {ProfileFile[]} files The files to group.
 * @returns {VideoGroup[]} One group per head, in the input head order.
 */
export function buildFileGroups(files: ProfileFile[]): VideoGroup[] {
    const headIds = new Set(files.filter((f) => !f.source_file_id).map((f) => f.id));
    const variantsBySource = new Map<string, ProfileFile[]>();
    for (const f of files) {
        if (f.source_file_id && headIds.has(f.source_file_id)) {
            const list = variantsBySource.get(f.source_file_id);
            if (list) list.push(f);
            else variantsBySource.set(f.source_file_id, [f]);
        }
    }
    const heads = files.filter((f) => !f.source_file_id || !headIds.has(f.source_file_id));
    return heads.map((head) => ({
        head,
        variants: (variantsBySource.get(head.id) ?? [])
            .slice()
            .sort(
                (a, b) => (ORIGIN_RANK[a.origin ?? ""] ?? 9) - (ORIGIN_RANK[b.origin ?? ""] ?? 9)
            ),
    }));
}
