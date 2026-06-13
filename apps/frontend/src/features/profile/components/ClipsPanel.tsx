/**
 * @packageDocumentation The Clips tab: the saved-clip list + detail view, delete,
 * and "Export all to Anki" (merged in from the old SavedPage).
 */

import { useState } from "react";
import useSWR, { mutate } from "swr";
import { Download, Trash2 } from "lucide-react";
import { toast } from "react-hot-toast";
import { useProfile } from "@/contexts/ProfileContext";
import { Card, Button, EmptyState, IconButton } from "@/shared/ui";
import { downloadFromUrl, staticUrl, truncateText } from "@/shared/format/files";
import { toastApiError } from "@/shared/api/errors";
import type { Clip } from "@/shared/clips/types";
import { listClips, deleteClip, exportAnki } from "../api";
import { ClipDetail } from "./ClipDetail";
import { NoProfile, PanelLoading } from "./panelStates";

/**
 * The ClipsPanel component.
 *
 * @returns {JSX.Element} The clips panel.
 */
export function ClipsPanel() {
    const { profileId } = useProfile();
    const key = profileId ? "profiles/clips" : null;
    const { data, isLoading } = useSWR<Clip[]>(key, listClips, {
        revalidateOnFocus: false,
        keepPreviousData: true,
        onError: (e) => toastApiError(e),
    });
    const [selected, setSelected] = useState<Clip | null>(null);
    const [deleting, setDeleting] = useState<string | null>(null);
    const [exporting, setExporting] = useState(false);

    if (!profileId) return <NoProfile what="view your saved clips" />;
    if (isLoading && !data) return <PanelLoading />;

    const onDelete = async (id: string) => {
        setDeleting(id);
        const tId = toast.loading("Deleting Clip ...");
        try {
            await deleteClip(id);
            toast.success("Clip Deleted", { id: tId });
            if (selected?.id === id) setSelected(null);
            mutate(key);
        } catch (e) {
            toastApiError(e, tId);
        } finally {
            setDeleting(null);
        }
    };

    const onExport = async () => {
        setExporting(true);
        const tId = toast.loading("Generating Anki Deck ...");
        try {
            const { anki_deck_url } = await exportAnki();
            toast.loading("Downloading Deck ...", { id: tId });
            await downloadFromUrl(staticUrl(anki_deck_url), `${profileId}_anki_deck.apkg`);
            toast.success("Deck Downloaded", { id: tId });
        } catch (e) {
            toastApiError(e, tId);
        } finally {
            setExporting(false);
        }
    };

    if (!data || data.length === 0) {
        return (
            <EmptyState
                title="No Clips"
                description="Save Clips From The Player To Build Your Anki Deck"
            />
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 border-b border-ink/10 pb-3">
                <span className="text-sm text-ink-muted">
                    {data.length} {data.length === 1 ? "Clip" : "Clips"}
                </span>
                <Button size="sm" onClick={onExport} loading={exporting} className="shrink-0">
                    <Download size={15} /> Export All To Anki
                </Button>
            </div>

            {selected && <ClipDetail clip={selected} onClose={() => setSelected(null)} />}

            <div className="space-y-2">
                {data.map((clip) => (
                    <Card key={clip.id} className="flex items-center gap-3 p-3">
                        <button
                            className="min-w-0 flex-1 text-left"
                            onClick={() => setSelected(clip)}
                        >
                            <div lang="ja" className="truncate text-ink">
                                {clip.breakdown.sentence ||
                                    clip.breakdown.focus?.word.surface ||
                                    "Clip"}
                            </div>
                            <div className="truncate text-sm text-ink-muted">
                                {truncateText(clip.breakdown.explanation) || "—"}
                            </div>
                        </button>
                        <IconButton
                            label="Delete Clip"
                            size="sm"
                            onClick={() => onDelete(clip.id)}
                            disabled={deleting === clip.id}
                            className="hover:text-danger"
                        >
                            <Trash2 size={16} />
                        </IconButton>
                    </Card>
                ))}
            </div>
        </div>
    );
}
