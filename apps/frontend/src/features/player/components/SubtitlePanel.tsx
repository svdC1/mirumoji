/**
 * @packageDocumentation The subtitle-navigation panel: the full cue list with
 * search, click-to-seek, and an active-cue highlight that auto-scrolls into
 * view. Collapsible to a thin rail so the video can reclaim the width.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import {
    PanelRightClose,
    PanelRightOpen,
    PanelBottomOpen,
    PanelBottomClose,
    Search,
} from "lucide-react";
import { Input, IconButton, EmptyState, cn } from "@/shared/ui";
import { useIsMobile } from "@/shared/hooks/useMediaQuery";
import { formatClock } from "@/shared/format/time";
import type { Cue } from "../types";

export interface SubtitlePanelProps {
    cues: Cue[];
    activeIdx: number | null;
    collapsed: boolean;
    onToggle: () => void;
    onSeek: (seconds: number) => void;
}

/**
 * The SubtitlePanel component.
 *
 * @param {SubtitlePanelProps} props The props.
 * @returns {JSX.Element} The subtitle navigation panel.
 */
export function SubtitlePanel({
    cues,
    activeIdx,
    collapsed,
    onToggle,
    onSeek,
}: SubtitlePanelProps) {
    const [query, setQuery] = useState("");
    const activeRef = useRef<HTMLButtonElement | null>(null);

    // The panel docks to the right on desktop and the bottom on mobile, so the
    // collapse/expand affordances point the matching direction.
    const isMobile = useIsMobile();
    const ExpandIcon = isMobile ? PanelBottomOpen : PanelRightOpen;
    const CollapseIcon = isMobile ? PanelBottomClose : PanelRightClose;

    // Keep original indices so the active highlight + seek survive filtering.
    const rows = useMemo(() => {
        const q = query.trim().toLowerCase();
        return cues
            .map((cue, idx) => ({ cue, idx }))
            .filter(({ cue }) => (q ? cue.raw.toLowerCase().includes(q) : true));
    }, [cues, query]);

    // Auto-scroll the active cue into view when it changes.
    useEffect(() => {
        if (collapsed) return;
        activeRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }, [activeIdx, collapsed]);

    if (collapsed) {
        // Mobile: a slim full-width bar below the video. Desktop: a vertical rail.
        return (
            <div className="flex w-full shrink-0 items-center gap-2 border-t border-ink/10 bg-surface px-3 py-2 md:h-full md:w-11 md:flex-col md:border-l md:border-t-0 md:px-0 md:py-3">
                <IconButton label="Show Subtitles" onClick={onToggle}>
                    <ExpandIcon size={18} />
                </IconButton>
                <span className="text-2xs uppercase tracking-widest text-ink-faint md:mt-3 md:[writing-mode:vertical-rl]">
                    Subtitles
                </span>
            </div>
        );
    }

    // Mobile: full-width, fills the space below the video. Desktop: a fixed rail.
    return (
        <aside className="flex min-h-0 w-full flex-1 flex-col border-t border-ink/10 bg-surface md:h-full md:w-80 md:flex-none md:border-l md:border-t-0 lg:w-96">
            <div className="flex items-center gap-2 border-b border-ink/10 px-3 py-2.5">
                <h2 className="flex-1 font-display text-sm text-ink">Subtitles</h2>
                <span className="text-2xs text-ink-faint">{cues.length} Cues</span>
                <IconButton label="Hide Subtitles" size="sm" onClick={onToggle}>
                    <CollapseIcon size={16} />
                </IconButton>
            </div>

            <div className="border-b border-ink/10 p-2.5">
                <div className="relative">
                    <Search
                        size={15}
                        className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-faint"
                    />
                    <Input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search Subtitles ..."
                        className="pl-8"
                    />
                </div>
            </div>

            {cues.length === 0 ? (
                <EmptyState title="No Subtitles" description="Load / Generate SRT" />
            ) : rows.length === 0 ? (
                <EmptyState title="No Matches" description={`Nothing Matches “${query}”`} />
            ) : (
                <ul className="min-h-0 flex-1 overflow-y-auto p-2">
                    {rows.map(({ cue, idx }) => {
                        const active = idx === activeIdx;
                        return (
                            <li key={idx}>
                                <button
                                    ref={active ? activeRef : undefined}
                                    onClick={() => onSeek(cue.start)}
                                    className={cn(
                                        "mb-1 flex w-full gap-2.5 rounded-control border-l-2 px-2.5 py-2 text-left transition-colors",
                                        active
                                            ? "border-shu bg-shu/10"
                                            : "border-transparent hover:bg-ink/5"
                                    )}
                                >
                                    <span className="shrink-0 pt-0.5 text-2xs tabular-nums text-ink-faint">
                                        {formatClock(cue.start)}
                                    </span>
                                    <span
                                        lang="ja"
                                        className={cn(
                                            "text-sm leading-snug",
                                            active ? "text-ink" : "text-ink-muted"
                                        )}
                                    >
                                        {cue.raw}
                                    </span>
                                </button>
                            </li>
                        );
                    })}
                </ul>
            )}
        </aside>
    );
}
