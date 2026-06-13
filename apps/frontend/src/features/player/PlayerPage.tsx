/**
 * @packageDocumentation The Player page: a video stage with overlay subtitles, a
 * collapsible subtitle-navigation panel, and a slim toolbar. Pulls media + style
 * from the global contexts so state persists across navigation.
 */

import { useEffect, useState } from "react";
import { Clapperboard } from "lucide-react";
import { usePlayer } from "@/contexts/PlayerContext";
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
}

/**
 * The PlayerPage component.
 *
 * @returns {JSX.Element} The player page.
 */
export default function PlayerPage() {
    const { video, videoUrl, srt, showFurigana, timestamp, setTimestamp } = usePlayer();
    // The video element via a callback ref, so effects bind exactly when it mounts.
    const [videoEl, setVideoEl] = useState<HTMLVideoElement | null>(null);

    const { cues, preparing } = useCues(srt);
    const activeIdx = useActiveCue(videoEl, cues);
    const activeCue = activeIdx != null ? cues[activeIdx] : null;

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

    // Restore the saved position on load; persist it on pause / source change.
    useEffect(() => {
        if (!videoEl || !blobUrl) return;
        const restore = () => {
            if (timestamp && timestamp > 0) videoEl.currentTime = timestamp;
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
        setDialog({
            sentence,
            word,
            cueStart: activeCue?.start ?? 0,
            cueEnd: activeCue?.end ?? 0,
        });
    };

    return (
        <div className="flex h-dvh flex-col bg-bg text-ink">
            <PlayerToolbar />

            <div className="flex min-h-0 flex-1 flex-col md:flex-row">
                {hasMedia ? (
                    <div className="min-h-0 min-w-0 flex-1">
                        <VideoStage
                            onVideoEl={setVideoEl}
                            blobUrl={blobUrl}
                            activeCue={activeCue}
                            showFurigana={showFurigana}
                            preparing={preparing}
                            onWordClick={onWordClick}
                        />
                    </div>
                ) : (
                    <div className="flex flex-1 items-center justify-center">
                        <EmptyState
                            icon={<Clapperboard size={32} />}
                            title="Load a video to begin"
                            description="Use the Load button in the toolbar to open a video and subtitles from your device or profile."
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
                    onClose={() => setDialog(null)}
                />
            )}
        </div>
    );
}
