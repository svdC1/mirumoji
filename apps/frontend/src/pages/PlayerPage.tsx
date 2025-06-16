import React, { useState } from "react";
import SubtitlePlayer from "../components/SubtitlePlayer";
import SettingsDrawer from "../components/SettingsDrawer";
import { Menu } from "lucide-react";

export default function PlayerPage() {
    const [video, setVideo] = useState<File | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [srt, setSrt] = useState<File | null>(null);
    const [drawerOpen, setDrawerOpen] = useState(true);
    const [showFurigana, setShowFurigana] = useState<boolean>(true);

    return (
        <div className="h-screen w-screen flex flex-col bg-black text-white">
            {/* top bar */}
            <header className="flex items-center gap-2 p-2">
                <button
                    className="p-2 hover:bg-white/10 rounded"
                    onClick={() => setDrawerOpen((o) => !o)}
                >
                    <Menu size={20} />
                </button>
                <h1 className="text-lg font-semibold">Mirumoji</h1>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* drawer */}
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
                        onToggleFurigana={() =>
                            setShowFurigana((prev) => !prev)
                        }
                    />
                )}

                {/* video area */}
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
