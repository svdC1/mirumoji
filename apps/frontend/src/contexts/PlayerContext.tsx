/**
 * @fileoverview This file defines the context for managing the state of the video player.
 * It allows the player's state (e.g., loaded video, subtitles, settings) to persist
 * across component mounts and unmounts, enabling navigating
 * between pages.
 */

import React, { createContext, useContext, useState, ReactNode } from "react";

/**
 * @interface PlayerContextState
 * Defines the shape of the data stored in the PlayerContext.
 */
interface PlayerContextState {
    video: File | null;
    setVideo: (file: File | null) => void;
    videoFileName: string | null;
    setVideoFileName: (name: string | null) => void;
    srt: File | null;
    setSrt: (file: File | null) => void;
    srtFileName: string | null;
    setSrtFileName: (name: string | null) => void;
    videoUrl: string | null;
    setVideoUrl: (url: string | null) => void;
    drawerOpen: boolean;
    setDrawerOpen: (open: boolean) => void;
    showFurigana: boolean;
    setShowFurigana: (show: boolean) => void;
    clearPlayerState: () => void;
}

const PlayerContext = createContext<PlayerContextState | undefined>(undefined);

interface PlayerProviderProps {
    children: ReactNode;
}

/**
 * The provider component that supplies the PlayerContext to its children.
 * It encapsulates the state logic and provides the state and action functions to its descendants.
 * @param {PlayerProviderProps} props - The props for the component.
 * @returns {JSX.Element} The provider component.
 */
export const PlayerProvider: React.FC<PlayerProviderProps> = ({ children }) => {
    const [video, setVideo] = useState<File | null>(null);
    const [videoFileName, setVideoFileName] = useState<string | null>(null);
    const [srt, setSrt] = useState<File | null>(null);
    const [srtFileName, setSrtFileName] = useState<string | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [drawerOpen, setDrawerOpen] = useState(true);
    const [showFurigana, setShowFurigana] = useState<boolean>(true);

    /**
     * Resets all player-related state to their initial default values.
     */
    const clearPlayerState = () => {
        setVideo(null);
        setVideoFileName(null);
        setSrt(null);
        setSrtFileName(null);
        setVideoUrl(null);
        setDrawerOpen(true);
        setShowFurigana(true);
    };

    const value = {
        video,
        setVideo,
        videoFileName,
        setVideoFileName,
        srt,
        setSrt,
        srtFileName,
        setSrtFileName,
        videoUrl,
        setVideoUrl,
        drawerOpen,
        setDrawerOpen,
        showFurigana,
        setShowFurigana,
        clearPlayerState,
    };

    return (
        <PlayerContext.Provider value={value}>
            {children}
        </PlayerContext.Provider>
    );
};

/**
 * A custom hook for consuming the PlayerContext.
 * @throws {Error} If the hook is used outside of a PlayerProvider.
 * @returns {PlayerContextState} The state and actions from the PlayerContext.
 */
export const usePlayer = (): PlayerContextState => {
    const context = useContext(PlayerContext);
    if (context === undefined) {
        throw new Error("usePlayer must be used within a PlayerProvider");
    }
    return context;
};
