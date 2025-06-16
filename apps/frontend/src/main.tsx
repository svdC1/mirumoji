import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { Toaster } from "react-hot-toast";
import { ProfileProvider } from "./contexts/ProfileContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <ProfileProvider>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </ProfileProvider>
        <Toaster position="top-center" />
    </React.StrictMode>
);
