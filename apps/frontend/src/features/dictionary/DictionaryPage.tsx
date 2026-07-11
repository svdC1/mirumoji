/**
 * @packageDocumentation The Dictionary hub layout: a single integrated search
 * control (Japanese / English / Radicals modes fused to the input) above a
 * breadcrumb trail that stitches the routed views together (search results,
 * word entry, kanji detail, radical search). Every view is URL-addressed so
 * back/forward, deep links, and the WordDialog's cross-link all work.
 */

import { useEffect, useState } from "react";
import {
    Link,
    Outlet,
    useLocation,
    useMatch,
    useNavigate,
    useSearchParams,
} from "react-router-dom";
import { ChevronRight, Search } from "lucide-react";
import { Tooltip, cn } from "@/shared/ui";
import { kanjiRoute, wordRoute } from "@/shared/dict/routes";

type SearchMode = "jp" | "en" | "radicals";

/** Navigation state the views pass along so the breadcrumb can show a trail. */
export interface DictionaryTrailState {
    /** The word view a kanji was opened from. */
    fromWord?: string;
    /** The picked radicals a kanji was opened from. */
    fromRadicals?: string;
    /** The radical match mode (all / any) the kanji was opened from. */
    fromRadicalsMatch?: string;
    /** The kanji view a word was opened from. */
    fromKanji?: string;
}

const MODES: { key: SearchMode; label: string; hint: string }[] = [
    { key: "jp", label: "あ", hint: "Search Japanese Words" },
    { key: "en", label: "A", hint: "Search By English Meaning" },
    { key: "radicals", label: "部", hint: "Find Kanji By Radical" },
];

/**
 * The DictionaryPage layout component.
 *
 * @returns {JSX.Element} The dictionary hub.
 */
export default function DictionaryPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const [searchParams] = useSearchParams();
    const wordMatch = useMatch("/dictionary/word");
    const kanjiMatch = useMatch("/dictionary/kanji");
    const radicalsMatch = useMatch("/dictionary/radicals");
    const trail = (location.state ?? {}) as DictionaryTrailState;

    const urlQuery = searchParams.get("q") ?? "";
    // The routed kanji/word value now travels in the query string (see
    // `shared/dict/routes`) so the URL path stays ASCII for a Modal-hosted host
    const routeTerm = wordMatch ? (searchParams.get("term") ?? "") : "";
    const mode: SearchMode = radicalsMatch
        ? "radicals"
        : searchParams.get("mode") === "en"
          ? "en"
          : "jp";

    const [pattern, setPattern] = useState(routeTerm || urlQuery);

    // Keep the search field reflecting the hub's current place, so the bar
    // reads as the hub's spine rather than a detached form
    useEffect(() => {
        if (routeTerm) setPattern(routeTerm);
        else if (urlQuery) setPattern(urlQuery);
    }, [routeTerm, urlQuery]);

    const setMode = (next: SearchMode) => {
        if (next === mode) return;
        if (next === "radicals") navigate("/dictionary/radicals");
        else if (next === "en") navigate("/dictionary?mode=en");
        else navigate("/dictionary");
    };

    const submit = () => {
        const q = pattern.trim();
        if (!q || mode === "radicals") return;
        if (mode === "en") {
            navigate(`/dictionary?q=${encodeURIComponent(q)}&mode=en`);
        } else if (/[*%]/.test(q)) {
            // Wildcards match many words, so they land on the results list
            navigate(`/dictionary?q=${encodeURIComponent(q)}&mode=jp`);
        } else {
            navigate(wordRoute(q));
        }
    };

    // Breadcrumb trail: Search › (word) › leaf. It encodes how the current
    // view was reached and is the way back
    const crumbs: { label: string; to?: string; ja?: boolean }[] = [];
    if (wordMatch || kanjiMatch || radicalsMatch) {
        crumbs.push({ label: "Search", to: "/dictionary" });
    }
    if (kanjiMatch) {
        if (trail.fromWord) {
            crumbs.push({
                label: trail.fromWord,
                to: wordRoute(trail.fromWord),
                ja: true,
            });
        }
        if (trail.fromRadicals) {
            const matchParam = trail.fromRadicalsMatch === "any" ? "&match=any" : "";
            crumbs.push({
                label: "Radicals",
                to: `/dictionary/radicals?picked=${encodeURIComponent(trail.fromRadicals)}${matchParam}`,
            });
        }
        crumbs.push({ label: searchParams.get("char") ?? "", ja: true });
    } else if (wordMatch) {
        if (trail.fromKanji) {
            crumbs.push({
                label: trail.fromKanji,
                to: kanjiRoute(trail.fromKanji),
                ja: true,
            });
        }
        crumbs.push({ label: routeTerm, ja: true });
    } else if (radicalsMatch) {
        crumbs.push({ label: "Radicals" });
    }

    return (
        <div className="mx-auto min-h-[var(--content-h)] w-full max-w-3xl px-[calc(1rem_+_var(--safe-x))] py-8 lg:min-h-dvh">
            <div className="mx-auto mb-5 max-w-xl">
                <h1 className="mb-6 text-center font-display text-3xl text-ink">Dictionary</h1>

                {/* One integrated control: mode selector + input + submit */}
                <div className="flex items-stretch overflow-hidden rounded-control border border-ink/15 bg-surface-2 transition-colors focus-within:border-shu/50">
                    <div className="flex shrink-0 items-stretch border-r border-ink/10">
                        {MODES.map(({ key, label, hint }) => (
                            <Tooltip key={key} label={hint}>
                                <button
                                    type="button"
                                    lang="ja"
                                    onClick={() => setMode(key)}
                                    aria-label={hint}
                                    aria-pressed={mode === key}
                                    className={cn(
                                        "px-3 text-sm font-medium transition-colors",
                                        mode === key
                                            ? "bg-shu/15 text-shu"
                                            : "text-ink-faint hover:bg-ink/5 hover:text-ink"
                                    )}
                                >
                                    {label}
                                </button>
                            </Tooltip>
                        ))}
                    </div>
                    <input
                        lang={mode === "jp" ? "ja" : undefined}
                        value={mode === "radicals" ? "" : pattern}
                        disabled={mode === "radicals"}
                        onChange={(e) => setPattern(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && submit()}
                        placeholder={
                            mode === "jp"
                                ? "Word Or Wildcard Pattern (e.g. *字*)"
                                : mode === "en"
                                  ? "English Meaning"
                                  : "Pick Radicals Below"
                        }
                        className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:outline-none disabled:cursor-default"
                    />
                    <button
                        type="button"
                        onClick={submit}
                        disabled={mode === "radicals"}
                        aria-label="Search"
                        className="shrink-0 border-l border-ink/10 px-3.5 text-ink-muted transition-colors hover:bg-shu/15 hover:text-shu disabled:opacity-40"
                    >
                        <Search size={17} />
                    </button>
                </div>

                {/* Breadcrumb trail stitching the views together */}
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
