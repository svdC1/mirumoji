/**
 * @packageDocumentation API error type + toast helper, keyed off the server's
 * structured error envelope `{ success:false, error:{ code, message, details } }`.
 */

import toast from "react-hot-toast";

/**
 * An error thrown for non-2xx API responses (or a request that never reached the
 * server). `code` is the server's machine-readable identifier from the error
 * envelope, when present. `displayMessage` marks whether `message` is safe to
 * show to the user — `true` for server-envelope messages and intentional
 * client-side messages, `false` for a generic fallback synthesised from a
 * non-envelope body (e.g. a static host's 404 HTML), which must never be shown.
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
        public code?: string,
        public details?: unknown,
        public displayMessage = true
    ) {
        super(message);
        this.name = "ApiError";
    }
}

/** Friendly messages keyed by the server's machine-readable error `code`. */
const MESSAGE_BY_CODE: Record<string, string> = {
    BackendUnreachable: "🔌 Can't Reach The Server",
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
    FFmpeg: "🎬 Video Processing Failed",
    Fugashi: "🈂️ The Tokenizer Is Unavailable",
    Kotobase: "📖 The Dictionary Is Unavailable",
    LLM: "🤖 The LLM Request Failed",
    Transcription: "🎤 Transcription Failed",
    Modal: "☁️ The Remote GPU Job Failed",
    Media: "💾 A Media Error Occurred",
    MediaNotFound: "🔍 Media File Not Found",
    InvalidMediaPath: "🚫 Invalid Media Path",
};

/**
 * A stable toast id per error class, so identical errors (e.g. an SWR retry
 * storm against a dead backend, or several panels failing at once) collapse onto
 * a single toast that updates in place instead of stacking duplicates.
 */
function errorToastId(err: unknown): string {
    if (err instanceof ApiError) return `api:${err.code ?? err.status}`;
    return "api:unexpected";
}

/**
 * Displays an API error as a toast, preferring the server's machine-readable
 * `code`, then an explicit (envelope/client) message, then the HTTP status.
 * Never shows a raw non-envelope body.
 *
 * @param {unknown} err The error to display.
 * @param {string} [toastId] An existing toast id to update.
 */
export function toastApiError(err: unknown, toastId?: string) {
    const opts = { id: toastId ?? errorToastId(err), duration: 5000 };

    if (err instanceof ApiError) {
        if (err.code && MESSAGE_BY_CODE[err.code]) {
            toast.error(MESSAGE_BY_CODE[err.code], opts);
            return;
        }
        if (err.status === 403) {
            toast.error("🚫 Not Allowed", opts);
            return;
        }
        // Show the message only when it's a real, safe-to-display string (server
        // envelope or an intentional client message) — never a raw HTML / proxy
        // body, which is suppressed in favour of a generic notice.
        if (err.displayMessage && err.message) {
            console.error(`API Error ${err.status}:`, err.message, err);
            const msg = err.message.length > 160 ? `${err.message.slice(0, 157)}…` : err.message;
            toast.error(msg, opts);
            return;
        }
        console.error(`API Error ${err.status}:`, err);
        toast.error(`Server Error (${err.status})`, opts);
        return;
    }

    console.error("Unexpected Error:", err);
    toast.error("Unexpected Error", opts);
}
