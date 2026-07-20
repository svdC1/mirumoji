/**
 * @packageDocumentation A popover to load a video + subtitles, either from the
 * device or from the active profile's stored files. Profile media is grouped by
 * lineage, so a video's derived files (subtitles, a converted MP4) sit right
 * under it, and every row loads on its own.
 */

import { useRef, useState } from "react";
import useSWR from "swr";
import { ChevronDown, ChevronRight, FileText, FolderOpen, Play } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiFetch } from "@/shared/api/client";
import { toastApiError } from "@/shared/api/errors";
import { inferFileType, staticUrl } from "@/shared/format/files";
import { buildFileGroups, fileKind } from "@/features/profile/grouping";
import { IconButton, Popover, Button, cn } from "@/shared/ui";
import { usePlayer } from "@/contexts/PlayerContext";
import { useProfile } from "@/contexts/ProfileContext";
import type { ProfileFile } from "@/features/profile/types";

function isVideoName(name: string): boolean {
    return inferFileType(name) === "video";
}

/** Short badges naming what each derived file is, keyed by its origin. */
const ORIGIN_LABEL: Record<string, string> = {
    generated: "Generated",
    fixed: "Fixed",
    subtitle: "Saved",
    converted: "Converted",
};

const rowBtn =
    "flex w-full items-center gap-1.5 rounded bg-surface-2 px-2 py-1 text-left text-sm text-ink-muted transition-colors hover:text-shu";

/**
 * A single loadable file row: a kind icon, the file's real name, and an origin
 * badge. Clicking it loads exactly this file, never a sibling.
 *
 * @param {{ file: ProfileFile; onLoad: (f: ProfileFile) => void }} props The
 *   file to show and the loader to call on click.
 * @returns {JSX.Element} The row button.
 */
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

/**
 * The LoadMediaPopover component.
 *
 * @param {{ className?: string }} props Optional class for the trigger.
 * @returns {JSX.Element} The load-media trigger + popover.
 */
export function LoadMediaPopover({ className }: { className?: string }) {
    const [open, setOpen] = useState(false);
    const [expanded, setExpanded] = useState<Set<string>>(new Set());
    const videoInputRef = useRef<HTMLInputElement | null>(null);
    const srtInputRef = useRef<HTMLInputElement | null>(null);
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

    // Group by lineage. Playable media (video / audio heads) become the primary
    // list; standalone or orphaned subtitles are offered separately.
    const groups = buildFileGroups(files ?? []);
    const mediaGroups = groups.filter((g) => fileKind(g.head) !== "srt");
    const subtitleGroups = groups.filter((g) => fileKind(g.head) === "srt");
    // Only reserve the left-hand toggle column when at least one row can
    // expand. With no expandable groups the rows fill that space instead.
    const anyExpandable = mediaGroups.some((g) => g.variants.length > 0);

    const toggle = (id: string) =>
        setExpanded((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });

    const loadVideo = (file: ProfileFile) => {
        // Load every video the same way and let the player try to play it. A
        // container this browser can't decode (e.g. .mkv on iOS) is caught
        // there and offered for conversion. videoFileId is always set, so the
        // toolbar's by-reference actions stay enabled even when it won't play.
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
            const srtFile = new File([text], file.name, { type: "application/x-subrip" });
            setSrt(srtFile);
            setSrtFileName(file.name);
            setSrtFileId(file.id);
        } catch (err) {
            toastApiError(err);
            toast.error("Could Not Load Subtitle File");
        }
    };

    // Load one file on its own. Subtitles fill the SRT slot, everything else
    // (source video, converted MP4, audio) the video slot. Every row loads
    // exactly the file it names, never a sibling.
    const loadFile = (file: ProfileFile) => {
        if (fileKind(file) === "srt") void loadSrt(file);
        else loadVideo(file);
    };

    // A file input fires `change` only when the picked file differs from its
    // current value, so re-picking the same file after a reset-less pick is
    // silently ignored and the dialog reads as unresponsive. Every path clears
    // the value, including the ones that succeed.
    const onPickVideo = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = "";
        if (!file) return;
        // The input has no `accept` (an iOS/.mkv workaround), so it accepts any
        // file. Reject non-video picks here so Generate SRT / Convert never run
        // FFmpeg/Whisper over a text or other unrelated file.
        if (!isVideoName(file.name)) {
            toast.error("Please Select A Video File");
            return;
        }
        setVideoUrl(null);
        setVideo(file);
        setVideoFileName(file.name);
        setVideoFileId(null);
        setTimestamp(null);
    };

    const onPickSrt = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = "";
        if (!file) return;
        setSrt(file);
        setSrtFileName(file.name);
        setSrtFileId(null);
    };

    return (
        <div className={cn("relative", className)}>
            {/*
             * Mounted outside the Popover, which unmounts its children when it
             * closes. On iOS, opening the native file sheet can dismiss the
             * popover, and an input torn down while the sheet is still up never
             * receives its `change` event, so the pick is silently lost and the
             * dialog reads as unresponsive.
             *
             * No `accept` on the video input: iOS maps accept tokens to UTTypes
             * and greys anything it can't map, and Matroska (.mkv) has no Apple
             * UTType, so any video filter hides .mkv there. Leaving it open
             * keeps every container selectable.
             */}
            <input ref={videoInputRef} type="file" onChange={onPickVideo} className="hidden" />
            <input
                ref={srtInputRef}
                type="file"
                accept=".srt"
                onChange={onPickSrt}
                className="hidden"
            />
            <IconButton label="Load media" active={open} onClick={() => setOpen((v) => !v)}>
                <FolderOpen size={18} />
            </IconButton>
            <Popover open={open} onClose={() => setOpen(false)} className="w-64 p-4 sm:w-72">
                <div className="space-y-4">
                    <div className="space-y-2">
                        <h4 className="text-2xs uppercase tracking-wide text-ink-faint">
                            From device
                        </h4>
                        <Button
                            variant="secondary"
                            size="sm"
                            className="w-full"
                            onClick={() => videoInputRef.current?.click()}
                        >
                            Select Video
                        </Button>
                        <Button
                            variant="secondary"
                            size="sm"
                            className="w-full"
                            onClick={() => srtInputRef.current?.click()}
                        >
                            Select Subtitles
                        </Button>
                    </div>

                    {profileId && (
                        <div className="space-y-3 border-t border-ink/10 pt-3">
                            <div>
                                <h4 className="mb-1 text-2xs uppercase tracking-wide text-ink-faint">
                                    Profile media
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
                                                                    onClick={() =>
                                                                        toggle(g.head.id)
                                                                    }
                                                                    className="shrink-0 text-ink-faint transition-colors hover:text-ink"
                                                                    aria-label={
                                                                        isOpen
                                                                            ? "Hide files"
                                                                            : "Show files"
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
                                                            <FileRow
                                                                file={g.head}
                                                                onLoad={loadFile}
                                                            />
                                                        </div>
                                                    </div>
                                                    {isOpen && hasVariants && (
                                                        <ul className="ml-3 mt-1 space-y-1 border-l border-ink/10 pl-2">
                                                            {g.variants.map((v) => (
                                                                <li key={v.id}>
                                                                    <FileRow
                                                                        file={v}
                                                                        onLoad={loadFile}
                                                                    />
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
                                <div>
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
                    )}
                </div>
            </Popover>
        </div>
    );
}
