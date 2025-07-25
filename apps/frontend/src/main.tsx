/**
 * @fileoverview This is the entry point of the application.
 * It sets up the React application, including providers and routing.
 * It also includes a fix for handling client-side routing on static hosting
 * services like GitHub Pages.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./assets/index.css";
import { Toaster } from "react-hot-toast";
import { ProfileProvider } from "./contexts/ProfileContext";
import { SubtitleSettingsProvider } from "./contexts/SubtitleSettingsContext";

/**
 * Fix for GitHub Pages and other static hosts.
 * When a user refreshes on a nested path (e.g., /player), the server returns a 404.
 * We configure the server to serve a 404.html file which redirects to the root.
 * This script then reads the intended path from sessionStorage and uses the History API
 * to restore the correct URL before the router initializes.
 */
(function () {
    const redirectPath = sessionStorage.getItem("redirectPath");
    if (redirectPath && redirectPath !== window.location.pathname) {
        window.history.replaceState(null, "", redirectPath);
        sessionStorage.removeItem("redirectPath");
    }
})();

/**
 * The root of the application.
 *
 * It sets up the following:
 * - React.StrictMode for highlighting potential problems in an application.
 * - ProfileProvider for managing user profiles.
 * - SubtitleSettingsProvider for managing subtitle settings.
 * - BrowserRouter for handling routing.
 * - Toaster for displaying notifications.
 */
ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <ProfileProvider>
            <SubtitleSettingsProvider>
                <BrowserRouter basename={import.meta.env.BASE_URL}>
                    <App />
                </BrowserRouter>
            </SubtitleSettingsProvider>
        </ProfileProvider>
        <Toaster position="top-center" />
    </React.StrictMode>
);
