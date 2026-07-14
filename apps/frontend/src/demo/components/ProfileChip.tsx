/**
 * @packageDocumentation Demo variant of the sidebar profile control, aliased in
 * only for `--mode demo`. The demo runs on one fixed profile, so this shows it
 * read-only with no set / clear dialog.
 */

import { User } from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";

export interface ProfileChipProps {
    /** Whether the sidebar is expanded (show the label) or collapsed (icon only). */
    expanded: boolean;
}

/** The demo profile chip: the fixed profile, read-only. */
export function ProfileChip({ expanded }: ProfileChipProps) {
    const { profileId } = useProfile();

    return (
        <div
            title={`Demo Profile: ${profileId ?? "demo"}`}
            className="flex h-11 w-full items-center text-left"
        >
            <span className="flex w-16 shrink-0 items-center justify-center">
                <span className="grid h-7 w-7 place-items-center rounded-full border border-shu/40 bg-shu/15 text-shu">
                    <User size={15} />
                </span>
            </span>
            {expanded && (
                <span className="min-w-0 flex-1 pr-3">
                    <span className="block truncate text-sm text-ink">{profileId ?? "demo"}</span>
                    <span className="block text-2xs text-ink-faint">Demo Profile</span>
                </span>
            )}
        </div>
    );
}
