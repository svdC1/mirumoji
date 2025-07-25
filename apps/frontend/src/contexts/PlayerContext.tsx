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
 * @property {File | null} video - The currently loaded video file.
 * @property {(file: File | null) => void} setVideo - Function to set the video file.
 * @property {File | null} srt - The currently loaded SRT subtitle file.
 * @property {(file: File | null) => void} setSrt - Function to set the SRT file.
 * @property {string | null} videoUrl - The URL of a video (used for profile-loaded or converted videos).
 * @property {(url: string | null) => void} setVideoUrl - Function to set the video URL.
 * @property {boolean} drawerOpen - The visibility state of the settings drawer.
 * @property {(open: boolean) => void} setDrawerOpen - Function to toggle the settings drawer.
 * @property {boolean} showFurigana - The visibility state of furigana on subtitles.
 * @property {(show: boolean) => void} setShowFurigana - Function to toggle furigana visibility.
 * @property {() => void} clearPlayerState - Function to reset the player state to its initial values.
 */
interface PlayerContextState {
    video: File | null;
    setVideo: (file: File | null) => void;
    srt: File | null;
    setSrt: (file: File | null) => void;
    videoUrl: string | null;
    setVideoUrl: (url: string | null) => void;
    drawerOpen: boolean;
    setDrawerOpen: (open: boolean) => void;
    showFurigana: boolean;
    setShowFurigana: (show: boolean) => void;
    clearPlayerState: () => void;
}

/**
 * The React Context object for the player state.
 */
const PlayerContext = createContext<PlayerContextState | undefined>(undefined);

/**
 * @interface PlayerProviderProps
 * Defines the props for the PlayerProvider component.
 * @property {ReactNode} children - The child components that the provider will wrap.
 */
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
    const [srt, setSrt] = useState<File | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [drawerOpen, setDrawerOpen] = useState(true);
    const [showFurigana, setShowFurigana] = useState<boolean>(true);

    /**
     * Resets all player-related state to their initial default values.
     * This function can be called to manually clear the player session.
     */
    const clearPlayerState = () => {
        setVideo(null);
        setSrt(null);
        setVideoUrl(null);
        setDrawerOpen(true); // Reset drawer to be open
        setShowFurigana(true);
    };

    const value = {
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
 * This hook simplifies accessing the context's state and ensures that the
 * consumer component is within a PlayerProvider.
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
