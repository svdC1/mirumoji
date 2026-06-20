/**
 * @packageDocumentation The app shell's primary navigation: a collapsible icon
 * rail that expands on hover (desktop). On the immersive Player route it hides
 * and is reachable via a floating menu button as a left drawer. Profile lives at
 * the foot (not in the nav).
 */

import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
    Home,
    Clapperboard,
    Mic,
    Languages,
    BookOpen,
    GraduationCap,
    LayoutDashboard,
    Menu,
    X,
} from "lucide-react";
import { ProfileChip } from "./ProfileChip";
import { cn, IconButton } from "@/shared/ui";
import { useIsMobile } from "@/shared/hooks/useMediaQuery";

interface NavEntry {
    to: string;
    label: string;
    icon: typeof Home;
    end?: boolean;
}

const NAV: NavEntry[] = [
    { to: "/", label: "Home", icon: Home, end: true },
    { to: "/player", label: "Player", icon: Clapperboard },
    { to: "/transcribe", label: "Transcribe", icon: Mic },
    { to: "/text", label: "Text", icon: Languages },
    { to: "/dictionary", label: "Dictionary", icon: BookOpen },
    { to: "/guide", label: "Guide", icon: GraduationCap },
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
];

function isActive(pathname: string, entry: NavEntry): boolean {
    if (entry.end) return pathname === entry.to;
    return pathname === entry.to || pathname.startsWith(`${entry.to}/`);
}

function RailBody({
    expanded,
    pathname,
    onNavigate,
    scrollable,
}: {
    expanded: boolean;
    pathname: string;
    onNavigate: () => void;
    scrollable: boolean;
}) {
    return (
        <div className="flex h-full flex-col">
            <Link to="/" onClick={onNavigate} className="flex h-16 items-center">
                {/* Fixed w-16 leading slot keeps every glyph on one centered
                    column (32px) so the brand, nav icons, and profile avatar
                    line up in the collapsed rail. */}
                <span className="flex w-16 shrink-0 items-center justify-center">
                    <span
                        lang="ja"
                        className="grid h-9 w-9 place-items-center rounded-lg bg-shu/15 font-jp text-lg text-shu"
                    >
                        見
                    </span>
                </span>
                {expanded && <span className="font-display text-lg text-ink">Mirumoji</span>}
            </Link>

            {/* On a short mobile viewport (landscape phone) the items must scroll
                so the lower ones stay reachable; the desktop rail keeps its
                original non-scrolling layout, where the scrollbar squeezed the
                collapsed icon column. */}
            <nav className={cn("flex-1 py-2", scrollable && "min-h-0 overflow-y-auto")}>
                {NAV.map((entry) => {
                    const active = isActive(pathname, entry);
                    const Icon = entry.icon;
                    return (
                        <Link
                            key={entry.to}
                            to={entry.to}
                            onClick={onNavigate}
                            title={entry.label}
                            className={cn(
                                "flex h-11 items-center transition-colors",
                                active
                                    ? "bg-shu/15 text-shu"
                                    : "text-ink-muted hover:bg-ink/5 hover:text-ink"
                            )}
                        >
                            <span className="flex w-16 shrink-0 items-center justify-center">
                                <Icon size={20} />
                            </span>
                            {expanded && (
                                <span className="truncate text-sm font-medium">{entry.label}</span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            <div className="border-t border-ink/10 py-2">
                <ProfileChip expanded={expanded} />
            </div>
        </div>
    );
}

/**
 * The AppSidebar component.
 *
 * @param {{ immersive: boolean }} props Whether the current route is immersive
 *     (the Player), where the rail hides behind a floating menu button.
 * @returns {JSX.Element} The sidebar.
 */
export function AppSidebar({ immersive }: { immersive: boolean }) {
    const { pathname } = useLocation();
    const [hovered, setHovered] = useState(false);
    const [open, setOpen] = useState(false);
    // Only the mobile drawer scrolls its nav; the desktop rail keeps its
    // original non-scrolling layout (see RailBody).
    const isMobile = useIsMobile();

    return (
        <>
            {/* Drawer menu — every route on mobile, and the immersive Player on
                desktop. Hidden on desktop for regular pages (they use the hover
                rail below), so it never reserves content width on mobile. */}
            {/* Mobile top bar — non-immersive routes. Holds the menu button (and
                brand) so it fills the top strip instead of floating over content. */}
            {!immersive && (
                <header className="fixed inset-x-0 top-0 z-40 flex h-14 items-center gap-2 border-b border-ink/10 bg-surface/80 px-3 backdrop-blur lg:hidden">
                    <IconButton label="Open menu" onClick={() => setOpen(true)}>
                        <Menu size={20} />
                    </IconButton>
                    <Link to="/" className="flex items-center gap-2">
                        <span
                            lang="ja"
                            className="grid h-8 w-8 place-items-center rounded-lg bg-shu/15 font-jp text-shu"
                        >
                            見
                        </span>
                        <span className="font-display text-ink">Mirumoji</span>
                    </Link>
                </header>
            )}

            {/* Floating menu button — immersive Player (all sizes). */}
            {immersive && !open && (
                <IconButton
                    label="Open menu"
                    onClick={() => setOpen(true)}
                    className="fixed left-3 top-3 z-50 bg-surface/70 opacity-60 backdrop-blur transition-opacity hover:opacity-100"
                >
                    <Menu size={20} />
                </IconButton>
            )}

            {/* Drawer overlay + panel — mobile (all routes) + immersive desktop. */}
            <div className={immersive ? "" : "lg:hidden"}>
                {open && (
                    <div
                        className="fixed inset-0 z-40 bg-black/50"
                        onClick={() => setOpen(false)}
                    />
                )}
                <aside
                    className={cn(
                        "fixed left-0 top-0 z-50 h-dvh w-60 border-r border-ink/10 bg-surface transition-transform duration-200",
                        open ? "translate-x-0 shadow-lift" : "-translate-x-full"
                    )}
                >
                    <div className="flex h-full flex-col">
                        <div className="flex justify-end px-2 pt-2">
                            <IconButton label="Close menu" onClick={() => setOpen(false)}>
                                <X size={18} />
                            </IconButton>
                        </div>
                        <div className="min-h-0 flex-1">
                            <RailBody
                                expanded
                                pathname={pathname}
                                onNavigate={() => setOpen(false)}
                                scrollable={isMobile}
                            />
                        </div>
                    </div>
                </aside>
            </div>

            {/* Hover rail — desktop, regular pages only. */}
            {!immersive && (
                <aside
                    onMouseEnter={() => setHovered(true)}
                    onMouseLeave={() => setHovered(false)}
                    className={cn(
                        "fixed left-0 top-0 z-40 hidden h-dvh overflow-hidden border-r border-ink/10 bg-surface transition-[width] duration-200 lg:block",
                        hovered ? "w-60 shadow-lift" : "w-16"
                    )}
                >
                    <RailBody
                        expanded={hovered}
                        pathname={pathname}
                        onNavigate={() => setHovered(false)}
                        scrollable={false}
                    />
                </aside>
            )}
        </>
    );
}
