/**
 * @packageDocumentation The root component: app shell (collapsible sidebar) +
 * routing, wrapped in the global PlayerProvider.
 */

import { Routes, Route, useLocation } from "react-router-dom";
import { PlayerProvider } from "@/contexts/PlayerContext";
import { AppSidebar } from "./shell/AppSidebar";
import HomePage from "@/pages/HomePage";
import PlayerPage from "@/features/player/PlayerPage";
import TranscribePage from "@/pages/TranscribePage";
import TextPage from "@/pages/TextPage";
import { DictionaryPage } from "@/pages/DictionaryPage";
import UserPage from "@/pages/UserPage";
import SavedPage from "@/pages/SavedPage";
import GuidePage from "@/features/guide/GuidePage";
import NotFoundPage from "@/pages/NotFoundPage";

/**
 * The main application component — shell + routes.
 *
 * @returns {JSX.Element} The app.
 */
export default function App() {
    const { pathname } = useLocation();
    // The Player is immersive: the sidebar hides behind a floating menu button.
    const immersive = pathname === "/player";

    return (
        <PlayerProvider>
            <AppSidebar immersive={immersive} />
            <div className={immersive ? "" : "pl-16"}>
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/player" element={<PlayerPage />} />
                    <Route path="/transcribe" element={<TranscribePage />} />
                    <Route path="/text" element={<TextPage />} />
                    <Route path="/dictionary" element={<DictionaryPage />} />
                    <Route path="/dashboard" element={<UserPage />} />
                    <Route path="/saved" element={<SavedPage />} />
                    <Route path="/guide" element={<GuidePage />} />
                    <Route path="*" element={<NotFoundPage />} />
                </Routes>
            </div>
        </PlayerProvider>
    );
}
