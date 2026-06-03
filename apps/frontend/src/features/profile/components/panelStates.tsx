/**
 * @packageDocumentation Shared Dashboard panel states (no-profile + loading).
 */

import { UserPlus } from "lucide-react";
import { EmptyState, Spinner } from "@/shared/ui";

/**
 * Shown by a panel when no profile is set.
 *
 * @param {{ what: string }} props What the profile is needed for.
 * @returns {JSX.Element} The empty state.
 */
export function NoProfile({ what }: { what: string }) {
    return (
        <EmptyState
            icon={<UserPlus size={28} />}
            title="No Profile Set"
            description={`Set a profile to ${what}`}
        />
    );
}

/**
 * A centered loading spinner for a panel's first load.
 *
 * @returns {JSX.Element} The spinner.
 */
export function PanelLoading() {
    return (
        <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-ink-faint" />
        </div>
    );
}
