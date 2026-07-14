/**
 * @packageDocumentation Demo variant of the Dictionary hub, aliased in only for
 * `--mode demo`. Free search has no fixtures, so the search control is disabled
 * with a hint to use the curated suggestions on the landing view. The breadcrumb
 * trail and routed `<Outlet/>` are kept intact so links between the captured
 * word / kanji views still work.
 */

import { Link, Outlet, useLocation, useMatch, useSearchParams } from "react-router-dom";
import { ChevronRight, Search } from "lucide-react";
import { kanjiRoute, wordRoute } from "@/shared/dict/routes";
import type { DictionaryTrailState } from "@real/features/dictionary/DictionaryPage";

export type { DictionaryTrailState } from "@real/features/dictionary/DictionaryPage";

/** The demo Dictionary hub: disabled search + the real breadcrumb + `<Outlet/>`. */
export default function DictionaryPage() {
    const location = useLocation();
    const [searchParams] = useSearchParams();
    const wordMatch = useMatch("/dictionary/word");
    const kanjiMatch = useMatch("/dictionary/kanji");
    const radicalsMatch = useMatch("/dictionary/radicals");
    const trail = (location.state ?? {}) as DictionaryTrailState;
    const routeTerm = wordMatch ? (searchParams.get("term") ?? "") : "";

    const crumbs: { label: string; to?: string; ja?: boolean }[] = [];
    if (wordMatch || kanjiMatch || radicalsMatch) {
        crumbs.push({ label: "Search", to: "/dictionary" });
    }
    if (kanjiMatch) {
        if (trail.fromWord) {
            crumbs.push({ label: trail.fromWord, to: wordRoute(trail.fromWord), ja: true });
        }
        crumbs.push({ label: searchParams.get("char") ?? "", ja: true });
    } else if (wordMatch) {
        if (trail.fromKanji) {
            crumbs.push({ label: trail.fromKanji, to: kanjiRoute(trail.fromKanji), ja: true });
        }
        crumbs.push({ label: routeTerm, ja: true });
    } else if (radicalsMatch) {
        crumbs.push({ label: "Radicals" });
    }

    return (
        <div className="mx-auto min-h-[var(--content-h)] w-full max-w-3xl px-[calc(1rem_+_var(--safe-x))] py-8 lg:min-h-dvh">
            <div className="mx-auto mb-5 max-w-xl">
                <h1 className="mb-6 text-center font-display text-3xl text-ink">Dictionary</h1>

                <div className="flex items-stretch overflow-hidden rounded-control border border-ink/15 bg-surface-2 opacity-60">
                    <input
                        disabled
                        placeholder="Search Is Limited In The Demo, Use The Suggestions Below"
                        className="min-w-0 flex-1 cursor-default bg-transparent px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:outline-none"
                    />
                    <span className="shrink-0 border-l border-ink/10 px-3.5 py-2.5 text-ink-faint">
                        <Search size={17} />
                    </span>
                </div>

                {crumbs.length > 0 && (
                    <nav
                        aria-label="Breadcrumb"
                        className="mt-2.5 flex flex-wrap items-center gap-1 text-sm"
                    >
                        {crumbs.map((crumb, i) => (
                            <span key={i} className="flex items-center gap-1">
                                {i > 0 && <ChevronRight size={13} className="text-ink-faint" />}
                                {crumb.to ? (
                                    <Link
                                        to={crumb.to}
                                        lang={crumb.ja ? "ja" : undefined}
                                        className="text-ink-muted transition-colors hover:text-shu"
                                    >
                                        {crumb.label}
                                    </Link>
                                ) : (
                                    <span lang={crumb.ja ? "ja" : undefined} className="text-ink">
                                        {crumb.label}
                                    </span>
                                )}
                            </span>
                        ))}
                    </nav>
                )}
            </div>

            <Outlet />
        </div>
    );
}
