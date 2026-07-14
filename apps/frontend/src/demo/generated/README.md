# Generated Demo Fixtures

These files are produced by [`scripts/generate_demo_data.py`](../../../../../scripts/generate_demo_data.py)
by driving a real Mirumoji server once over a sample clip

They are committed so that
the `--mode demo` build runs with no backend

## Files

- `fixtures.json` &rarr; recorded `apiFetch` responses, keyed by the shared scheme in [`../api/key.ts`](../api/key.ts)

- `sse.json` &rarr; recorded LLM Server-Sent Events streams (raw body text), keyed the same way

- `jobs.json` &rarr; canned job results per operation type, replayed by the job simulator

- `inset.json` &rarr; the allowlist of captured dictionary words/kanji, for disabling out-of-set links

- `sample.json` &rarr; the pre-loaded sample descriptor (video + subtitle URLs and ids) the demo loads on startup

- `assets/api/...` &rarr; recorded binary assets (media, clips, audio), copied to the build's `/api/...` root
