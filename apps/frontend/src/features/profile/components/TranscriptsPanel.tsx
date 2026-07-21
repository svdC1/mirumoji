/**
 * @packageDocumentation The Transcripts tab: lists the active profile's
 * transcripts with their text + optional LLM explanation, audio download, and
 * delete.
 */

import { useState } from "react";
import useSWR, { mutate } from "swr";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import { Download, Trash2 } from "lucide-react";
import { toast } from "react-hot-toast";
import { useProfile } from "@/contexts/ProfileContext";
import { Card, EmptyState, IconButton, Badge } from "@/shared/ui";
import {
    downloadFromUrl,
    getFileExtension,
    staticUrl,
    truncateFilename,
} from "@/shared/format/files";
import { toastApiError } from "@/shared/api/errors";
import { listTranscripts, deleteTranscript } from "../api";
import type { ProfileTranscript } from "../types";
import { NoProfile, PanelLoading } from "./panelStates";

/**
 * The TranscriptsPanel component.
 *
 * @returns {JSX.Element} The transcripts panel.
 */
export function TranscriptsPanel() {
    const { profileId } = useProfile();
    const key = profileId ? "profiles/transcripts" : null;
    const { data, isLoading } = useSWR<ProfileTranscript[]>(key, listTranscripts, {
        revalidateOnFocus: false,
        keepPreviousData: true,
        onError: (e) => toastApiError(e),
    });
    const [deleting, setDeleting] = useState<string | null>(null);
    const [downloading, setDownloading] = useState<string | null>(null);

    if (!profileId) return <NoProfile what="view your transcripts" />;
    if (isLoading && !data) return <PanelLoading />;
    if (!data || data.length === 0) {
        return (
            <EmptyState
                title="No Transcripts"
                description="Transcribe Audio To Build Your Transcript History"
            />
        );
    }

    // The delete is optimistic: the card leaves the cached list before the
    // request so the panel responds on click even on a high-latency host, and
    // a revalidation follows to reconcile (restoring the card if the delete
    // failed).
    const onDelete = async (id: string) => {
        setDeleting(id);
        void mutate(key, (current?: ProfileTranscript[]) => current?.filter((t) => t.id !== id), {
            revalidate: false,
        });
        try {
            await deleteTranscript(id);
            toast.success("Transcript Deleted");
        } catch (e) {
            toastApiError(e);
        } finally {
            void mutate(key);
            setDeleting(null);
        }
    };

    const onDownload = async (t: ProfileTranscript) => {
        if (!t.url) return;
        setDownloading(t.id);
        try {
            const ext = getFileExtension(t.url) || "audio";
            await downloadFromUrl(staticUrl(t.url), `${truncateFilename(t.id, 10, 5)}.${ext}`);
            toast.success("Audio Downloaded");
        } catch (e) {
            toastApiError(e);
        } finally {
            setDownloading(null);
        }
    };

    return (
        <div className="space-y-3">
            {data.map((t) => (
                <Card key={t.id} className="p-4">
                    <div className="mb-2 flex items-center gap-2">
                        <Badge title={t.id}>ID {truncateFilename(t.id, 4, 4)}</Badge>
                        <div className="flex-1" />
                        {t.url && (
                            <IconButton
                                label="Download Audio"
                                size="sm"
                                onClick={() => onDownload(t)}
                                disabled={downloading === t.id}
                            >
                                <Download size={16} />
                            </IconButton>
                        )}
                        <IconButton
                            label="Delete Transcript"
                            size="sm"
                            onClick={() => onDelete(t.id)}
                            disabled={deleting === t.id}
                            className="hover:text-danger"
                        >
                            <Trash2 size={16} />
                        </IconButton>
                    </div>
                    <p lang="ja" className="whitespace-pre-wrap text-ink">
                        {t.text}
                    </p>
                    {t.llm_explanation && (
                        <div className="prose prose-invert prose-sm mt-3 max-w-none border-t border-ink/10 pt-3">
                            <ReactMarkdown remarkPlugins={[remarkBreaks]}>
                                {t.llm_explanation}
                            </ReactMarkdown>
                        </div>
                    )}
                </Card>
            ))}
        </div>
    );
}
