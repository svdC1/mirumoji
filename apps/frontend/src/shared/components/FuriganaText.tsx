/**
 * @packageDocumentation Renders a word with accurate furigana as ruby text,
 * from the per-segment segmentation the server extracts (JmdictFurigana).
 * Kana-only segments carry no annotation and render as plain text.
 */

import { Fragment } from "react";
import type { FuriganaSegment } from "@/shared/dict/types";

export interface FuriganaTextProps {
    /** The word's furigana segments. */
    segments: FuriganaSegment[];
    /** Fallback text when no segmentation is known. */
    fallback: string;
}

/**
 * The FuriganaText component. Font size is inherited, the ruby annotations
 * scale down from it.
 *
 * @param {FuriganaTextProps} props The props.
 * @returns {JSX.Element} The ruby-annotated word.
 */
export default function FuriganaText({ segments, fallback }: FuriganaTextProps) {
    if (segments.length === 0) {
        return <span lang="ja">{fallback}</span>;
    }
    return (
        <ruby
            lang="ja"
            className="[&>rt]:select-none [&>rt]:pb-[0.2em] [&>rt]:text-[0.42em] [&>rt]:text-ink-muted"
        >
            {segments.map((seg, i) => (
                <Fragment key={i}>
                    {seg.ruby}
                    <rt>{seg.rt ?? ""}</rt>
                </Fragment>
            ))}
        </ruby>
    );
}
