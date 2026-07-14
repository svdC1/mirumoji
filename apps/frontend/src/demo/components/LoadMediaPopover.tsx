/**
 * @packageDocumentation Demo variant of the load-media popover, aliased in only
 * for `--mode demo`. Loading a device file has no fixtures, so the "From device"
 * pickers are dropped; the profile-media list (the captured sample and its
 * derived files) is kept and loads from fixtures exactly as in the real app.
 */

import { useState } from "react";
import useSWR from "swr";
import { ChevronDown, ChevronRight, FileText, FolderOpen, Play } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiFetch } from "@/shared/api/client";
import { toastApiError } from "@/shared/api/errors";
import { staticUrl } from "@/shared/format/files";
import { buildFileGroups, fileKind } from "@/features/profile/grouping";
import { IconButton, Popover, cn } from "@/shared/ui";
import { usePlayer } from "@/contexts/PlayerContext";
import { useProfile } from "@/contexts/ProfileContext";
import type { ProfileFile } from "@/features/profile/types";

const ORIGIN_LABEL: Record<string, string> = {
    generated: "Generated",
    fixed: "Fixed",
    subtitle: "Saved",
    converted: "Converted",
};

const rowBtn =
    "flex w-full items-center gap-1.5 rounded bg-surface-2 px-2 py-1 text-left text-sm text-ink-muted transition-colors hover:text-shu";

function FileRow({ file, onLoad }: { file: ProfileFile; onLoad: (f: ProfileFile) => void }) {
    const Icon = fileKind(file) === "srt" ? FileText : Play;
    const label = ORIGIN_LABEL[file.origin ?? ""];
    return (
        <button onClick={() => onLoad(file)} className={rowBtn} title={file.name}>
            <Icon size={13} className="shrink-0" />
            <span className="min-w-0 flex-1 truncate">{file.name}</span>
            {label && (
                <span className="shrink-0 rounded-full bg-ink/10 px-1.5 py-0.5 text-2xs text-ink-faint">
                    {label}
                </span>
            )}
        </button>
    );
}

/** The demo load-media popover: the profile-media list only, no device pickers. */
export function LoadMediaPopover({ className }: { className?: string }) {
    const [open, setOpen] = useState(false);
    const [expanded, setExpanded] = useState<Set<string>>(new Set());
    const {
        setVideo,
        setVideoUrl,
        setSrt,
        setVideoFileName,
        setVideoFileId,
        setSrtFileName,
        setSrtFileId,
        setTimestamp,
    } = usePlayer();
    const { profileId } = useProfile();

    const { data: files } = useSWR<ProfileFile[]>(
        open && profileId ? "profiles/files" : null,
        apiFetch,
        { revalidateOnFocus: false, keepPreviousData: true }
    );

    const groups = buildFileGroups(files ?? []);
    const mediaGroups = groups.filter((g) => fileKind(g.head) !== "srt");
    const subtitleGroups = groups.filter((g) => fileKind(g.head) === "srt");
    const anyExpandable = mediaGroups.some((g) => g.variants.length > 0);

    const toggle = (id: string) =>
        setExpanded((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });

    const loadVideo = (file: ProfileFile) => {
        setVideo(null);
        setVideoUrl(staticUrl(file.url));
        setVideoFileName(file.name);
        setVideoFileId(file.id);
        setTimestamp(null);
    };

    const loadSrt = async (file: ProfileFile) => {
        try {
            const res = await fetch(staticUrl(file.url));
            const text = await res.text();
            setSrt(new File([text], file.name, { type: "application/x-subrip" }));
            setSrtFileName(file.name);
            setSrtFileId(file.id);
        } catch (err) {
            toastApiError(err);
            toast.error("Could Not Load Subtitle File");
        }
    };

    const loadFile = (file: ProfileFile) => {
        if (fileKind(file) === "srt") void loadSrt(file);
        else loadVideo(file);
    };

    return (
        <div className={cn("relative", className)}>
            <IconButton label="Load media" active={open} onClick={() => setOpen((v) => !v)}>
                <FolderOpen size={18} />
            </IconButton>
            <Popover open={open} onClose={() => setOpen(false)} className="w-64 p-4 sm:w-72">
                <div className="space-y-3">
                    <div>
                        <h4 className="mb-1 text-2xs uppercase tracking-wide text-ink-faint">
                            Sample media
                        </h4>
                        <ul className="max-h-52 space-y-1 overflow-y-auto">
                            {mediaGroups.length > 0 ? (
                                mediaGroups.map((g) => {
                                    const isOpen = expanded.has(g.head.id);
                                    const hasVariants = g.variants.length > 0;
                                    return (
                                        <li key={g.head.id}>
                                            <div className="flex items-center gap-1">
                                                {anyExpandable &&
                                                    (hasVariants ? (
                                                        <button
                                                            type="button"
                                                            onClick={() => toggle(g.head.id)}
                                                            className="shrink-0 text-ink-faint transition-colors hover:text-ink"
                                                            aria-label={
                                                                isOpen ? "Hide files" : "Show files"
                                                            }
                                                            aria-expanded={isOpen}
                                                        >
                                                            {isOpen ? (
                                                                <ChevronDown size={15} />
                                                            ) : (
                                                                <ChevronRight size={15} />
                                                            )}
                                                        </button>
                                                    ) : (
                                                        <span className="w-[15px] shrink-0" />
                                                    ))}
                                                <div className="min-w-0 flex-1">
                                                    <FileRow file={g.head} onLoad={loadFile} />
                                                </div>
                                            </div>
                                            {isOpen && hasVariants && (
                                                <ul className="ml-3 mt-1 space-y-1 border-l border-ink/10 pl-2">
                                                    {g.variants.map((v) => (
                                                        <li key={v.id}>
                                                            <FileRow file={v} onLoad={loadFile} />
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                        </li>
                                    );
                                })
                            ) : (
                                <li className="rounded bg-surface-2 px-2 py-1 text-center text-sm italic text-ink-faint">
                                    None
                                </li>
                            )}
                        </ul>
                    </div>

                    {subtitleGroups.length > 0 && (
                        <div className="border-t border-ink/10 pt-3">
                            <h4 className="mb-1 text-2xs uppercase tracking-wide text-ink-faint">
                                Other subtitles
                            </h4>
                            <ul className="max-h-28 space-y-1 overflow-y-auto">
                                {subtitleGroups.map((g) => (
                                    <li key={g.head.id}>
                                        <FileRow file={g.head} onLoad={loadFile} />
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </Popover>
        </div>
    );
}
