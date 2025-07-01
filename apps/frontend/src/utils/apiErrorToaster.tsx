/**
 * @fileoverview This file contains a function for displaying API errors as toasts.
 */

import React from "react";
import toast from "react-hot-toast";
import { ApiError } from "../types/types";

/**
 * Displays an API error as a toast.
 *
 * @param {unknown} err The error to display.
 * @param {string} [toastId] The ID of the toast to update.
 */
export function toastApiError(err: unknown, toastId?: string) {
    const opts = toastId ? { id: toastId, duration: 5000 } : { duration: 5000 };

    if (err instanceof ApiError) {
        switch (err.status) {
            case 403:
                toast.error(
                    "🚫 Action not allowed or permission denied.",
                    opts
                );
                return;
            case 404:
                toast.error("🔍 The requested resource was not found.", opts);
                return;
            default:
                console.error(`API Error ${err.status}:`, err.message, err);
                toast.error(`⚠️ Server Error (${err.status})`, opts);
                return;
        }
    }

    // For non-ApiError types or if err is not an instance of ApiError
    console.error("Unexpected Error:", err);
    toast.error("⚠️ Unexpected Error. Please try again.", opts);
}
