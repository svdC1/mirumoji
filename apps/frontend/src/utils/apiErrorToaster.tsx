/**
 * @packageDocumentation This file contains a function for displaying API errors as toasts.
 */

import toast from "react-hot-toast";
import { ApiError } from "../types/types";

/**
 * Friendly messages keyed by the server's machine-readable error `code`.
 */
const MESSAGE_BY_CODE: Record<string, string> = {
    LLMProviderUnavailable: "⚙️ LLM provider not configured",
    InvalidModelString: "⚙️ Invalid model selector",
    LLMRequest: "🤖 The LLM request failed",
    RecordNotFound: "🔍 Could Not Find Resource",
    WhisperUnavailable: "🎤 No transcription backend available",
    MissingFFmpeg: "🎬 FFmpeg is not available on the server",
    MissingFFprobe: "🎬 FFprobe is not available on the server",
    Upload: "⬆️ Upload failed",
    Storage: "💾 The server failed to store the file",
    Database: "💾 A database error occurred",
};

/**
 * Displays an API error as a toast.
 *
 * Prefers the server's machine-readable `code` from the error envelope, and
 * falls back to the HTTP status when the code is unknown.
 *
 * @param {unknown} err The error to display.
 * @param {string} [toastId] The ID of the toast to update.
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

    // For non-ApiError types or if err is not an instance of ApiError
    console.error("Unexpected Error:", err);
    toast.error("⚠️ Unexpected Error", opts);
}
