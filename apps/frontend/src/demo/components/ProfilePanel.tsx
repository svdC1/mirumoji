/**
 * @packageDocumentation Demo variant of the dashboard Profile tab, aliased in
 * only for `--mode demo`. The demo runs on one fixed profile, so it shows it
 * read-only with no set / clear controls.
 */

import { User } from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";
import { Badge, Card } from "@/shared/ui";

/** The demo Profile tab: the fixed profile, read-only. */
export function ProfilePanel() {
    const { profileId } = useProfile();

    return (
        <Card className="max-w-none space-y-5 p-6">
            <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-full border border-shu/40 bg-shu/15 text-shu">
                    <User size={20} />
                </span>
                <div className="flex-1">
                    <div className="text-2xs uppercase tracking-wide text-ink-faint">
                        Active profile
                    </div>
                    <div className="font-display text-xl text-ink">{profileId ?? "demo"}</div>
                </div>
                <Badge tone="success">Demo</Badge>
            </div>

            <p className="text-sm text-ink-muted">
                The Demo Runs On A Single Fixed Profile. Switching Is Disabled Here
            </p>
        </Card>
    );
}
