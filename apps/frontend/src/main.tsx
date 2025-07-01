/**
 * @fileoverview This is the entry point of the application.
 * It sets up the React application, including providers and routing.
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
