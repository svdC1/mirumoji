# mirumoji

[![PyPI](https://img.shields.io/pypi/v/mirumoji?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/mirumoji/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat)](https://github.com/svdC1/mirumoji/blob/main/.github/LICENSE)
[![Docs](https://img.shields.io/badge/docs-lightgrey?style=flat&logo=materialformkdocs&logoColor=black&logoSize=auto)](https://svdc1.github.io/mirumoji/docs)
[![Docker Pulls](https://img.shields.io/docker/pulls/svdc1/mirumoji?style=flat&logo=docker&logoColor=white)](https://hub.docker.com/r/svdc1/mirumoji)
[![Quality](https://img.shields.io/github/actions/workflow/status/svdC1/mirumoji/release.yaml?branch=main&style=flat&logo=githubactions&logoColor=white&label=quality)](https://github.com/svdC1/mirumoji/actions/workflows/release.yaml)

An open-source, self-hosted **Japanese immersion toolkit**. Drop in a video, an
anime episode, a drama, or an audio clip and Mirumoji gives you clickable
tokenized subtitles with instant dictionary lookups, Whisper-powered
transcription, SRT generation, clip saving, and one-click Anki export. All
running locally in Docker, with optional cloud GPU and LLM features

<p align="center">
  <img src="https://github.com/svdC1/mirumoji/blob/main/.github/assets/player_example.gif?raw=true" alt="Mirumoji demo" width="100%">
</p>

---

## Quickstart

Mirumoji runs as a local `Docker Compose Application`. The quickest way to start is to download the
`Desktop Launcher` for your platform

### Detailed Walkthroughs


- Full Walkthrough &rarr; [`GUI Setup`](https://svdc1.github.io/mirumoji/docs/setup/gui/)

- CLI Setup Walkthrough &rarr; [`CLI Setup`](https://svdc1.github.io/mirumoji/docs/setup/cli/)

- Manual Setup Walkthrough &rarr; [`Manual Setup`](https://svdc1.github.io/mirumoji/docs/setup/manual/)

---

## Features

<table>
  <tr>
    <td><b>Interactive Player</b></td>
    <td>Load any video and <code>.srt</code> subtitles for clickable, tokenized Japanese lines with instant dictionary pop-ups</td>
  </tr>
  <tr>
    <td><b>Transcription &amp; SRT</b></td>
    <td>Generate subtitles and transcribe audio with <a href="https://github.com/SYSTRAN/faster-whisper"><code>faster-whisper</code></a>, on a <a href="https://svdc1.github.io/mirumoji/docs/guides/gpu/"><code>local or cloud GPU</code></a></td>
  </tr>
  <tr>
    <td><b>Dictionary &amp; Analyzer</b></td>
    <td>Wildcard dictionary search (<a href="https://github.com/svdC1/kotobase"><code>kotobase</code></a>) + a paste-in text analyzer with furigana</td>
  </tr>
  <tr>
    <td><b>LLM Breakdowns</b></td>
    <td>Optional GPT / Claude / Gemini word &amp; sentence breakdowns with fully customizable prompts</td>
  </tr>
  <tr>
    <td><b>Clips &amp; Anki</b></td>
    <td>Save video segments with their word breakdowns and export them as an Anki deck</td>
  </tr>
  <tr>
    <td><b>Profiles</b></td>
    <td>Keep files, transcripts, clips, and LLM templates organized per profile on the server</td>
  </tr>
  <tr>
    <td><b>CLI &amp; Desktop GUI</b></td>
    <td>Run the docker compose application with <a href="https://svdc1.github.io/mirumoji/docs/cli/"><code>mirumoji up</code></a> or the <a href="https://svdc1.github.io/mirumoji/docs/setup/gui/"><code>desktop launcher</code></a></td>
  </tr>
</table>

---

## Help

<table>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs">Documentation</a></b></td>
    <td>Guides, Full Python API Reference, Full Frontend API Reference</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs/setup/">Setup Guide</a></b></td>
    <td>CLI, GUI, and Manual setup</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs/guides/gpu/">Using a GPU</a></b></td>
    <td>Local GPU vs. Modal Cloud GPU</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs/project/changelog/">Changelog</a></b></td>
    <td>Changed Between Versions</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/">Live Preview</a></b></td>
    <td>View a live preview of the frontend (not backend running)</td>
  </tr>
</table>


---

## Contributing

> Pull Requests, bug reports, and feature requests are all welcome.

> See [`CONTRIBUTING`](https://github.com/svdC1/mirumoji/blob/main/.github/CONTRIBUTING.md)
> for the dev container setup, quality gates, and PR conventions.
