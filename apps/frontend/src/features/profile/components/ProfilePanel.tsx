/**
 * @packageDocumentation The Profile tab: shows the active profile and lets the
 * user set or clear it (migrated from the old nav menu).
 */

import { useState } from "react";
import { User } from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";
import { Card, Button, Input, Label, Badge, cn } from "@/shared/ui";

/**
 * The ProfilePanel component.
 *
 * @returns {JSX.Element} The profile panel.
 */
export function ProfilePanel() {
    const { profileId, setProfileId } = useProfile();
    const [draft, setDraft] = useState(profileId ?? "");

    // The profile name travels in the `X-Profile-ID` request header, which can
    // only carry ASCII, and a Modal-hosted deploy rejects a non-ASCII header
    // outright, so the name is held to ASCII here with a clear reason
    const trimmed = draft.trim();
    const nonAscii = [...trimmed].some((ch) => ch.charCodeAt(0) > 127);
    const dirty = trimmed !== (profileId ?? "");

    const save = () => {
        if (nonAscii) return;
        setProfileId(trimmed || null);
    };

    return (
        <Card className="max-w-none space-y-5 p-6">
            <div className="flex items-center gap-3">
                <span
                    className={cn(
                        "grid h-11 w-11 place-items-center rounded-full border",
                        profileId
                            ? "border-shu/40 bg-shu/15 text-shu"
                            : "border-ink/15 text-ink-faint"
                    )}
                >
                    <User size={20} />
                </span>
                <div className="flex-1">
                    <div className="text-2xs uppercase tracking-wide text-ink-faint">
                        Active profile
                    </div>
                    <div className="font-display text-xl text-ink">{profileId ?? "None"}</div>
                </div>
                {profileId && <Badge tone="success">Active</Badge>}
            </div>

            <p className="text-sm text-ink-muted">
                Files, Transcripts, Clips, and LLM Template Are Stored Under This Profile Name On
                The Server
            </p>

            <div>
                <Label htmlFor="dash-profile">Profile Name</Label>
                <Input
                    id="dash-profile"
                    value={draft}
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

            <div className="flex gap-2">
                <Button onClick={save} disabled={!dirty || nonAscii}>
                    Save
                </Button>
                {profileId && (
                    <Button
                        variant="ghost"
                        onClick={() => {
                            setProfileId(null);
                            setDraft("");
                        }}
                    >
                        Clear
                    </Button>
                )}
            </div>
        </Card>
    );
}
