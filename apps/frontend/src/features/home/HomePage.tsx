/**
 * @packageDocumentation The Home page — a quick-start launcher: active-profile
 * status, primary actions, a glance at recent clips/transcripts, and links to
 * the Guide / repo / docs.
 */

import { Link } from "react-router-dom";
import useSWR from "swr";
import {
    Clapperboard,
    Mic,
    Languages,
    BookOpen,
    GraduationCap,
    Github,
    ScrollText,
    ArrowRight,
    User,
} from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";
import { Card, Button, Badge, buttonClasses, cn } from "@/shared/ui";
import { listClips, listTranscripts } from "@/features/profile/api";
import type { Clip } from "@/shared/clips/types";
import type { ProfileTranscript } from "@/features/profile/types";

const ACTIONS = [
    {
        to: "/player",
        icon: Clapperboard,
        title: "Player",
        desc: "Watch With Interactive Subtitles",
    },
    { to: "/transcribe", icon: Mic, title: "Transcribe", desc: "Record Or Upload Audio" },
    { to: "/text", icon: Languages, title: "Text Analyzer", desc: "Tokenize Pasted Japanese" },
    { to: "/dictionary", icon: BookOpen, title: "Dictionary", desc: "Look Up Words And Kanji" },
];

/**
 * The HomePage component.
 *
 * @returns {JSX.Element} The home page.
 */
export default function HomePage() {
    const { profileId } = useProfile();
    const { data: clips } = useSWR<Clip[]>(profileId ? "profiles/clips" : null, listClips, {
        revalidateOnFocus: false,
        keepPreviousData: true,
    });
    const { data: transcripts } = useSWR<ProfileTranscript[]>(
        profileId ? "profiles/transcripts" : null,
        listTranscripts,
        { revalidateOnFocus: false, keepPreviousData: true }
    );

    return (
        <div className="mx-auto min-h-[var(--content-h)] lg:min-h-dvh w-full max-w-5xl px-[calc(1rem_+_var(--safe-x))] py-10">
            <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <span
                        lang="ja"
                        className="grid h-11 w-11 place-items-center rounded-lg bg-shu/15 font-jp text-2xl text-shu"
                    >
                        見
                    </span>
                    <div>
                        <h1 className="font-display text-2xl text-ink">Mirumoji</h1>
                        <p className="text-sm text-ink-muted">Japanese Immersion Toolkit</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <a
                        href="https://github.com/svdC1/mirumoji"
                        target="_blank"
                        rel="noopener noreferrer"
                        className={buttonClasses("secondary", "sm")}
                    >
                        <Github size={15} /> GitHub
                    </a>
                    <a
                        href="https://svdc1.github.io/mirumoji/docs"
                        target="_blank"
                        rel="noopener noreferrer"
                        className={buttonClasses("secondary", "sm")}
                    >
                        <ScrollText size={15} /> Docs
                    </a>
                </div>
            </header>

            {/* Active profile */}
            <Card className="mb-8 flex flex-wrap items-center gap-4 p-5">
                <span
                    className={cn(
                        "grid h-10 w-10 place-items-center rounded-full border",
                        profileId
                            ? "border-shu/40 bg-shu/15 text-shu"
                            : "border-ink/15 text-ink-faint"
                    )}
                >
                    <User size={18} />
                </span>
                <div className="min-w-0 flex-1">
                    <div className="text-2xs uppercase tracking-wide text-ink-faint">
                        Active Profile
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="min-w-0 truncate font-display text-lg text-ink">
                            {profileId ?? "None Set"}
                        </span>
                        {profileId && <Badge tone="success">Active</Badge>}
                    </div>
                </div>
                <Link
                    to="/dashboard"
                    className={buttonClasses(profileId ? "secondary" : "primary", "sm")}
                >
                    {profileId ? "Manage" : "Set A Profile"}
                </Link>
            </Card>

            {/* Primary actions */}
            <div className="mb-10 grid gap-3 sm:grid-cols-2">
                {ACTIONS.map(({ to, icon: Icon, title, desc }) => (
                    <Link key={to} to={to} className="group">
                        <Card className="flex items-center gap-4 p-5 transition-colors group-hover:border-shu/40">
                            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-ink/5 text-ink-muted transition-colors group-hover:bg-shu/15 group-hover:text-shu">
                                <Icon size={20} />
                            </span>
                            <div className="flex-1">
                                <div className="font-display text-lg text-ink">{title}</div>
                                <div className="text-sm text-ink-muted">{desc}</div>
                            </div>
                            <ArrowRight
                                size={18}
                                className="text-ink-faint transition-transform group-hover:translate-x-0.5 group-hover:text-shu"
                            />
                        </Card>
                    </Link>
                ))}
            </div>

            {/* Recent activity */}
            {profileId &&
                ((clips && clips.length > 0) || (transcripts && transcripts.length > 0)) && (
                    <div className="mb-10 grid gap-6 sm:grid-cols-2">
                        {clips && clips.length > 0 && (
                            <div className="min-w-0">
                                <div className="mb-2 flex items-center justify-between">
                                    <h2 className="font-display text-ink">Recent Clips</h2>
                                    <Link
                                        to="/dashboard"
                                        className="text-sm text-ai hover:underline"
                                    >
                                        View All
                                    </Link>
                                </div>
                                <Card className="divide-y divide-ink/10">
                                    {clips.slice(0, 3).map((c) => (
                                        <div
                                            key={c.id}
                                            lang="ja"
                                            className="truncate px-4 py-2.5 text-sm text-ink-muted"
                                        >
                                            {c.breakdown.sentence ||
                                                c.breakdown.focus?.word.surface ||
                                                "Clip"}
                                        </div>
                                    ))}
                                </Card>
                            </div>
                        )}
                        {transcripts && transcripts.length > 0 && (
                            <div className="min-w-0">
                                <div className="mb-2 flex items-center justify-between">
                                    <h2 className="font-display text-ink">Recent Transcripts</h2>
                                    <Link
                                        to="/dashboard"
                                        className="text-sm text-ai hover:underline"
                                    >
                                        View All
                                    </Link>
                                </div>
                                <Card className="divide-y divide-ink/10">
                                    {transcripts.slice(0, 3).map((t) => (
                                        <div
                                            key={t.id}
                                            lang="ja"
                                            className="truncate px-4 py-2.5 text-sm text-ink-muted"
                                        >
                                            {t.text}
                                        </div>
                                    ))}
                                </Card>
                            </div>
                        )}
                    </div>
                )}

            {/* Guide CTA + footer */}
            <Card className="mb-8 flex flex-wrap items-center gap-4 p-5">
                <GraduationCap size={22} className="text-ink-faint" />
                <div className="flex-1">
                    <div className="font-display text-ink">New To Mirumoji ?</div>
                    <div className="text-sm text-ink-muted">
                        See How To Set Profiles, Use The Player, Record Clips, And Setup An LLM
                    </div>
                </div>
                <Link to="/guide">
                    <Button variant="secondary" size="sm">
                        Open Guide
                    </Button>
                </Link>
            </Card>

            <footer className="flex flex-col items-center gap-1 border-t border-ink/10 pt-6 text-sm text-ink-faint">
                <span>© {new Date().getFullYear()} svdC1</span>
                <a
                    href="https://github.com/svdC1/mirumoji/blob/main/LICENSE"
                    className="text-ai hover:underline"
                >
                    MIT License
                </a>
            </footer>
        </div>
    );
}
