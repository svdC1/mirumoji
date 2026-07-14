# mirumoji

[![PyPI](https://img.shields.io/pypi/v/mirumoji?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/mirumoji/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat)](https://github.com/svdC1/mirumoji/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-lightgrey?style=flat&logo=materialformkdocs&logoColor=black&logoSize=auto)](https://svdc1.github.io/mirumoji/docs)
[![Docker Pulls](https://img.shields.io/docker/pulls/svdc1/mirumoji?style=flat&logo=docker&logoColor=white)](https://hub.docker.com/r/svdc1/mirumoji)
[![Release Action](https://img.shields.io/github/actions/workflow/status/svdC1/mirumoji/release.yaml?style=flat&logo=githubactions&logoColor=white&label=release)](https://github.com/svdC1/mirumoji/actions/workflows/release.yaml)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/svdc1/mirumoji/total?style=flat&logo=github&label=GitHub%20Downloads)]()


An open-source, self-hosted `Japanese Immersion Toolkit`

Drop in a video, an anime episode, a drama, or an audio clip and Mirumoji gives
you clickable tokenized subtitles with instant dictionary lookups whisper-powered
subtitle generation, clip saving, and Anki export. All running locally in Docker,
with optional cloud GPU and LLM features

<p align="center">
  <img src="https://github.com/svdC1/mirumoji/blob/main/.github/assets/player_example.gif?raw=true" alt="Mirumoji Demo" width="100%"/>
</p>

---

## Quickstart

Mirumoji runs as a local [`Docker Compose Application`](https://docs.docker.com/compose/)

The quickest way to start is to download the `Desktop Launcher` for your platform and follow
the [`Setup Walkthrough`](https://svdc1.github.io/mirumoji/docs/setup/gui/)

### Alternatives

You can also setup Mirumoji [`Manually`](https://svdc1.github.io/mirumoji/docs/setup/manual/), or through its [`CLI`](https://svdc1.github.io/mirumoji/docs/setup/cli/)

---

## Features

<table>
  <tr>
    <td><b>Interactive Player</b></td>
    <td>Load Videos + Subtitles For Clickable, Tokenized Japanese Lines With Dictionary Pop-Ups</td>
  </tr>
  <tr>
    <td><b>Transcription</b></td>
    <td>Generate Subtitles + Transcribe Audio with <a href="https://github.com/SYSTRAN/faster-whisper"><code>faster-whisper</code></a>, on a <a href="https://svdc1.github.io/mirumoji/docs/guides/gpu/"><code>Local / Cloud GPU</code></a></td>
  </tr>
  <tr>
    <td><b>Dictionary</b></td>
    <td>Wildcard dictionary search (<a href="https://github.com/svdC1/kotobase"><code>kotobase</code></a>) + a paste-in text analyzer with furigana</td>
  </tr>
  <tr>
    <td><b>LLM</b></td>
    <td>Optionally Use Gemini / Claude / GPT API Keys (Or Your Own Local LLM Server) To Generate Sentence Breakdowns With Fully Customizable Prompts</td>
  </tr>
  <tr>
    <td><b>Clips + Anki</b></td>
    <td>Save Video Segments With Their Word Breakdowns And Export Them As An Anki Deck</td>
  </tr>
  <tr>
    <td><b>Profiles</b></td>
    <td>Keep Generated Files, Transcripts, Clips, and LLM Templates Organized Per Profile On The Server</td>
  </tr>
  <tr>
    <td><b>Launcher</b></td>
    <td>Easily Run The Docker Compose Application Via The <a href="https://svdc1.github.io/mirumoji/docs/cli/"><code>CLI</code></a> Or The <a href="https://svdc1.github.io/mirumoji/docs/setup/gui/"><code>Desktop Launcher</code></a></td>
  </tr>
</table>

---

## Help

<table>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs">Documentation</a></b></td>
    <td>Guides + Full Backend / Frontend API Reference</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs/setup/">Setup Guide</a></b></td>
    <td>CLI + GUI + Manual setup</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs/guides/gpu/">Using a GPU</a></b></td>
    <td>Local GPU x Modal Cloud GPU</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/docs/project/changelog/">Changelog</a></b></td>
    <td>What Changed Between Versions</td>
  </tr>
  <tr>
    <td><b><a href="https://svdc1.github.io/mirumoji/">Demo</a></b></td>
    <td>Test A Limited Preview</td>
  </tr>
</table>


---

## Contributing

- All contributions are welcome

- See [`CONTRIBUTING`](https://svdc1.github.io/mirumoji/docs/project/contributing) for more information on how to
  contribute
