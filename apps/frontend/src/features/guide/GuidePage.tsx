/**
 * @packageDocumentation The Guide / tutorials page. Placeholder shell — the
 * how-to content is fleshed out in a later pass.
 */

import { EmptyState } from "@/shared/ui";
import { GraduationCap } from "lucide-react";

/**
 * The GuidePage component.
 *
 * @returns {JSX.Element} The guide page.
 */
export default function GuidePage() {
    return (
        <div className="mx-auto min-h-screen w-full max-w-3xl px-4 py-10">
            <h1 className="mb-2 font-display text-3xl text-ink">Guide</h1>
            <p className="mb-8 text-ink-muted">How To Use Mirumoji</p>
            <EmptyState
                icon={<GraduationCap size={32} />}
                title="Tutorials Coming Soon"
                description="Step-by-step guides for the player, profile, subtitles, clips, anki, and configuring an LLM are on the way"
            />
        </div>
    );
}
