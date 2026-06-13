/**
 * @packageDocumentation This is the entry point of the application.
 * It sets up the React application, including providers and routing.
 * It also includes a fix for handling client-side routing on static hosting
 * services like GitHub Pages.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { SWRConfig } from "swr";
import App from "./app/App";
import "./assets/index.css";
import { Toaster } from "react-hot-toast";
import { ProfileProvider } from "./contexts/ProfileContext";
import { SubtitleSettingsProvider } from "./contexts/SubtitleSettingsContext";
import { BundleSettingsProvider } from "./contexts/BundleSettingsContext";

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
        {/* Cap error retries so a dead backend (e.g. the live demo with no
            server) doesn't storm requests; toasts are deduped by id regardless. */}
        <SWRConfig value={{ errorRetryCount: 2 }}>
            <ProfileProvider>
                <SubtitleSettingsProvider>
                    <BundleSettingsProvider>
                        <BrowserRouter basename={import.meta.env.BASE_URL}>
                            <App />
                        </BrowserRouter>
                    </BundleSettingsProvider>
                </SubtitleSettingsProvider>
            </ProfileProvider>
        </SWRConfig>
        <Toaster
            position="top-center"
            toastOptions={{
                duration: 4000,
                // "Sumi & Shu" surface + hairline + washi ink, so toasts blend
                // into the theme instead of the library's default white pills.
                style: {
                    background: "rgb(var(--surface))",
                    color: "rgb(var(--ink))",
                    border: "1px solid rgb(var(--ink) / 0.1)",
                    borderRadius: "var(--radius-card)",
                    boxShadow: "0 12px 32px -12px rgb(0 0 0 / 0.6)",
                    fontSize: "0.875rem",
                    padding: "0.6rem 0.85rem",
                    maxWidth: "24rem",
                },
                success: {
                    iconTheme: { primary: "rgb(var(--matcha))", secondary: "rgb(var(--surface))" },
                },
                error: {
                    iconTheme: { primary: "rgb(var(--danger))", secondary: "rgb(var(--surface))" },
                },
                loading: {
                    iconTheme: { primary: "rgb(var(--shu))", secondary: "rgb(var(--surface))" },
                },
            }}
        />
    </React.StrictMode>
);
