/**
 * @packageDocumentation Demo variant of the player context, aliased in only for
 * `--mode demo`. It wraps the real provider so the sample-preloading bootstrap
 * and the demo banner mount inside it, and re-exports everything else unchanged.
 */

import type { ReactNode } from "react";
import { PlayerProvider as RealPlayerProvider } from "@real/contexts/PlayerContext";
import { DemoBanner } from "./DemoBanner";
import { DemoBootstrap } from "./DemoBootstrap";

export * from "@real/contexts/PlayerContext";

/** The real player provider with the demo bootstrap + banner mounted inside it. */
export function PlayerProvider({ children }: { children: ReactNode }) {
    return (
        <RealPlayerProvider>
            <DemoBootstrap />
            {children}
            <DemoBanner />
        </RealPlayerProvider>
    );
}
