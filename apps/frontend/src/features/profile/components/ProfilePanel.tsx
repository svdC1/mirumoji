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

    const save = () => setProfileId(draft.trim() || null);
    const dirty = draft.trim() !== (profileId ?? "");

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
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && save()}
                />
            </div>

            <div className="flex gap-2">
                <Button onClick={save} disabled={!dirty}>
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
