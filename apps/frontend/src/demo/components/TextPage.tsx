/**
 * @packageDocumentation Demo variant of the Text Analyzer, aliased in only for
 * `--mode demo`. Arbitrary pasted text has no tokenization fixture, so it shows
 * the captured sample sentence (read-only) tokenized from the recorded fixture.
 */

import { useEffect, useState } from "react";
import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { apiTokenize } from "@/shared/dict/api";
import { toastApiError } from "@/shared/api/errors";
import TokenizedText from "@/shared/components/TokenizedText";
import WordDialog from "@/shared/components/WordDialog";
import { Card, cn } from "@/shared/ui";
import type { JapaneseWord } from "@/shared/dict/types";
import sample from "../generated/sample.json";

/** The demo Text Analyzer: the sample sentence, tokenized read-only. */
export default function TextPage() {
    const text = (sample as { text?: string }).text ?? "";
    const [words, setWords] = useState<JapaneseWord[]>([]);
    const [selected, setSelected] = useState<{ sentence: string; word: string } | null>(null);
    const [showFurigana, setShowFurigana] = useState(true);
    const { mode } = useBundleSettings();

    useEffect(() => {
        if (!text) return;
        apiTokenize(text, mode)
            .then(setWords)
            .catch((e) => toastApiError(e));
    }, [text, mode]);

    return (
        <div className="mx-auto min-h-[var(--content-h)] w-full max-w-4xl px-[calc(1rem_+_var(--safe-x))] py-8 lg:min-h-dvh">
            <h1 className="mb-2 font-display text-3xl text-ink">Text Analyzer</h1>
            <p className="mb-6 text-sm text-ink-muted">
                Pasting Your Own Text Needs A Backend. Here Is The Demo Sample, Tokenized
            </p>

            <div className="mb-4 flex justify-end">
                <button
                    lang="ja"
                    onClick={() => setShowFurigana((v) => !v)}
                    title="Toggle Furigana"
                    className={cn(
                        "h-8 rounded-control px-3 text-sm font-medium transition-colors",
                        showFurigana
                            ? "bg-shu/15 text-shu"
                            : "text-ink-muted hover:bg-ink/5 hover:text-ink"
                    )}
                >
                    ふり
                </button>
            </div>

            <Card lang="ja" className="p-6 text-2xl leading-loose">
                <TokenizedText
                    words={words}
                    sentence={text}
                    showFurigana={showFurigana}
                    onWordClick={(sentence, word) => setSelected({ sentence, word })}
                    selectedLemma={selected?.word}
                />
            </Card>

            {selected && (
                <WordDialog
                    sentence={selected.sentence}
                    word={selected.word}
                    onClose={() => setSelected(null)}
                    cueStart={0}
                    cueEnd={0}
                    videoFile={null}
                    videoUrl={undefined}
                />
            )}
        </div>
    );
}
