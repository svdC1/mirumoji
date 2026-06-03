/**
 * @packageDocumentation The Files tab: lists the active profile's stored files
 * with download + delete.
 */

import { useState } from "react";
import useSWR, { mutate } from "swr";
import { Download, FileIcon, Trash2 } from "lucide-react";
import { toast } from "react-hot-toast";
import { useProfile } from "@/contexts/ProfileContext";
import { Card, EmptyState, IconButton } from "@/shared/ui";
import { staticUrl, truncateFilename } from "@/shared/format/files";
import { toastApiError } from "@/shared/api/errors";
import { listFiles, deleteFile } from "../api";
import type { ProfileFile } from "../types";
import { NoProfile, PanelLoading } from "./panelStates";

/**
 * The FilesPanel component.
 *
 * @returns {JSX.Element} The files panel.
 */
export function FilesPanel() {
    const { profileId } = useProfile();
    const key = profileId ? "profiles/files" : null;
    const { data, isLoading } = useSWR<ProfileFile[]>(key, listFiles, {
        revalidateOnFocus: false,
        keepPreviousData: true,
        onError: (e) => toastApiError(e),
    });
    const [deleting, setDeleting] = useState<string | null>(null);

    if (!profileId) return <NoProfile what="view your files" />;
    if (isLoading && !data) return <PanelLoading />;
    if (!data || data.length === 0) {
        return <EmptyState title="No Files" description="Files You Generate Or Save Appear Here" />;
    }

    const onDelete = async (id: string) => {
        setDeleting(id);
        try {
            await deleteFile(id);
            toast.success("File Deleted");
            mutate(key);
        } catch (e) {
            toastApiError(e);
        } finally {
            setDeleting(null);
        }
    };

    return (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.map((file) => (
                <Card key={file.id} className="flex items-center gap-3 p-3">
                    <FileIcon size={18} className="shrink-0 text-ink-faint" />
                    <span className="min-w-0 flex-1 text-sm text-ink" title={file.name}>
                        {truncateFilename(file.name, 6, 6)}
                    </span>
                    <a href={staticUrl(file.url)} download={file.name}>
                        <IconButton label="Download" size="sm">
                            <Download size={16} />
                        </IconButton>
                    </a>
                    <IconButton
                        label="Delete"
                        size="sm"
                        onClick={() => onDelete(file.id)}
                        disabled={deleting === file.id}
                        className="hover:text-danger"
                    >
                        <Trash2 size={16} />
                    </IconButton>
                </Card>
            ))}
        </div>
    );
}
