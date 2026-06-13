/**
 * @packageDocumentation Context for the token bundling mode (Words / Grammar /
 * Morphemes), a client-side view preference persisted to localStorage and sent
 * to the server tokenizer on every request.
 */

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
    ReactNode,
} from "react";
import type { BundleMode } from "@/shared/dict/types";

const STORAGE_KEY = "bundleMode";
const DEFAULT_MODE: BundleMode = "grammar";
const MODES: BundleMode[] = ["words", "grammar", "morphemes"];

/**
 * @interface BundleSettingsContextType
 * Shape of the bundle-settings context.
 */
export interface BundleSettingsContextType {
    mode: BundleMode;
    setMode: (mode: BundleMode) => void;
    resetMode: () => void;
}

const BundleSettingsContext = createContext<BundleSettingsContextType | undefined>(undefined);

/**
 * A provider for the BundleSettingsContext.
 *
 * @param {{ children: ReactNode }} props The props for the component.
 * @returns {JSX.Element} The BundleSettingsProvider component.
 */
export const BundleSettingsProvider = ({ children }: { children: ReactNode }) => {
    const [mode, setModeState] = useState<BundleMode>(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored && MODES.includes(stored as BundleMode)
            ? (stored as BundleMode)
            : DEFAULT_MODE;
    });

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, mode);
        } catch (error) {
            console.error("Failed to save bundle mode to localStorage", error);
        }
    }, [mode]);

    const setMode = useCallback((next: BundleMode) => setModeState(next), []);

    const resetMode = useCallback(() => setModeState(DEFAULT_MODE), []);

    const value = useMemo(() => ({ mode, setMode, resetMode }), [mode, setMode, resetMode]);

    return (
        <BundleSettingsContext.Provider value={value}>{children}</BundleSettingsContext.Provider>
    );
};

/**
 * A hook for using the BundleSettingsContext.
 *
 * @returns {BundleSettingsContextType} The BundleSettingsContext.
 */
export const useBundleSettings = () => {
    const context = useContext(BundleSettingsContext);
    if (context === undefined) {
        throw new Error("useBundleSettings must be used within a BundleSettingsProvider");
    }
    return context;
};
