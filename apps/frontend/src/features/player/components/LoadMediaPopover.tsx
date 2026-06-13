/**
 * @packageDocumentation A popover to load a video + subtitles, either from the
 * device or from the active profile's stored files.
 */

import { useRef, useState } from "react";
import useSWR from "swr";
import { FolderOpen } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiFetch } from "@/shared/api/client";
import { toastApiError } from "@/shared/api/errors";
import { staticUrl, truncateFilename } from "@/shared/format/files";
import { IconButton, Popover, Button, cn } from "@/shared/ui";
import { usePlayer } from "@/contexts/PlayerContext";
import { useProfile } from "@/contexts/ProfileContext";
import type { ProfileFile } from "@/features/profile/types";

const VIDEO_ACCEPT = [
    "video/*",
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".m4v",
    ".3gp",
    ".ogv",
    ".ts",
].join(",");

function FileList({
    title,
    files,
    onSelect,
}: {
    title: string;
    files: ProfileFile[];
    onSelect: (f: ProfileFile) => void;
}) {
    return (
        <div>
            <h4 className="mb-1 text-2xs uppercase tracking-wide text-ink-faint">{title}</h4>
            <ul className="max-h-28 space-y-1 overflow-y-auto">
                {files.length > 0 ? (
                    files.map((f) => (
                        <li key={f.id}>
                            <button
                                onClick={() => onSelect(f)}
                                className="w-full rounded bg-surface-2 px-2 py-1 text-left text-sm text-ink-muted transition-colors hover:text-shu"
                            >
                                {truncateFilename(f.name, 12, 12)}
                            </button>
                        </li>
                    ))
                ) : (
                    <li className="rounded bg-surface-2 px-2 py-1 text-center text-sm italic text-ink-faint">
                        None
                    </li>
                )}
            </ul>
        </div>
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
    const videoInputRef = useRef<HTMLInputElement | null>(null);
    const srtInputRef = useRef<HTMLInputElement | null>(null);
    const { setVideo, setVideoUrl, setSrt, setVideoFileName, setSrtFileName, setSrtFileId } =
        usePlayer();
    const { profileId } = useProfile();

    const { data: files } = useSWR<ProfileFile[]>(
        open && profileId ? "profiles/files" : null,
        apiFetch,
        { revalidateOnFocus: false, keepPreviousData: true }
    );

    const videoFiles = (files ?? []).filter((f) => f.type === "mp4");
    const subtitleFiles = (files ?? []).filter((f) => f.type === "srt");

    const onPickVideo = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setVideoUrl(null);
        setVideo(file);
        setVideoFileName(file.name);
    };

    const onPickSrt = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setSrt(file);
        setSrtFileName(file.name);
        setSrtFileId(null); // device file isn't a profile record
    };

    const selectProfileFile = async (file: ProfileFile) => {
        if (file.type === "mp4") {
            setVideo(null);
            setVideoUrl(staticUrl(file.url));
            setVideoFileName(file.name);
        } else if (file.type === "srt") {
            try {
                const res = await fetch(staticUrl(file.url));
                const text = await res.text();
                const srtFile = new File([text], file.name, { type: "application/x-subrip" });
                setSrt(srtFile);
                setSrtFileName(file.name);
                setSrtFileId(file.id); // track the profile file for in-place fixes
            } catch (err) {
                toastApiError(err);
                toast.error("Could Not Load Subtitle File");
            }
        }
    };

    return (
        <div className={cn("relative", className)}>
            <IconButton label="Load media" active={open} onClick={() => setOpen((v) => !v)}>
                <FolderOpen size={18} />
            </IconButton>
            <Popover open={open} onClose={() => setOpen(false)} className="w-60 p-4 sm:w-72">
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
                        <input
                            ref={videoInputRef}
                            type="file"
                            accept={VIDEO_ACCEPT}
                            onChange={onPickVideo}
                            className="hidden"
                        />
                        <input
                            ref={srtInputRef}
                            type="file"
                            accept=".srt"
                            onChange={onPickSrt}
                            className="hidden"
                        />
                    </div>

                    {profileId && (
                        <div className="space-y-3 border-t border-ink/10 pt-3">
                            <FileList
                                title="Profile videos"
                                files={videoFiles}
                                onSelect={selectProfileFile}
                            />
                            <FileList
                                title="Profile subtitles"
                                files={subtitleFiles}
                                onSelect={selectProfileFile}
                            />
                        </div>
                    )}
                </div>
            </Popover>
        </div>
    );
}
