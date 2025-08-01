/**
 * @packageDocumentation This file contains utility functions for working with files.
 */

/**
 * Truncates a filename to a specified length.
 *
 * @param {string | undefined} filename The filename to truncate.
 * @param {number} [startChars=8] The number of characters to keep at the beginning of the filename.
 * @param {number} [endChars=4] The number of characters to keep at the end of the filename.
 * @returns {string} The truncated filename.
 */
export const truncateFilename = (
    filename: string | undefined,
    startChars = 8,
    endChars = 4
) => {
    if (!filename) return "Unknown";
    if (filename.length > startChars + endChars + 3) {
        return `${filename.substring(0, startChars)}...${filename.substring(
            filename.length - endChars
        )}`;
    }
    return filename;
};

/**
 * Gets the extension of a file.
 *
 * @param {string | undefined} filenameOrUrl The filename or URL to get the extension from.
 * @returns {string} The file extension.
 */
export const getFileExtension = (filenameOrUrl: string | undefined) => {
    if (!filenameOrUrl) return "";
    const parts = filenameOrUrl.split(".");
    return parts.length > 1 ? parts.pop()!.split("?")[0] : "";
};

/**
 * Formats a static URL for the API
 *
 * @param {string} API_BASE The base URL of the API. (`/` included)
 * @param {string} url The URL to format.
 * @returns {string} The formatted URL.
 */
export const formatStaticUrl = (API_BASE: string, url: string) => {
    return `${API_BASE}${url}`;
};

/**
 * Truncates a string to a specified length.
 *
 * @param {string | undefined} text The string to truncate.
 * @param {number} [maxLength=50] The maximum length of the string.
 * @returns {string} The truncated string.
 */
export const truncateText = (text: string | undefined, maxLength = 50) => {
    if (!text) return "";
    if (text.length > maxLength) {
        return `${text.substring(0, maxLength)}...`;
    }
    return text;
};

export const uploadFile = (
    file: File,
    url: string,
    onProgress: (percent: number) => void
): Promise<any> => {
    return new Promise((resolve, reject) => {
        const uploadId = `${file.name}-${Date.now()}`;
        const xhr = new XMLHttpRequest();

        xhr.open("POST", url, true);
        xhr.setRequestHeader("X-Upload-ID", uploadId);
        xhr.setRequestHeader("X-File-Name", file.name);
        
        // This is crucial for FastAPI to not wait for the whole body
        // and to correctly handle the stream.
        xhr.setRequestHeader("Content-Type", "application/octet-stream");


        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                onProgress(percentComplete);
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    reject(new Error("Failed to parse server response."));
                }
            } else {
                reject(new Error(xhr.statusText));
            }
        };

        xhr.onerror = () => {
            reject(new Error("Network Error"));
        };

        xhr.send(file);
    });
};

