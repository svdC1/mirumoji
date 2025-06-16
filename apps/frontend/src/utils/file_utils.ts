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

export const getFileExtension = (filenameOrUrl: string | undefined) => {
    if (!filenameOrUrl) return "";
    const parts = filenameOrUrl.split(".");
    return parts.length > 1 ? parts.pop()!.split("?")[0] : "";
};

export const formatStaticUrl = (API_BASE: string, url: string) => {
    return `${API_BASE}${url}`;
};

export const truncateText = (text: string | undefined, maxLength = 50) => {
    if (!text) return "";
    if (text.length > maxLength) {
        return `${text.substring(0, maxLength)}...`;
    }
    return text;
};
