/**
 * @packageDocumentation This is the root component of the application.
 * It sets up the main layout and routing, and wraps the application
 * in necessary context providers.
 */

import React from "react";
import { Routes, Route } from "react-router-dom";
import NavigationMenu from "./components/NavigationMenu";
import HomePage from "./pages/HomePage";
import PlayerPage from "./pages/PlayerPage";
import TranscribePage from "./pages/TranscribePage";
import NotFoundPage from "./pages/NotFoundPage";
import UserPage from "./pages/UserPage";
import SavedPage from "./pages/SavedPage";
import TextPage from "./pages/TextPage";
import { DictionaryPage } from "./pages/DictionaryPage";
import { PlayerProvider } from "./contexts/PlayerContext";

/**
 * The main application component.
 *
 * It renders the navigation menu and sets up the routes for the different pages.
 * It also wraps the entire application in the `PlayerProvider` to make the player's
 * state globally accessible and persistent across navigation.
 * @returns {JSX.Element} The main application component.
 */
function App() {
    return (
        <PlayerProvider>
            <div className="flex flex-col h-screen">
                <NavigationMenu />
                <main className="flex-1 overflow-auto">
                    <Routes>
                        <Route path="/dashboard" element={<UserPage />} />
                        <Route path="/saved" element={<SavedPage />} />
                        <Route
                            path="/transcribe"
                            element={<TranscribePage />}
                        />
                        <Route path="/" element={<HomePage />} />
                        <Route path="/player" element={<PlayerPage />} />
                        <Route path="/text" element={<TextPage />} />
                        <Route
                            path="/dictionary"
                            element={<DictionaryPage />}
                        />
                        <Route path="*" element={<NotFoundPage />} />
                    </Routes>
                </main>
            </div>
        </PlayerProvider>
    );
}

export default App;
