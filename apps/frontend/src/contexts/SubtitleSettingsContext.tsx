/**
 * @packageDocumentation This file provides a context for managing the subtitle settings.
 */

import React, {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback,
    useMemo,
    ReactNode,
} from "react";

/**
 * The shape of the subtitle style settings.
 */
export interface SubtitleStyle {
    fontSize: number;
    fontColor: string;
    backgroundColor: string;
    backgroundOpacity: number;
    textShadow: string;
    position: number;
}

/**
 * @interface SubtitleSettingsContextType
 * Shape of the Subtitle Settings Context
 */
export interface SubtitleSettingsContextType {
    subtitleStyle: SubtitleStyle;
    setSubtitleStyle: (style: SubtitleStyle) => void;
    resetSubtitleStyle: () => void;
}

// Define default styles
const defaultSubtitleStyle: SubtitleStyle = {
    fontSize: 24,
    fontColor: "#FFFFFF",
    backgroundColor: "#000000",
    backgroundOpacity: 0.5,
    textShadow: "1px 1px 2px black",
    position: 5,
};

// Create the context with a default value
const SubtitleSettingsContext = createContext<SubtitleSettingsContextType | undefined>(undefined);

/**
 * A provider for the SubtitleSettingsContext.
 *
 * @param {{ children: ReactNode }} props The props for the component.
 * @returns {JSX.Element} The SubtitleSettingsProvider component.
 */
export const SubtitleSettingsProvider = ({ children }: { children: ReactNode }) => {
    const [subtitleStyle, setSubtitleStyleState] = useState<SubtitleStyle>(() => {
        try {
            const storedStyle = localStorage.getItem("subtitleStyle");
            return storedStyle ? JSON.parse(storedStyle) : defaultSubtitleStyle;
        } catch (error) {
            console.error("Failed to parse subtitle style from localStorage", error);
            return defaultSubtitleStyle;
        }
    });

    useEffect(() => {
        try {
            localStorage.setItem("subtitleStyle", JSON.stringify(subtitleStyle));
        } catch (error) {
            console.error("Failed to save subtitle style to localStorage", error);
        }
    }, [subtitleStyle]);

    const setSubtitleStyle = useCallback((newStyle: SubtitleStyle) => {
        setSubtitleStyleState(newStyle);
    }, []);

    const resetSubtitleStyle = useCallback(() => {
        setSubtitleStyleState(defaultSubtitleStyle);
    }, []);

    const value = useMemo(
        () => ({ subtitleStyle, setSubtitleStyle, resetSubtitleStyle }),
        [subtitleStyle, setSubtitleStyle, resetSubtitleStyle]
    );

    return (
        <SubtitleSettingsContext.Provider value={value}>
            {children}
        </SubtitleSettingsContext.Provider>
    );
};

/**
 * A hook for using the SubtitleSettingsContext.
 *
 * @returns {SubtitleSettingsContextType} The SubtitleSettingsContext.
 */
export const useSubtitleSettings = () => {
    const context = useContext(SubtitleSettingsContext);
    if (context === undefined) {
        throw new Error("useSubtitleSettings must be used within a SubtitleSettingsProvider");
    }
    return context;
};
