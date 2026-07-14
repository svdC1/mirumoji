/**
 * @packageDocumentation The active-profile control in the sidebar foot. Shows
 * the current profile and opens a small dialog to set or clear it. Profile data
 * is just a localStorage id (see ProfileContext); richer management lives on the
 * Dashboard.
 */

import { useEffect, useState } from "react";
import { User } from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";
import { Button, Dialog, Input, Label, cn } from "@/shared/ui";

export interface ProfileChipProps {
    /** Whether the sidebar is expanded (show the label) or collapsed (icon only). */
    expanded: boolean;
}

/**
 * The ProfileChip component.
 *
 * @param {ProfileChipProps} props The props.
 * @returns {JSX.Element} The profile chip + its set/clear dialog.
 */
export function ProfileChip({ expanded }: ProfileChipProps) {
    const { profileId, setProfileId } = useProfile();
    const [open, setOpen] = useState(false);
    const [draft, setDraft] = useState(profileId ?? "");

    useEffect(() => {
        if (open) setDraft(profileId ?? "");
    }, [open, profileId]);

    // The profile name travels in the `X-Profile-ID` request header, which can
    // only carry ASCII, and a Modal-hosted deploy rejects a non-ASCII header
    // outright, so the name is held to ASCII here with a clear reason
    const trimmed = draft.trim();
    const nonAscii = [...trimmed].some((ch) => ch.charCodeAt(0) > 127);

    const save = () => {
        if (nonAscii) return;
        setProfileId(trimmed || null);
        setOpen(false);
    };

    return (
        <>
            <button
                onClick={() => setOpen(true)}
                title={profileId ? `Profile: ${profileId}` : "Set a profile"}
                className={cn(
                    "flex h-11 w-full items-center text-left transition-colors hover:bg-ink/5",
                    !profileId && "text-ink-faint"
                )}
            >
                {/* Same w-16 centered slot as the nav icons + brand. */}
                <span className="flex w-16 shrink-0 items-center justify-center">
                    <span
                        className={cn(
                            "grid h-7 w-7 place-items-center rounded-full border",
                            profileId
                                ? "border-shu/40 bg-shu/15 text-shu"
                                : "border-ink/15 text-ink-faint"
                        )}
                    >
                        <User size={15} />
                    </span>
                </span>
                {expanded && (
                    <span className="min-w-0 flex-1 pr-3">
                        <span className="block truncate text-sm text-ink">
                            {profileId ?? "No Profile"}
                        </span>
                        <span className="block text-2xs text-ink-faint">
                            {profileId ? "Switch / Clear" : "Tap To Set"}
                        </span>
                    </span>
                )}
            </button>

            <Dialog open={open} onClose={() => setOpen(false)} className="max-w-sm">
                <div className="space-y-4 p-6">
                    <h2 className="font-display text-xl text-ink">Profile</h2>
                    <p className="text-sm text-ink-muted">
                        Set a Profile To Persist Data On The Server
                    </p>
                    <div>
                        <Label htmlFor="profile-input">Name</Label>
                        <Input
                            id="profile-input"
                            value={draft}
                            autoFocus
                            placeholder="e.g. Tanaka"
                            aria-invalid={nonAscii}
                            onChange={(e) => setDraft(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && save()}
                        />
                        {nonAscii && (
                            <p className="mt-1.5 text-2xs text-shu">
                                Use ASCII Only (No Japanese Or Accents)
                            </p>
                        )}
                    </div>
                    <div className="flex justify-end gap-2 pt-1">
                        {profileId && (
                            <Button
                                variant="ghost"
                                onClick={() => {
                                    setProfileId(null);
                                    setOpen(false);
                                }}
                            >
                                Clear
                            </Button>
                        )}
                        <Button variant="secondary" onClick={() => setOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={save} disabled={nonAscii}>
                            Save
                        </Button>
                    </div>
                </div>
            </Dialog>
        </>
    );
}
