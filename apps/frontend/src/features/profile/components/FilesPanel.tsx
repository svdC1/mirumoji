/**
 * @packageDocumentation The Files tab: the batch hub. An Upload dropdown adds
 * files or a folder (tracked in the Tasks tray); files list in collapsible
 * folder trays; and an Options dropdown runs a batch, deletes, or clears the
 * current selection.
 */

import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import useSWR, { mutate } from "swr";
import {
    ChevronDown,
    ChevronRight,
    Download,
    FileIcon,
    FolderUp,
    Play,
    Trash2,
    Upload,
    X,
} from "lucide-react";
import { toast } from "react-hot-toast";
import { useProfile } from "@/contexts/ProfileContext";
import { useTasks } from "@/contexts/TaskContext";
import { Button, Card, Checkbox, EmptyState, IconButton, Popover, cn } from "@/shared/ui";
import { staticUrl, truncateFilename } from "@/shared/format/files";
import { toastApiError } from "@/shared/api/errors";
import { listFiles, deleteFile } from "../api";
import type { ProfileFile } from "../types";
import { NoProfile, PanelLoading } from "./panelStates";
import { BatchDialog } from "./BatchDialog";

const SWR_KEY = "profiles/files";
const UNGROUPED = "__ungrouped__";

/**
 * The FilesPanel component.
 *
 * @returns {JSX.Element} The files panel.
 */
