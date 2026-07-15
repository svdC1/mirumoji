/**
 * @packageDocumentation The Advanced panel's App Data sub-tab: a maintenance
 * action that unregisters the service worker and clears its caches, for
 * recovering a client stuck on a stale cached build. Profile and preferences
 * are kept.
 */

import { useState } from "react";
import { Button } from "@/shared/ui";
import { resetAppData } from "@/shared/pwa/reset";

/** The App Data reset controls, rendered inside the Advanced panel. */
export function AppDataPanel() {
    const [confirming, setConfirming] = useState(false);

    return (
        <div className="space-y-4">
            <p className="text-sm text-ink-muted">
                Clears The Cached App And Reloads A Fresh Copy. Use This If An Update Has Not Taken
                Effect. Your Profile And Settings Are Kept
            </p>
            <div className="flex items-center justify-center gap-2">
                <Button
                    variant="secondary"
                    onClick={() => {
                        if (confirming) {
                            void resetAppData();
                        } else {
                            setConfirming(true);
                        }
                    }}
                >
                    {confirming ? "Tap Again To Confirm" : "Reset App Data"}
                </Button>
                {confirming && (
                    <Button variant="ghost" onClick={() => setConfirming(false)}>
                        Cancel
                    </Button>
                )}
            </div>
        </div>
    );
}
