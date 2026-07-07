/**
 * @packageDocumentation The Player page: a video stage with overlay subtitles, a
 * collapsible subtitle-navigation panel, and a slim toolbar. Pulls media + style
 * from the global contexts so state persists across navigation.
 */

import { useEffect, useState } from "react";
import { Clapperboard, Loader2 } from "lucide-react";
import { toast } from "react-hot-toast";
import { usePlayer } from "@/contexts/PlayerContext";
import { useOperationSettings } from "@/contexts/OperationSettingsContext";
import WordDialog from "@/shared/components/WordDialog";
import { EmptyState } from "@/shared/ui";
import { useCues } from "./hooks/useCues";
import { useActiveCue } from "./hooks/useActiveCue";
import { VideoStage } from "./components/VideoStage";
import { SubtitlePanel } from "./components/SubtitlePanel";
import { PlayerToolbar } from "./components/PlayerToolbar";

interface DialogState {
    sentence: string;
    word: string;
    cueStart: number;
    cueEnd: number;
    context?: string;
}

/**
 * The PlayerPage component.
 *
 * @returns {JSX.Element} The player page.
 */
export default function PlayerPage() {
    const {
        video,
        videoUrl,
        videoFileId,
        setVideo,
        setVideoUrl,
        setVideoFileName,
        setVideoFileId,
        srt,
        showFurigana,
        timestamp,
        setTimestamp,
    } = usePlayer();
    // The video element via a callback ref, so effects bind exactly when it mounts.
    const [videoEl, setVideoEl] = useState<HTMLVideoElement | null>(null);
    // A loaded source this browser can't decode (e.g. .mkv on iOS, which Chrome
    // desktop plays fine). We don't guess from the extension; we let it try and
    // flag it on the actual error, so the prompt only shows when truly needed.
    const [unplayable, setUnplayable] = useState(false);
    // True while the element is fetching/decoding a source (before it can show a
    // frame or fails), so a slow or undecodable source reads as "loading" rather
    // than a dead black box.
    const [loading, setLoading] = useState(false);

    const { cues, preparing } = useCues(srt);
    const activeIdx = useActiveCue(videoEl, cues);
    const activeCue = activeIdx != null ? cues[activeIdx] : null;
    const { settings } = useOperationSettings();

    const [panelCollapsed, setPanelCollapsed] = useState(false);
    const [dialog, setDialog] = useState<DialogState | null>(null);

    const hasMedia = !!(video || videoUrl);

    // Single source of truth for the blob URL (avoids the double-effect /
    // video.load() thrash that caused flicker). Changing `src` reloads the video.
    const [blobUrl, setBlobUrl] = useState<string | null>(null);
    useEffect(() => {
        if (videoUrl) {
            setBlobUrl(videoUrl);
            return;
        }
        if (video) {
            const url = URL.createObjectURL(video);
            setBlobUrl(url);
            return () => URL.revokeObjectURL(url);
        }
        setBlobUrl(null);
    }, [video, videoUrl]);

    // A fresh source gets a clean attempt: clear any prior "can't decode" flag
    // and show the loading state until it proves itself (or fails).
    useEffect(() => {
        setUnplayable(false);
        setLoading(!!(video || videoUrl));
    }, [video, videoUrl]);

    // Hide the loading state once the element shows signs of life (metadata,
    // first frame, or playback) or fails. Several events are watched because
    // browsers that defer loading (iOS) may fire one but not another.
    useEffect(() => {
        if (!videoEl) return;
        const ready = () => setLoading(false);
        const events = ["loadedmetadata", "loadeddata", "canplay", "playing", "error"];
        events.forEach((e) => videoEl.addEventListener(e, ready));
        if (videoEl.readyState >= 1 || videoEl.error) ready();
        return () => events.forEach((e) => videoEl.removeEventListener(e, ready));
    }, [videoEl]);

    // Whether a container decodes is runtime + browser specific (Chrome desktop
    // plays .mkv, iOS Safari can't), so we try to play and react to the actual
    // error rather than guessing from the extension. A file the browser can't
    // match to a decoder fails with SRC_NOT_SUPPORTED, while one it starts
    // decoding and then chokes on fails with DECODE, and both mean "can't play
    // here". A convertible source stays loaded so it can be converted to MP4
    // from the toolbar, and a bare URL that is simply gone is dropped.
    useEffect(() => {
        if (!videoEl) return;
        const onError = () => {
            const err = videoEl.error;
            if (
                !err ||
                (err.code !== err.MEDIA_ERR_SRC_NOT_SUPPORTED && err.code !== err.MEDIA_ERR_DECODE)
            ) {
                return;
            }
            if (video || videoFileId) {
                setUnplayable(true);
                return;
            }
            toast.error("This Video Is No Longer Available");
            setVideo(null);
            setVideoUrl(null);
            setVideoFileName(null);
            setVideoFileId(null);
        };
        videoEl.addEventListener("error", onError);
        // The element may have already failed before this listener attached
        // (a fast local blob, or a source set before the effect ran).
        if (videoEl.error) onError();
        return () => videoEl.removeEventListener("error", onError);
    }, [videoEl, video, videoFileId, setVideo, setVideoUrl, setVideoFileName, setVideoFileId]);

    // Restore the saved position on load; persist it on pause / source change.
    useEffect(() => {
        if (!videoEl || !blobUrl) return;
        const restore = () => {
            // Only resume within the new video's bounds; an out-of-range saved
            // position (a shorter video) starts from the beginning instead.
            const dur = videoEl.duration;
            if (timestamp && timestamp > 0 && (!Number.isFinite(dur) || timestamp <= dur)) {
                videoEl.currentTime = timestamp;
            }
        };
        const save = () => setTimestamp(videoEl.currentTime);
        videoEl.addEventListener("loadedmetadata", restore, { once: true });
        videoEl.addEventListener("pause", save);
        return () => {
            videoEl.removeEventListener("loadedmetadata", restore);
            videoEl.removeEventListener("pause", save);
            save();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [videoEl, blobUrl]);

    const seek = (seconds: number) => {
        if (!videoEl) return;
        videoEl.currentTime = seconds;
        videoEl.play?.().catch(() => undefined);
    };

    const onWordClick = (sentence: string, word: string) => {
        // Surrounding-subtitle context around the active cue. It is always
        // built and passed, but only a template that references {context}
        // actually uses it, so opting in is a template choice, not a toggle.
        const n = settings.breakdownContextWindow;
        const context =
            n > 0 && activeIdx != null
                ? cues
                      .slice(Math.max(0, activeIdx - n), activeIdx + n + 1)
                      .map((c) => c.raw)
                      .join("\n")
                : undefined;
        setDialog({
            sentence,
            word,
            cueStart: activeCue?.start ?? 0,
            cueEnd: activeCue?.end ?? 0,
            context,
        });
    };

    return (
        <div className="flex h-dvh flex-col bg-bg text-ink">
            <PlayerToolbar />

            <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
                {hasMedia && !unplayable ? (
                    <div className="relative min-h-0 min-w-0 flex-1">
                        <VideoStage
                            onVideoEl={setVideoEl}
                            blobUrl={blobUrl}
                            activeCue={activeCue}
                            showFurigana={showFurigana}
                            preparing={preparing}
                            onWordClick={onWordClick}
                        />
                        {loading && (
                            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                                <span className="inline-flex items-center gap-2 rounded-control bg-surface/90 px-3 py-1.5 text-xs font-medium text-ink-muted shadow-soft ring-1 ring-ink/10 backdrop-blur">
                                    <Loader2 size={14} className="animate-spin text-shu" />
                                    Loading Video
                                </span>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-1 items-center justify-center">
                        <EmptyState
                            icon={<Clapperboard size={32} />}
                            title={unplayable ? "Convert To Play" : "Load a video to begin"}
                            description={
                                unplayable
                                    ? "This browser can't play this video format. Use To MP4 in the toolbar to convert it, and it will load here automatically."
                                    : "Use the Load button in the toolbar to open a video and subtitles from your device or profile."
                            }
                        />
                    </div>
                )}

                <SubtitlePanel
                    cues={cues}
                    activeIdx={activeIdx}
                    collapsed={panelCollapsed}
                    onToggle={() => setPanelCollapsed((v) => !v)}
                    onSeek={seek}
                />
            </div>

            {dialog && (
                <WordDialog
                    sentence={dialog.sentence}
                    word={dialog.word}
                    cueStart={dialog.cueStart}
                    cueEnd={dialog.cueEnd}
                    videoFile={video}
                    videoUrl={videoUrl || undefined}
                    context={dialog.context}
                    onClose={() => setDialog(null)}
                />
            )}
        </div>
    );
}
