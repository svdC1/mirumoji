/**
 * @packageDocumentation The expanded view of a saved clip: video + focus word +
 * sentence + LLM explanation.
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { toHiragana } from "@/shared/japanese/kana";
import { staticUrl } from "@/shared/format/files";
import { Card, Button } from "@/shared/ui";
import type { Clip } from "@/shared/clips/types";

/**
 * The ClipDetail component.
 *
 * @param {{ clip: Clip; onClose: () => void }} props The clip + close handler.
 * @returns {JSX.Element} The clip detail view.
 */
export function ClipDetail({ clip, onClose }: { clip: Clip; onClose: () => void }) {
    const { focus, sentence, explanation } = clip.breakdown;
    return (
        <Card elevated className="overflow-hidden">
            <video
                key={staticUrl(clip.clip_url)}
                controls
                src={staticUrl(clip.clip_url)}
                className="aspect-video w-full bg-black"
            />
            <div className="space-y-4 p-5">
                {focus && (
                    <div>
                        <span lang="ja" className="font-display text-2xl text-ink">
                            {focus.word.surface}
                        </span>
                        {focus.word.reading && (
                            <span lang="ja" className="ml-2 text-ink-muted">
                                {toHiragana(focus.word.reading)}
                            </span>
                        )}
                        {focus.kotobase_data.meanings.length > 0 && (
                            <p className="mt-1 text-sm text-ink-muted">
                                {focus.kotobase_data.meanings.join("; ")}
                            </p>
                        )}
                    </div>
                )}
                {sentence && (
                    <div className="border-t border-ink/10 pt-3">
                        <div className="text-2xs uppercase tracking-wide text-ink-faint py-2">
                            Sentence
                        </div>
                        <p lang="ja" className="italic text-ink">
                            {sentence}
                        </p>
                    </div>
                )}
                {explanation && (
                    <div className="prose prose-invert prose-sm max-w-none border-t border-ink/10 pt-3">
                        <div className="text-2xs uppercase tracking-wide text-ink-faint py-2">
                            LLM Explanation
                        </div>
                        <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                            {explanation}
                        </ReactMarkdown>
                    </div>
                )}
                <Button variant="secondary" size="sm" onClick={onClose}>
                    Close
                </Button>
            </div>
        </Card>
    );
}
