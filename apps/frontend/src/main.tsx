import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { Toaster } from "react-hot-toast";
import { ProfileProvider } from "./contexts/ProfileContext";
import { SubtitleSettingsProvider } from "./contexts/SubtitleSettingsContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <ProfileProvider>
            <SubtitleSettingsProvider>
                <BrowserRouter>
                    <App />
                </BrowserRouter>
            </SubtitleSettingsProvider>
        </ProfileProvider>
        <Toaster position="top-center" />
    </React.StrictMode>
);
