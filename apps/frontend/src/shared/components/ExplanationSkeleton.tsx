/**
 * @packageDocumentation The shared loading skeleton for a streamed LLM
 * explanation: a heading bar over a few text lines, shown until the first token
 * arrives. Used by the word dialog and the transcribe chat bubble so both
 * present the same placeholder.
 */

/**
 * The ExplanationSkeleton component.
 *
 * @returns {JSX.Element} A pulsing placeholder for an explanation that is still
 *     loading.
 */
export function ExplanationSkeleton() {
    return (
        <div className="w-full space-y-4">
            <div className="h-6 w-1/3 animate-pulse rounded bg-ink/10" />
            {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-4 w-full animate-pulse rounded bg-ink/10" />
            ))}
        </div>
    );
}
