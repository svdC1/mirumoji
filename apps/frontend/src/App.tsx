import React from "react"; // Assuming useEffect is no longer needed
import { Routes, Route } from "react-router-dom"; // Assuming useLocation is no longer needed
import NavigationMenu from "./components/NavigationMenu";
import HomePage from "./pages/HomePage";
import PlayerPage from "./pages/PlayerPage";
import TranscribePage from "./pages/TranscribePage";
import NotFoundPage from "./pages/NotFoundPage";
import UserPage from "./pages/UserPage";
import SavedPaged from "./pages/SavedPage";


function App() {
    return (
        <div className="flex flex-col h-screen">
            <NavigationMenu />
            <main className="flex-1 overflow-auto">
                <Routes>
                    <Route path="/dashboard" element={<UserPage />} />
                    <Route path="/saved" element={<SavedPaged />} />
                    <Route path="/transcribe" element={<TranscribePage />} />
                    <Route path="/" element={<HomePage />} />
                    <Route path="/player" element={<PlayerPage />} />
                    <Route path="*" element={<NotFoundPage />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;
