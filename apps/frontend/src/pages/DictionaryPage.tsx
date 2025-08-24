/**
 * @packageDocumentation This file contains the DictionaryPage component, which allows users to search the dictionary
 * for words and kanji using wildcard patterns. It displays results in a tabbed interface and shows
 * detailed information when a result is selected.
 */

import { useState } from "react";
import {
    apiWildcardQuery,
    apiWordQuery,
    filterDictWildcardLookup,
    filterDictLookup,
} from "../services/dictApi";
import { SearchIcon } from "lucide-react";
import { DictLookup, DictWildcardLookup } from "../types/types";
import {
    ComprehensiveEntryCard,
    WildcardResults,
} from "../components/DictDisplays";

/**
 * Renders the main dictionary search page.
 * @returns {JSX.Element} The dictionary page component.
 */
export const DictionaryPage = () => {
    const [pattern, setPattern] = useState("");
    const [wildcardResult, setWildcardResult] =
        useState<DictWildcardLookup | null>(null);
    const [selectedWordResult, setSelectedWordResult] =
        useState<DictLookup | null>(null);
    const [selectedWord, setSelectedWord] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    /**
     * Handles the search for a wildcard pattern.
     */
    const handleSearch = async () => {
        if (!pattern) return;
        setIsLoading(true);
        setError(null);
        setSelectedWordResult(null);
        setWildcardResult(null);
        try {
            const result = await apiWildcardQuery(pattern);
            const filteredResult = filterDictWildcardLookup(result);
            setWildcardResult(filteredResult);
            if (!filteredResult) {
                setError("No results found for your query.");
            }
        } catch (err) {
            setError("Failed to fetch dictionary results.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    /**
     * Handles the selection of a word from the wildcard results to fetch its detailed information.
     * @param {string} word - The word to look up.
     */
    const handleWordSelect = async (word: string) => {
        setIsLoading(true);
        setError(null);
        setSelectedWord(word);
        try {
            const result = await apiWordQuery(word);
            setSelectedWordResult(filterDictLookup(result));
        } catch (err) {
            setError("Failed to fetch details for the selected word.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="container select-none mx-auto p-4 sm:p-6 text-white min-h-screen">
            <h1 className="text-4xl font-bold mb-6 text-center text-indigo-400">
                Dictionary
            </h1>
            <div className="flex flex-col justify-center sm:flex-row gap-2 mb-6 max-w-xl mx-auto">
                <input
                    type="text"
                    value={pattern}
                    onChange={(e) => setPattern(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Word or wildcard pattern (e.g. *字*)"
                    className="flex-grow text-center bg-neutral-800 border border-neutral-700 rounded-md py-2 px-4 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                />
                <button
                    onClick={handleSearch}
                    disabled={isLoading}
                    className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded-md transition-colors duration-200"
                >
                    {isLoading ? "..." : <SearchIcon size={20}/>}
                </button>
            </div>

            {error && <p className="text-center text-red-400 mt-4">{error}</p>}

            {wildcardResult && !selectedWordResult && (
                <WildcardResults
                    results={wildcardResult}
                    onWordSelect={handleWordSelect}
                />
            )}

            {selectedWordResult && (
                <div className="mt-6 max-w-2xl mx-auto">
                    <ComprehensiveEntryCard
                        word={selectedWord}
                        jmdictEntries={selectedWordResult.jmentries}
                        jmnedictEntries={selectedWordResult.jmnentries}
                        kanjiInfo={selectedWordResult.kanji}
                        examples={selectedWordResult.examples}
                    />
                    <button
                        onClick={() => setSelectedWordResult(null)}
                        className="mt-4 bg-neutral-700 hover:bg-neutral-600 text-white font-bold py-2 px-4 rounded-md w-full"
                    >
                        Close
                    </button>
                </div>
            )}
        </div>
    );
};
