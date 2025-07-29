/**
 * @packageDocumentation This file provides a context for managing the user's profile.
 */

import React, {
    createContext,
    useContext,
    useState,
    useEffect,
    ReactNode,
} from "react";

/**
 * The context for managing the user's profile.
 *
 * @property {string | null} profileId The ID of the current profile.
 * @property {(id: string | null) => void} setProfileId A function for setting the current profile ID.
 */
export interface ProfileContextType {
    profileId: string | null;
    setProfileId: (id: string | null) => void;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

/**
 * A provider for the ProfileContext.
 *
 * @param {{ children: ReactNode }} props The props for the component.
 * @returns {JSX.Element} The ProfileProvider component.
 */
export const ProfileProvider: React.FC<{ children: ReactNode }> = ({
    children,
}) => {
    const [profileId, setProfileIdState] = useState<string | null>(() => {
        return localStorage.getItem("currentProfileId");
    });

    useEffect(() => {
        if (profileId) {
            localStorage.setItem("currentProfileId", profileId);
        } else {
            localStorage.removeItem("currentProfileId");
        }
    }, [profileId]);

    const setProfileId = (id: string | null) => {
        setProfileIdState(id);
    };

    return (
        <ProfileContext.Provider value={{ profileId, setProfileId }}>
            {children}
        </ProfileContext.Provider>
    );
};

/**
 * A hook for using the ProfileContext.
 *
 * @returns {ProfileContextType} The ProfileContext.
 */
export const useProfile = (): ProfileContextType => {
    const context = useContext(ProfileContext);
    if (context === undefined) {
        throw new Error("useProfile must be used within a ProfileProvider");
    }
    return context;
};
