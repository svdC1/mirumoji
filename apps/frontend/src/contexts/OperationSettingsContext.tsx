/**
 * @packageDocumentation Profile-scoped operation settings: the curated Whisper
 * transcription options, the default `clean_audio` flag, and the conversion
 * options that the single-op and batch flows send to the server. Persisted per
 * profile in localStorage. An unset Whisper field is omitted from requests, so
 * the server keeps its own tuned default rather than being overridden.
 */

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
    ReactNode,
} from "react";
import { useProfile } from "./ProfileContext";
import type { ConvertOpts, TranscribeOpts } from "@/shared/jobs/types";

/** The full client-side operation settings for one profile. */
export interface OperationSettings {
    /** Curated Whisper opts, shared by `transcribe` and `generate_srt`. */
    transcribe: TranscribeOpts;
    /** Default `clean_audio` for `transcribe` jobs. */
    cleanAudio: boolean;
    /** Conversion opts for `convert` jobs. */
    convert: ConvertOpts;
    /**
     * Subtitle lines each side of the active cue sent to a word breakdown as
     * `{context}` (only used by a template that references it).
     */
    breakdownContextWindow: number;
}

const STORAGE_PREFIX = "operationSettings";

/**
 * A fresh copy of the defaults: everything unset, so every operation falls back
 * to the server's own tuned default until the user overrides it.
 */
export function defaultOperationSettings(): OperationSettings {
    return {
        transcribe: {},
        cleanAudio: false,
        convert: {},
        breakdownContextWindow: 3,
    };
}

function storageKey(profileId: string | null): string {
    return `${STORAGE_PREFIX}:${profileId ?? "default"}`;
}

function load(profileId: string | null): OperationSettings {
    const base = defaultOperationSettings();
    try {
        const raw = localStorage.getItem(storageKey(profileId));
        if (!raw) return base;
        const parsed = JSON.parse(raw) as Partial<OperationSettings>;
        return {
            transcribe: { ...base.transcribe, ...parsed.transcribe },
            cleanAudio: parsed.cleanAudio ?? base.cleanAudio,
            convert: { ...base.convert, ...parsed.convert },
            breakdownContextWindow: parsed.breakdownContextWindow ?? base.breakdownContextWindow,
        };
    } catch {
        return base;
    }
}

/** Drops `undefined` / empty-string entries so unset fields use server defaults. */
function compact(obj: Record<string, unknown>): Record<string, unknown> {
    return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined && v !== ""));
}

/**
 * @interface OperationSettingsContextType
 * Shape of the operation-settings context.
 */
export interface OperationSettingsContextType {
    settings: OperationSettings;
    /** Commits a new settings object (persists it for the active profile). */
    replace: (next: OperationSettings) => void;
    /**
     * The curated Whisper opts (unset fields dropped), shared by `transcribe`
     * and `generate_srt`. Callers add `clean_audio` for `transcribe`.
     */
    whisperOpts: () => Record<string, unknown>;
    /** Opts payload for a `convert` job. */
    convertOpts: () => Record<string, unknown>;
}

const OperationSettingsContext = createContext<OperationSettingsContextType | undefined>(undefined);

/**
 * A provider for the OperationSettingsContext.
 *
 * @param {{ children: ReactNode }} props The provider children.
 * @returns {JSX.Element} The provider.
 */
export const OperationSettingsProvider = ({ children }: { children: ReactNode }) => {
    const { profileId } = useProfile();
    const [settings, setSettings] = useState<OperationSettings>(() => load(profileId));

    // The profile the in-memory settings belong to, and a one-shot flag so the
    // reload that follows a profile switch does not persist back over the
    // freshly-loaded values.
    const profileRef = useRef(profileId);
    const skipPersist = useRef(false);

    // Reload when the active profile changes (skips the initial mount, which the
    // useState initializer already loaded for).
    useEffect(() => {
        if (profileRef.current === profileId) return;
        profileRef.current = profileId;
        skipPersist.current = true;
        setSettings(load(profileId));
    }, [profileId]);

    // Persist edits to the active profile's key.
    useEffect(() => {
        if (skipPersist.current) {
            skipPersist.current = false;
            return;
        }
        try {
            localStorage.setItem(storageKey(profileRef.current), JSON.stringify(settings));
        } catch (error) {
            console.error("Failed to save operation settings", error);
        }
    }, [settings]);

    const replace = useCallback((next: OperationSettings) => setSettings(next), []);

    const whisperOpts = useCallback(() => compact({ ...settings.transcribe }), [settings]);
    const convertOpts = useCallback(() => compact({ ...settings.convert }), [settings]);

    const value = useMemo(
        () => ({ settings, replace, whisperOpts, convertOpts }),
        [settings, replace, whisperOpts, convertOpts]
    );

    return (
        <OperationSettingsContext.Provider value={value}>
            {children}
        </OperationSettingsContext.Provider>
    );
};

/**
 * Hook for consuming the operation-settings context.
 *
 * @returns {OperationSettingsContextType} The operation-settings context.
 */
export const useOperationSettings = (): OperationSettingsContextType => {
    const ctx = useContext(OperationSettingsContext);
    if (ctx === undefined) {
        throw new Error("useOperationSettings must be used within an OperationSettingsProvider");
    }
    return ctx;
};
