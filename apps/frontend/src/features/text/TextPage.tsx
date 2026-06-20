/**
 * @packageDocumentation The Text Analyzer: tokenizes pasted Japanese on the
 * server and renders it as clickable furigana tokens; clicking a token opens its
 * WordDialog.
 */

import React, { useState } from "react";
import { ArrowLeft, ClipboardPaste } from "lucide-react";
import { apiTokenize } from "@/shared/dict/api";
import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { toastApiError } from "@/shared/api/errors";
import WordDialog from "@/shared/components/WordDialog";
import TokenizedText from "@/shared/components/TokenizedText";
import { Button, Card, TextArea, cn } from "@/shared/ui";
import type { JapaneseWord } from "@/shared/dict/types";

/**
 * The TextPage component.
 *
 * @returns {JSX.Element} The Text Analyzer page.
 */
export default function TextPage() {
    const [text, setText] = useState("");
    const [words, setWords] = useState<JapaneseWord[]>([]);
    const [selected, setSelected] = useState<{ sentence: string; word: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [showFurigana, setShowFurigana] = useState(true);
    const [reading, setReading] = useState(false);
    const { mode } = useBundleSettings();

    const handleRead = async () => {
        if (text.trim() === "" || loading) return;
        setLoading(true);
        try {
            setWords(await apiTokenize(text, mode));
            setReading(true);
        } catch (e) {
            toastApiError(e);
        } finally {
            setLoading(false);
        }
    };

    const handlePaste = async () => {
        try {
            setText(await navigator.clipboard.readText());
        } catch (err) {
            console.error("Failed to read clipboard contents:", err);
        }
    };

    return (
        <div className="mx-auto min-h-[calc(100dvh_-_3.5rem)] lg:min-h-dvh w-full max-w-4xl px-4 py-8">
            <h1 className="mb-6 font-display text-3xl text-ink">Text Analyzer</h1>

            {reading ? (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <Button variant="secondary" size="sm" onClick={() => setReading(false)}>
                            <ArrowLeft size={15} /> Back To Editor
                        </Button>
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
                </div>
            ) : (
                <div className="space-y-4">
                    <TextArea
                        lang="ja"
                        className="min-h-[60vh] text-lg leading-relaxed"
                        placeholder="Paste Japanese Text Here ..."
                        value={text}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                            setText(e.target.value)
                        }
                    />
                    <div className="flex justify-between">
                        <Button variant="secondary" onClick={handlePaste}>
                            <ClipboardPaste size={16} /> Paste
                        </Button>
                        <Button onClick={handleRead} loading={loading} disabled={!text.trim()}>
                            Read
                        </Button>
                    </div>
                </div>
            )}

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
