// src/components/NavigationMenu.tsx
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
    Bars3Icon,
    XMarkIcon,
    UserCircleIcon,
} from "@heroicons/react/24/outline";
import { useProfile } from "../contexts/ProfileContext";

export default function NavigationMenu() {
    const { profileId, setProfileId } = useProfile();
    const [open, setOpen] = useState(false);
    const [profileInput, setProfileInput] = useState(profileId || "");

    useEffect(() => {
        setProfileInput(profileId || "");
    }, [profileId]);

    const handleSetProfile = () => {
        if (profileInput.trim()) {
            setProfileId(profileInput.trim());
        } else {
            setProfileId(null);
        }
    };

    return (
        <>
            {/* Hamburger button */}
            <button
                onClick={() => setOpen(true)}
                className="
          fixed top-4 right-4 z-50 p-2 bg-white dark:bg-gray-800 shadow-md
          rounded-full focus:outline-none focus:ring transition-opacity duration-200
          opacity-50 hover:opacity-100 focus:opacity-100
        "
            >
                <Bars3Icon className="w-6 h-6 text-gray-700 dark:text-gray-200" />
            </button>

            {/* Backdrop */}
            <div
                className={`
          fixed inset-0 bg-black/60 z-40 transition-opacity
          ${open ? "opacity-100" : "opacity-0 pointer-events-none"}
        `}
                onClick={() => setOpen(false)}
            />

            {/* Side panel */}
            <aside
                className={`
          fixed top-0 right-0 z-50 h-full w-72  /* Increased width for profile input */
          bg-gray-800 dark:bg-gray-900 shadow-lg
          transform transition-transform
          ${open ? "translate-x-0" : "translate-x-full"}
        `}
            >
                {/* Header */}
                <div className="relative flex items-center justify-between h-16 border-b border-gray-700 px-4">
                    <span className="text-lg font-semibold text-white">
                        Menu
                    </span>
                    <button
                        onClick={() => setOpen(false)}
                        className="p-2 rounded-full focus:outline-none focus:ring hover:bg-gray-700"
                    >
                        <XMarkIcon className="w-6 h-6 text-white" />
                    </button>
                </div>

                {/* Profile Section */}
                <div className="px-4 py-3 border-b border-gray-700 space-y-2">
                    <div className="flex items-center bg-gray-700 dark:bg-gray-800 px-3 py-2 rounded-md">
                        <UserCircleIcon className="w-5 h-5 text-gray-300 flex-shrink-0" />
                        {profileId ? (
                            <span className="ml-2 text-sm text-white truncate">
                                Profile: {profileId}
                            </span>
                        ) : (
                            <span className="ml-2 text-sm text-gray-300">
                                No active profile
                            </span>
                        )}
                    </div>
                    <input
                        type="text"
                        value={profileInput}
                        onChange={(e) => setProfileInput(e.target.value)}
                        placeholder="Enter Profile Name"
                        className="w-full px-3 py-2 text-sm text-white bg-gray-700 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                    <button
                        onClick={handleSetProfile}
                        className="w-full px-3 py-2 text-sm rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none"
                    >
                        Save
                    </button>
                    {profileId && (
                        <button
                            onClick={() => {
                                setProfileId(null);
                                setProfileInput("");
                            }}
                            className="w-full mt-1 px-3 py-2 text-sm rounded-md text-white bg-red-600 hover:bg-red-500 focus:outline-none"
                        >
                            Clear Profile
                        </button>
                    )}
                </div>

                {/* Navigation */}
                <nav className="flex flex-col justify-between flex-grow p-4 space-y-2">
                    <div className="space-y-2">
                        <Link
                            to="/"
                            onClick={() => setOpen(false)}
                            className="w-full text-center px-3 py-2 rounded-md text-white transition-all duration-200 hover:bg-gray-700 block"
                        >
                            Home
                        </Link>
                        <Link
                            to="/player"
                            onClick={() => setOpen(false)}
                            className="w-full text-center px-3 py-2 rounded-md text-white transition-all duration-200 hover:bg-gray-700 block"
                        >
                            Player
                        </Link>
                        <Link
                            to="/transcribe"
                            onClick={() => setOpen(false)}
                            className="w-full text-center px-3 py-2 rounded-md text-white transition-all duration-200 hover:bg-gray-700 block"
                        >
                            Transcribe
                        </Link>
                        <Link
                            to="/dashboard"
                            onClick={() => setOpen(false)}
                            className="w-full text-center px-3 py-2 rounded-md text-white transition-all duration-200 hover:bg-gray-700 block"
                        >
                            Profile
                        </Link>
                        <Link
                            to="/saved"
                            onClick={() => setOpen(false)}
                            className="w-full text-center px-3 py-2 rounded-md text-white transition-all duration-200 hover:bg-gray-700 block"
                        >
                            Saved Clips
                        </Link>
                    </div>
                </nav>
            </aside>
        </>
    );
}
