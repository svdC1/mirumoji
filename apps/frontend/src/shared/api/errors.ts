/**
 * @packageDocumentation API error type + toast helper, keyed off the server's
 * structured error envelope `{ success:false, error:{ code, message, details } }`.
 */

import toast from "react-hot-toast";

/**
 * An error thrown for non-2xx API responses. `code` is the server's
 * machine-readable identifier from the error envelope, when present.
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
        public code?: string,
        public details?: unknown
    ) {
        super(message);
        this.name = "ApiError";
    }
}

/** Friendly messages keyed by the server's machine-readable error `code`. */
const MESSAGE_BY_CODE: Record<string, string> = {
    LLMProviderUnavailable: "⚙️ LLM Provider Not Configured",
    InvalidModelString: "⚙️ Invalid Model Selector",
    LLMRequest: "🤖 The LLM Request Failed",
    RecordNotFound: "🔍 Could Not Find Resource",
    WhisperUnavailable: "🎤 No Transcription Backend Available",
    MissingFFmpeg: "🎬 FFmpeg Not Available On The Server",
    MissingFFprobe: "🎬 FFprobe Not Available On The Server",
    Upload: "⬆️ Upload Failed",
    Storage: "💾 The Server Failed To Store The File",
    Database: "💾 A Database Error Occurred",
};

/**
 * Displays an API error as a toast, preferring the server's machine-readable
 * `code` and falling back to the HTTP status.
 *
 * @param {unknown} err The error to display.
 * @param {string} [toastId] An existing toast id to update.
 */
export function toastApiError(err: unknown, toastId?: string) {
    const opts = toastId ? { id: toastId, duration: 5000 } : { duration: 5000 };

    if (err instanceof ApiError) {
        if (err.code && MESSAGE_BY_CODE[err.code]) {
            toast.error(MESSAGE_BY_CODE[err.code], opts);
            return;
        }
        switch (err.status) {
            case 403:
                toast.error("🚫 Not Allowed", opts);
                return;
            case 404:
                toast.error("🔍 Could Not Find Resource", opts);
                return;
            default:
                console.error(`API Error ${err.status}:`, err.message, err);
                toast.error(`⚠️ Server Error (${err.status})`, opts);
                return;
        }
    }

    console.error("Unexpected Error:", err);
    toast.error("⚠️ Unexpected Error", opts);
}
