/**
 * @fileoverview This component is the player page of the application.
 * It integrates the settings drawer and the main subtitle player, using the
 * global PlayerContext to manage and persist player state across navigation.
 */

import React from "react";
import SubtitlePlayer from "../components/SubtitlePlayer";
import SettingsDrawer from "../components/SettingsDrawer";
import { usePlayer } from "../contexts/PlayerContext";
import { Menu } from "lucide-react";

/**
 * The PlayerPage component.
 *
 * This component serves as the main container for the video player experience.
 * It sources its state from the `PlayerContext` and passes the necessary state
 * and actions down to the `SettingsDrawer` and `SubtitlePlayer` components.
 *
 * @returns {JSX.Element} The PlayerPage component.
 */
export default function PlayerPage() {
    const {
        video,
        setVideo,
        srt,
        setSrt,
        videoUrl,
        setVideoUrl,
        drawerOpen,
        setDrawerOpen,
        showFurigana,
        setShowFurigana,
    } = usePlayer();

    return (
        <div className="h-screen w-screen flex flex-col bg-black text-white">
            {/* Top Bar */}
            <header className="flex items-center gap-2 p-2">
                <button
                    className="p-2 hover:bg-white/10 rounded"
                    onClick={() => setDrawerOpen(!drawerOpen)}
                >
                    <Menu size={20} />
                </button>
                <h1 className="text-lg font-semibold text-center flex-1">
                    Mirumoji Player
                </h1>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Drawer */}
                {drawerOpen && (
                    <SettingsDrawer
                        video={video}
                        srt={srt}
                        onVideo={(file) => {
                            setVideo(file);
                            setVideoUrl(null);
                        }}
                        onVideoUrl={setVideoUrl}
                        onSrt={setSrt}
                        onClose={() => setDrawerOpen(false)}
                        showFurigana={showFurigana}
                        onToggleFurigana={() => setShowFurigana(!showFurigana)}
                    />
                )}

                {/* Video Area */}
                <main className="flex-1 flex items-center justify-center overflow-hidden p-2">
                    {video || videoUrl ? (
                        <SubtitlePlayer
                            video={video!}
                            videoUrl={videoUrl || undefined}
                            srt={srt}
                            showFurigana={showFurigana}
                        />
                    ) : (
                        <p className="text-gray-400">
                            Load a video from the menu ☰ to begin.
                        </p>
                    )}
                </main>
            </div>
        </div>
    );
}