export function FilesPanel() {
    const { profileId } = useProfile();
    const tasks = useTasks();
    const { data, isLoading } = useSWR<ProfileFile[]>(profileId ? SWR_KEY : null, listFiles, {
        revalidateOnFocus: false,
        keepPreviousData: true,
        onError: (e) => toastApiError(e),
    });
    const [deleting, setDeleting] = useState<string | null>(null);
    const [selected, setSelected] = useState<Set<string>>(new Set());
    const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
    const [uploading, setUploading] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [uploadOpen, setUploadOpen] = useState(false);
    const [optionsOpen, setOptionsOpen] = useState(false);

    const filesInputRef = useRef<HTMLInputElement | null>(null);
    const folderInputRef = useRef<HTMLInputElement | null>(null);

    // `webkitdirectory` is non-standard, so it is set imperatively.
    useEffect(() => {
        const el = folderInputRef.current;
        if (el) {
            el.setAttribute("webkitdirectory", "");
            el.setAttribute("directory", "");
        }
    }, []);

    const groups = useMemo(() => {
        const map = new Map<string, ProfileFile[]>();
        for (const f of data ?? []) {
            const k = f.folder || UNGROUPED;
            const list = map.get(k);
            if (list) list.push(f);
            else map.set(k, [f]);
        }
        return {
            named: [...map.entries()].filter(([k]) => k !== UNGROUPED),
            ungrouped: map.get(UNGROUPED),
        };
    }, [data]);

    if (!profileId) return <NoProfile what="manage your files" />;

    const toggleFile = (id: string) =>
        setSelected((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });

    const toggleGroup = (files: ProfileFile[]) =>
        setSelected((prev) => {
            const next = new Set(prev);
            const all = files.every((f) => next.has(f.id));
            for (const f of files) {
                if (all) next.delete(f.id);
                else next.add(f.id);
            }
            return next;
        });

    const toggleCollapse = (title: string) =>
        setCollapsed((prev) => {
            const next = new Set(prev);
            if (next.has(title)) next.delete(title);
            else next.add(title);
            return next;
        });

    const clearSelection = () => setSelected(new Set());

    // Deleting a file cascades its dependent jobs away server-side. The server
    // returns those job ids, so they are pruned from the task tray immediately
    // (which polls only while a job is active) and the Tasks tab is refreshed.
    const onDelete = async (id: string) => {
        setDeleting(id);
        try {
            const res = await deleteFile(id);
            toast.success("File Deleted");
            setSelected((prev) => {
                const next = new Set(prev);
                next.delete(id);
                return next;
            });
            res.deleted_job_ids.forEach((jobId) => tasks.dismiss(jobId));
            mutate(SWR_KEY);
            mutate("jobs/history");
        } catch (e) {
            toastApiError(e);
        } finally {
            setDeleting(null);
        }
    };

    const deleteSelected = async () => {
        const ids = [...selected];
        if (ids.length === 0) return;
        const results = await Promise.allSettled(ids.map((id) => deleteFile(id)));
        const ok = results.filter((r) => r.status === "fulfilled").length;
        // Prune the tray of every job cascaded away by the successful deletes.
        for (const r of results) {
            if (r.status === "fulfilled") {
                r.value.deleted_job_ids.forEach((jobId) => tasks.dismiss(jobId));
            }
        }
        clearSelection();
        if (ok > 0) toast.success(`Deleted ${ok} File(s)`);
        if (ok < ids.length) toast.error(`${ids.length - ok} File(s) Could Not Be Deleted`);
        mutate(SWR_KEY);
        mutate("jobs/history");
    };

    // Library uploads run through the task tray (which shows their progress).
    const runUpload = async (files: File[], folder?: string) => {
        if (files.length === 0) return;
        setUploading(true);
        const ok = await tasks.uploadFiles(files, folder);
        setUploading(false);
        if (ok > 0) toast.success(`Uploaded ${ok} File(s)`);
        mutate(SWR_KEY);
    };

    const onPickFiles = (e: ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files ?? []);
        e.target.value = "";
        void runUpload(files);
    };

    const onPickFolder = (e: ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files ?? []);
        e.target.value = "";
        const folder = files[0]?.webkitRelativePath?.split("/")[0] || undefined;
        void runUpload(files, folder);
    };

    const fileCard = (file: ProfileFile) => (
        <Card key={file.id} className="flex items-center gap-2.5 p-3">
            <Checkbox
                checked={selected.has(file.id)}
                onChange={() => toggleFile(file.id)}
                label={`Select ${file.name}`}
            />
            <FileIcon size={16} className="shrink-0 text-ink-faint" />
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
    );

    const fileGrid = (files: ProfileFile[]) => (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{files.map(fileCard)}</div>
    );

    /** A folder as a contained tray with a Shu spine and a collapsible body. */
    const renderTray = (title: string, files: ProfileFile[], spine: string) => {
        const open = !collapsed.has(title);
        return (
            <div
                key={title}
                className="flex overflow-hidden rounded-card border border-ink/10 bg-surface-2"
            >
                <span className={cn("w-1 shrink-0", spine)} />
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2.5 px-3 py-2.5">
                        <Checkbox
                            checked={files.every((f) => selected.has(f.id))}
                            onChange={() => toggleGroup(files)}
                            label={`Select all in ${title}`}
                        />
                        <button
                            type="button"
                            onClick={() => toggleCollapse(title)}
                            className="flex min-w-0 flex-1 items-center gap-2 text-left"
                        >
                            <span className="truncate font-display text-sm text-ink">{title}</span>
                            <span className="rounded-full bg-ink/10 px-1.5 py-0.5 text-2xs text-ink-muted">
                                {files.length}
                            </span>
                            <span className="ml-auto text-ink-faint">
                                {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            </span>
                        </button>
                    </div>
                    {open && <div className="px-3 pb-3">{fileGrid(files)}</div>}
                </div>
            </div>
        );
    };

    const hasFiles = (data?.length ?? 0) > 0;
    const hasSelection = selected.size > 0;

    const menuItem = "w-full";

    return (
        <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-end gap-2">
                {uploading && <span className="mr-auto text-sm text-ink-muted">Uploading…</span>}

                <div className="relative">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setUploadOpen((v) => !v)}
                        disabled={uploading}
                    >
                        <Upload size={15} /> Upload <ChevronDown size={14} />
                    </Button>
                    <Popover
                        open={uploadOpen}
                        onClose={() => setUploadOpen(false)}
                        align="right"
                        className="w-44 p-2"
                    >
                        <div className="flex flex-col gap-1.5">
                            <Button
                                variant="secondary"
                                size="sm"
                                className={menuItem}
                                onClick={() => {
                                    setUploadOpen(false);
                                    filesInputRef.current?.click();
                                }}
                            >
                                <Upload size={15} /> Files
                            </Button>
                            <Button
                                variant="secondary"
                                size="sm"
                                className={menuItem}
                                onClick={() => {
                                    setUploadOpen(false);
                                    folderInputRef.current?.click();
                                }}
                            >
                                <FolderUp size={15} /> Folder
                            </Button>
                        </div>
                    </Popover>
                </div>

                <div className="relative">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setOptionsOpen((v) => !v)}
                        disabled={!hasSelection}
                    >
                        Options <ChevronDown size={14} />
                    </Button>
                    <Popover
                        open={optionsOpen}
                        onClose={() => setOptionsOpen(false)}
                        align="right"
                        className="w-44 p-2"
                    >
                        <div className="flex flex-col gap-1.5">
                            <Button
                                variant="secondary"
                                size="sm"
                                className={menuItem}
                                onClick={() => {
                                    setOptionsOpen(false);
                                    setDialogOpen(true);
                                }}
                            >
                                <Play size={15} /> Run Batch
                            </Button>
                            <Button
                                variant="secondary"
                                size="sm"
                                className={menuItem}
                                onClick={() => {
                                    setOptionsOpen(false);
                                    void deleteSelected();
                                }}
                            >
                                <Trash2 size={15} /> Delete Selected
                            </Button>
                            <Button
                                variant="secondary"
                                size="sm"
                                className={menuItem}
                                onClick={() => {
                                    setOptionsOpen(false);
                                    clearSelection();
                                }}
                            >
                                <X size={15} /> Clear
                            </Button>
                        </div>
                    </Popover>
                </div>

                <input
                    ref={filesInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={onPickFiles}
                />
                <input
                    ref={folderInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={onPickFolder}
                />
            </div>

            {isLoading && !data ? (
                <PanelLoading />
            ) : !hasFiles ? (
                <EmptyState
                    title="No Files"
                    description="Upload Files Or A Folder To Batch-Process Them"
                />
            ) : (
                <div className="space-y-4">
                    {groups.named.map(([name, files]) => renderTray(name, files, "bg-shu"))}
                    {groups.ungrouped &&
                        (groups.named.length > 0
                            ? renderTray("Ungrouped", groups.ungrouped, "bg-ink/20")
                            : fileGrid(groups.ungrouped))}
                </div>
            )}

            <BatchDialog
                open={dialogOpen}
                files={(data ?? []).filter((f) => selected.has(f.id))}
                onClose={() => setDialogOpen(false)}
                onSubmitted={clearSelection}
            />
        </div>
    );
}
