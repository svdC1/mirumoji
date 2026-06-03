/**
 * @packageDocumentation The Dictionary page: search a word or wildcard pattern,
 * browse wildcard results, and drill into a word's full entry.
 */

import { useState } from "react";
import { Search } from "lucide-react";
import { apiDictQuery, isEmptyDict } from "@/shared/dict/api";
import { Button, Input, EmptyState } from "@/shared/ui";
import { ComprehensiveEntryCard, WildcardResults } from "@/shared/components/DictDisplays";
import type { KotobaseData } from "@/shared/dict/types";

/**
 * The DictionaryPage component.
 *
 * @returns {JSX.Element} The dictionary page.
 */
export default function DictionaryPage() {
    const [pattern, setPattern] = useState("");
    const [wildcardResult, setWildcardResult] = useState<KotobaseData | null>(null);
    const [selectedWordResult, setSelectedWordResult] = useState<KotobaseData | null>(null);
    const [selectedWord, setSelectedWord] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!pattern) return;
        setLoading(true);
        setError(null);
        setSelectedWordResult(null);
        setWildcardResult(null);
        try {
            const result = await apiDictQuery(pattern, true);
            if (isEmptyDict(result)) {
                setError(`No Results For “${pattern}”`);
            } else {
                setWildcardResult(result);
            }
        } catch (err) {
            setError("Failed To Fetch Results");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleWordSelect = async (word: string) => {
        setLoading(true);
        setError(null);
        setSelectedWord(word);
        try {
            const result = await apiDictQuery(word);
            setSelectedWordResult(isEmptyDict(result) ? null : result);
        } catch (err) {
            setError("Failed To Fetch Word Details");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mx-auto min-h-screen w-full max-w-3xl px-4 py-8">
            <h1 className="mb-6 text-center font-display text-3xl text-ink">Dictionary</h1>

            <div className="mx-auto mb-6 flex max-w-xl gap-2">
                <Input
                    lang="ja"
                    value={pattern}
                    onChange={(e) => setPattern(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Word Or Wildcard Pattern (e.g. *字*)"
                />
                <Button onClick={handleSearch} loading={loading} className="shrink-0">
                    <Search size={18} />
                </Button>
            </div>

            {error && <EmptyState title="Nothing Found" description={error} />}

            {wildcardResult && !selectedWordResult && (
                <WildcardResults results={wildcardResult} onWordSelect={handleWordSelect} />
            )}

            {selectedWordResult && (
                <div className="mx-auto mt-6 max-w-2xl space-y-4">
                    <ComprehensiveEntryCard
                        word={selectedWord}
                        jmdictEntries={selectedWordResult.jmentries}
                        jmnedictEntries={selectedWordResult.jmnentries}
                        kanjiInfo={selectedWordResult.kanji}
                        examples={selectedWordResult.examples}
                    />
                    <Button
                        variant="secondary"
                        className="w-full"
                        onClick={() => setSelectedWordResult(null)}
                    >
                        Close
                    </Button>
                </div>
            )}
        </div>
    );
}
