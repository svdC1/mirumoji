"""
Generates the static fixtures for the backend-free demo build

Drives a running mirumoji server over one sample clip with httpx, mimicking
every endpoint the frontend calls and recording each response + the binary
assets (the sample video, its generated SRT) into
`apps/frontend/src/demo/generated/`, so `vite build --mode demo` serves the
whole app tour with no backend

The recorded fixture keys must match what the frontend requests at runtime, so
`key_of` below mirrors `apps/frontend/src/demo/api/key.ts`

Server Configuration:
    `mirumoji dev server` starts the server directly and does not inject the
    `mirumoji config` managed environment, so the OpenAI / Modal credentials
    must be present in the active shell or a `.env` file beside the directory
    the script is run from

Usage:
    1. Start the server with `mirumoji dev server`

    2. Run the generator:
        python scripts/generate_demo_data.py
          --clip <SAMPLE_CLIP> --model <PROVIDER:MODEL>

    Pass --no-kanji-audio to skip the kanji pronunciation clips and keep the
    committed demo assets small
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode

import httpx
from rich.console import Console
from rich.theme import Theme

# On Windows the std streams default to cp1252, which cannot encode rich's
# unicode and crashes the script with a UnicodeEncodeError. Force UTF-8 on the
# streams before any output is written.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8", errors="replace")

# --- Console ---

MIRUMOJI_THEME = Theme(
    {
        "accent": "#E2533B",
        "info": "#5E83A4",
        "success": "#8AA06A",
        "danger": "bold #C8503D",
        "warning": "#D9A441",
        "muted": "#7E7567",
    }
)

console = Console(theme=MIRUMOJI_THEME, highlight=False)

# --- Curated Dictionary Landing Terms (Synced With SearchResults.tsx) ---

EXPLORE_KANJI = [
    "語",
    "食",
    "水",
    "心",
    "時",
    "見",
    "気",
    "本",
    "話",
    "学",
    "字",
    "書",
]
EXPLORE_WORDS = [
    "言葉",
    "友達",
    "時間",
    "楽しい",
    "勉強",
    "音楽",
    "映画",
    "世界",
    "夢",
    "旅行",
    "元気",
    "面白い",
    "大丈夫",
    "気持ち",
    "物語",
    "朝ご飯",
]

# --- Fixture Key Scheme (Mirror Of apps/frontend/src/demo/api/key.ts) ---

# The frontend keys most requests by method + path + sorted query. These four
# POST endpoints are keyed by a whitelisted subset of their JSON body instead,
# since the same path is called with different payloads.
BODY_KEYED = {
    "dict/tokenize": ["mode", "sentences"],
    "llm/breakdown": ["context", "focus", "sentence"],
    "llm/explain_sentence": ["sentence"],
    "llm/breakdown/preview": ["context", "focus", "prompt", "sentence"],
}

# --- Paths ---

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "apps" / "frontend"
DEMO_DIR = FRONTEND_DIR / "src" / "demo"
DEFAULT_OUT = DEMO_DIR / "generated"


# --- Key Helpers ---


def canonical_json(value: Any) -> str:
    """
    Serializes a value to whitespace-free JSON with sorted keys, matching the
    TS `canonicalJson` so a body-keyed fixture is found at runtime

    Args:
        value (Any): The value to serialize

    Returns:
        The canonical JSON string
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def key_of(method: str, url: str, body: Any = None) -> str:
    """
    Computes the fixture key for a request in the `/api`-prefixed frontend
    form, identical to the TS `keyOf` so the demo transport finds it

    Args:
        method (str): The HTTP method
        url (str): The relative API path (no `/api` prefix, as the frontend
            passes it), optionally with a query string
        body (Any): The request body, only used for the body-keyed POSTs

    Returns:
        The lookup key
    """
    m = method.upper()
    raw_path, _, raw_query = url.partition("?")
    path = raw_path.lstrip("/")

    pairs = parse_qsl(raw_query, keep_blank_values=True)
    pairs.sort(key=lambda kv: kv[0])
    query = "&".join(f"{k}={v}" for k, v in pairs)

    key = f"{m} /api/{path}" + (f"?{query}" if query else "")

    fields = BODY_KEYED.get(path)
    if fields and body is not None:
        obj = json.loads(body) if isinstance(body, str) else body
        subset = {f: obj[f] for f in fields if obj.get(f) is not None}
        key += "#" + canonical_json(subset)
    return key


# --- Fixture Accumulation + Output ---


class Fixtures:
    """
    Accumulates every recorded response, SSE stream, binary asset, canned job
    result, the in-set allowlist, and the sample manifest, and writes them as
    the JSON + asset bundle the demo transport loads
    """

    def __init__(self, out: Path) -> None:
        """
        Args:
            out (Path): The output directory (the demo `generated/` folder)
        """
        self.out = out
        self.fixtures: dict[str, dict[str, Any]] = {}
        self.sse: dict[str, str] = {}
        self.jobs: dict[str, Any] = {}
        self.inset_words: set[str] = set()
        self.inset_kanji: set[str] = set()
        self.sample: dict[str, Any] = {}

    def record(
        self,
        method: str,
        rel: str,
        resp: httpx.Response,
        body: Any = None,
    ) -> Any:
        """
        Stores a response under its frontend-form key and returns its parsed
        body, so the caller can chain off the recorded value

        Args:
            method (str): The HTTP method
            rel (str): The relative path the frontend would call
            resp (httpx.Response): The server response
            body (Any): The request body for body-keyed POSTs

        Returns:
            The parsed JSON body, or the text for a non-JSON response
        """
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            parsed: Any = resp.json()
        else:
            parsed = resp.text
        self.fixtures[key_of(method, rel, body)] = {
            "status": resp.status_code,
            "contentType": content_type,
            "body": parsed,
        }
        return parsed

    def record_stream(self, rel: str, body: Any, text: str) -> None:
        """
        Stores a raw Server-Sent Events body for the demo to replay frame by
        frame

        Args:
            rel (str): The relative path
            body (Any): The request body
            text (str): The raw SSE response body
        """
        self.sse[key_of("POST", rel, body)] = text

    def save_asset(self, media_path: str, content: bytes) -> None:
        """
        Writes a binary asset under `assets/<media_path>`, mirroring the URL
        the browser requests it from

        Args:
            media_path (str): The path below the `assets/` root (e.g.
                `api/media/profiles/demo/uploads/x.mp4`)
            content (bytes): The asset bytes
        """
        dest = self.out / "assets" / media_path.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    def write(self) -> None:
        """
        Writes every accumulated fixture file to the output directory, one JSON
        file per kind (fixtures, streams, jobs, allowlist, sample)
        """
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "fixtures.json").write_text(
            json.dumps(self.fixtures, ensure_ascii=False, indent=0),
            encoding="utf-8",
        )
        (self.out / "sse.json").write_text(
            json.dumps(self.sse, ensure_ascii=False, indent=0),
            encoding="utf-8",
        )
        (self.out / "jobs.json").write_text(
            json.dumps(self.jobs, ensure_ascii=False, indent=0),
            encoding="utf-8",
        )
        (self.out / "inset.json").write_text(
            json.dumps(
                {
                    "words": sorted(self.inset_words),
                    "kanji": sorted(self.inset_kanji),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.out / "sample.json").write_text(
            json.dumps(self.sample, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# --- Recording Driver ---


class Driver:
    """
    Calls the server the way the frontend does and records every response, so
    the saved fixtures can answer the demo's requests offline
    """

    def __init__(
        self,
        client: httpx.Client,
        fx: Fixtures,
        model: str,
        kanji_audio: bool = True,
    ) -> None:
        """
        Args:
            client (httpx.Client): The HTTP client (base URL + profile header)
            fx (Fixtures): The fixture accumulator
            model (str): The `provider:model` selector for the LLM flows
            kanji_audio (bool): Capture kanji pronunciation clips (many small
                files). Pass False to keep the demo assets small
        """
        self.client = client
        self.fx = fx
        self.model = model
        self.kanji_audio = kanji_audio

    def get(self, rel: str) -> Any:
        """
        GETs a relative path and records the response as a fixture

        Args:
            rel (str): The relative path (no `/api` prefix)

        Returns:
            The parsed response body
        """
        resp = self.client.get("/" + rel.lstrip("/"))
        return self.fx.record("GET", rel, resp)

    def post(self, rel: str, body: dict[str, Any]) -> Any:
        """
        POSTs a JSON body to a relative path and records the response, keyed by
        the body subset when the endpoint is body-keyed

        Args:
            rel (str): The relative path
            body (dict): The JSON body

        Returns:
            The parsed response body
        """
        resp = self.client.post("/" + rel.lstrip("/"), json=body)
        return self.fx.record("POST", rel, resp, body)

    def stream(self, rel: str, body: dict[str, Any]) -> None:
        """
        POSTs to a streaming endpoint and records the raw SSE body verbatim,
        for the demo to replay as a live token stream

        Args:
            rel (str): The relative path
            body (dict): The JSON body
        """
        resp = self.client.post("/" + rel.lstrip("/"), json=body, timeout=120)
        self.fx.record_stream(rel, body, resp.text)

    def download_media(self, media_url: str) -> None:
        """
        Downloads a `/media/...` asset and saves it at the `/api/media/...`
        path the browser requests, raising if the fetch fails

        Args:
            media_url (str): The server media URL (e.g. `/media/profiles/...`)
        """
        resp = self.client.get(media_url)
        resp.raise_for_status()
        self.fx.save_asset("api" + media_url, resp.content)

    def run_job(
        self,
        job_type: str,
        file_id: str,
        opts: dict[str, Any],
    ) -> Any:
        """
        Submits a long-running job, polls it once a second to completion, and
        stores its result by type for the demo's job simulator to hand back

        Args:
            job_type (str): The operation type
                (generate_srt / transcribe / ...)
            file_id (str): The uploaded file id to run it on
            opts (dict): The operation options

        Returns:
            The finished job's `result`

        Raises:
            RuntimeError: If the job does not succeed
        """
        body: dict[str, Any] = {
            "type": job_type,
            "file_id": file_id,
            "opts": opts,
        }
        job = self.client.post("/jobs", json=body).json()
        job_id = job["id"]
        for _ in range(600):
            job = self.client.get(f"/jobs/{job_id}").json()
            if job["status"] in ("succeeded", "failed", "cancelled"):
                break
            time.sleep(1)
        if job["status"] != "succeeded":
            raise RuntimeError(
                f"Job {job_type} did not succeed: {job.get('error')}"
            )
        self.fx.jobs[job_type] = job["result"]
        return job["result"]

    # --- Dictionary ---

    def query_word(
        self,
        word: str,
        reading: str | None = None,
        pos: str | None = None,
    ) -> Any:
        """
        Records a dictionary lookup and marks the word in-set, so its link
        stays enabled while off-fixture words are gated

        Args:
            word (str): The word or wildcard pattern
            reading (str | None): Optional reading hint
            pos (str | None): Optional part-of-speech hint

        Returns:
            The lookup result
        """
        params = {"word": word, "wildcard": "false"}
        if reading:
            params["reading"] = reading
        if pos:
            params["pos"] = pos
        self.fx.inset_words.add(word)
        return self.get("dict/query?" + urlencode(params))

    def capture_kanji(self, literal: str) -> None:
        """
        Records a kanji's full detail view (info, strokes, words, sentences,
        and its audio clips unless disabled) and marks it in-set, skipping a
        kanji already captured

        Args:
            literal (str): The kanji character
        """
        if literal in self.fx.inset_kanji:
            return
        self.fx.inset_kanji.add(literal)
        self.get("dict/kanji?" + urlencode({"literal": literal}))
        self.get("dict/kanji/strokes?" + urlencode({"literal": literal}))
        self.get(
            "dict/kanji/words?"
            + urlencode({"literal": literal, "limit": "50"})
        )
        self.get(
            "dict/kanji/sentences?"
            + urlencode({"literal": literal, "limit": "10"})
        )
        # The pronunciation clips are many small files. When enabled, record
        # the listing and each clip as the static asset the demo serves at
        # /api/dict-audio/<literal>-<clip>.mp3. Otherwise the KanjiView hides
        # its audio section (apiKanjiAudio falls back to no clips on a 404)
        if not self.kanji_audio:
            return
        audio = self.get(
            "dict/kanji/audio?" + urlencode({"literal": literal})
        )
        clips = audio.get("clips", []) if isinstance(audio, dict) else []
        for clip in clips:
            resp = self.client.get(
                "/dict/kanji/audio/clip?"
                + urlencode({"literal": literal, "clip": clip})
            )
            if resp.status_code == 200:
                self.fx.save_asset(
                    f"api/dict-audio/{literal}-{clip}.mp3", resp.content
                )

    def capture_sentence(
        self,
        sentence: str,
        context: str | None = None,
        also_no_context: bool = False,
    ) -> None:
        """
        Records everything a word popup needs for one sentence: it tokenizes
        the sentence in every bundling mode, then for each unique lemma
        captures its dict lookup, any kanji it contains, and its breakdown

        Args:
            sentence (str): The sentence a word is clicked in
            context (str | None): Surrounding-cue context for a player
                breakdown, or None for a text-page / transcribe breakdown
            also_no_context (bool): Also record a no-context breakdown, for the
                sample sentence opened from both the player and the text page
        """
        variants: dict[tuple[str, str | None, str | None], None] = {}
        for mode in ("words", "grammar", "morphemes"):
            words = self.get(
                "dict/tokenize?"
                + urlencode({"sentence": sentence, "mode": mode})
            )
            for w in words or []:
                lemma = w.get("lemma") or w.get("surface") or ""
                if lemma:
                    reading = w.get("reading") or None
                    pos = w.get("pos") or None
                    variants[(lemma, reading, pos)] = None

        broken_down: set[str] = set()
        for lemma, reading, pos in variants:
            self.query_word(lemma, reading, pos)
            if lemma in broken_down:
                continue
            broken_down.add(lemma)
            for ch in lemma:
                if "一" <= ch <= "鿿":
                    self.capture_kanji(ch)
            body = {"sentence": sentence, "focus": lemma, "model": self.model}
            if context is not None:
                self.stream("llm/breakdown", {**body, "context": context})
                if also_no_context:
                    self.stream("llm/breakdown", body)
            else:
                self.stream("llm/breakdown", body)


# --- Cue Parsing ---


def parse_cues(srt_content: str) -> list[str]:
    """
    Splits generated SRT content into one sentence per cue, joining a
    multi-line cue the same way the player's `useCues` parser does, so the
    tokenize fixture recorded here matches at runtime

    Args:
        srt_content (str): The raw SRT file body

    Returns:
        The cue sentences in order, blank cues dropped
    """
    cues: list[str] = []
    for block in srt_content.split("\n\n"):
        lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        if len(lines) >= 3:
            text = "\n".join(lines[2:]).strip()
            if text:
                cues.append(text)
    return cues


# --- Recording Phases ---


def record_health(drv: Driver) -> None:
    """
    Records the startup capability probe: the health and provider endpoints the
    app fetches on load to decide which features to enable

    Args:
        drv (Driver): The recording driver
    """
    with console.status(
        "Recording Server Capabilities", spinner_style="accent"
    ):
        drv.get("health/status")
        drv.get("health/system")
        drv.get("llm/providers")


def record_llm(drv: Driver, model: str) -> None:
    """
    Records the provider's model list and installs a breakdown template, so the
    demo enables the LLM features that stay disabled until a template exists

    Args:
        drv (Driver): The recording driver
        model (str): The provider:model selector, whose provider half selects
            the model list and whose full value is stored on the template
    """
    provider = model.split(":", 1)[0]
    with console.status("Recording LLM Setup", spinner_style="accent"):
        drv.get("llm/models?" + urlencode({"provider": provider}))
        # A template must exist for the frontend to enable the LLM features
        drv.post(
            "profiles/template",
            {
                "sys_msg": "You are a concise Japanese tutor.",
                "prompt": "Break down {focus} in: {sentence}",
                "model": model,
            },
        )


def upload_clip(drv: Driver, clip_path: Path) -> dict[str, Any]:
    """
    Uploads the sample clip as the demo profile's only file, the way the
    Transcribe uploader posts raw bytes, and returns the created file record

    Args:
        drv (Driver): The recording driver
        clip_path (Path): The local sample clip

    Returns:
        The uploaded file record (its id and media url)
    """
    with console.status("Uploading Sample Clip", spinner_style="accent"):
        up: dict[str, Any] = drv.client.post(
            "/profiles/files",
            content=clip_path.read_bytes(),
            headers={"X-File-Name": clip_path.name},
        ).json()
    return up


def process_clip(
    drv: Driver,
    up: dict[str, Any],
    clip_name: str,
) -> tuple[list[str], str]:
    """
    Runs the subtitle and transcript jobs and records the player sample: it
    downloads the video, generates and downloads the SRT, transcribes the
    audio, and stores the video / SRT / transcript / first-cue text in the
    manifest the demo preloads

    Args:
        drv (Driver): The recording driver
        up (dict): The uploaded file record from `upload_clip`
        clip_name (str): The sample clip filename, for the manifest

    Returns:
        The SRT cue sentences and the transcript text the breakdown phases run
        over
    """
    status = "Generating Subtitles And Transcribing"
    with console.status(status, spinner_style="accent"):
        file_id = up["id"]
        drv.download_media(up["url"])

        srt = drv.run_job("generate_srt", file_id, {})
        drv.download_media(srt["srt_url"])
        transcribe = drv.run_job("transcribe", file_id, {"clean_audio": False})

        cues = parse_cues(srt["srt_content"])
        drv.fx.sample.update(
            {
                "video": {
                    "url": up["url"],
                    "name": clip_name,
                    "fileId": file_id,
                },
                "srt": {
                    "url": srt["srt_url"],
                    "name": Path(srt["srt_url"]).name,
                    "fileId": srt["srt_file_id"],
                },
                "transcript": transcribe["transcript"],
                "text": cues[0] if cues else "",
            }
        )
    return cues, transcribe["transcript"]


def record_subtitles(drv: Driver, cues: list[str]) -> None:
    """
    Records the player's subtitle tokenization and per-word breakdowns: it
    batch-tokenizes every cue in all three modes the way the player
    pre-tokenizes on load, then captures the lookups and breakdowns each word
    produces, passing the surrounding-cue window the player sends as {context}

    Args:
        drv (Driver): The recording driver
        cues (list[str]): The ordered cue sentences from the SRT
    """
    context_window = 3
    with console.status(
        "Recording Subtitles", spinner_style="accent"
    ) as status:
        for mode in ("words", "grammar", "morphemes"):
            drv.post("dict/tokenize", {"sentences": cues, "mode": mode})
        for i, cue in enumerate(cues):
            status.update(
                f"Recording Subtitle Breakdowns ({i + 1}/{len(cues)})"
            )
            context = "\n".join(
                cues[max(0, i - context_window) : i + context_window + 1]
            )
            drv.capture_sentence(
                cue, context=context, also_no_context=(i == 0)
            )


def record_transcript(drv: Driver, transcript: str, model: str) -> None:
    """
    Records the Transcribe page's flow

    It tokenizes and breaks down the whole transcript with
    no cue context, then captures its full-sentence explanation

    Args:
        drv (Driver): The recording driver
        transcript (str): The transcribed text
        model (str): The provider:model selector for the explanation
    """
    if not transcript:
        return
    with console.status("Recording Transcript", spinner_style="accent"):
        drv.capture_sentence(transcript)
        drv.stream(
            "llm/explain_sentence",
            {"sentence": transcript, "model": model},
        )


def record_dictionary(drv: Driver) -> None:
    """
    Records the curated dictionary landing set (the kanji and words the hub
    floats, kept in sync with SearchResults.tsx) plus the radical inventory, so
    browsing the sample dictionary works offline

    Args:
        drv (Driver): The recording driver
    """
    total = len(EXPLORE_KANJI) + len(EXPLORE_WORDS)
    with console.status(
        "Recording Dictionary", spinner_style="accent"
    ) as status:
        done = 0
        for k in EXPLORE_KANJI:
            drv.capture_kanji(k)
            done += 1
            status.update(f"Recording Dictionary ({done}/{total})")
        for word in EXPLORE_WORDS:
            drv.query_word(word)
            done += 1
            status.update(f"Recording Dictionary ({done}/{total})")
        drv.get("dict/radicals")


def record_profile(drv: Driver) -> None:
    """
    Records the profile listings the dashboard reads (the uploaded file, the
    transcript, the saved clips, the anki export, and the active template), so
    the demo dashboard renders fully populated

    Args:
        drv (Driver): The recording driver
    """
    with console.status("Recording Profile Listings", spinner_style="accent"):
        drv.get("profiles/files")
        drv.get("profiles/transcripts")
        drv.get("profiles/clips")
        drv.get("profiles/anki_export")
        drv.get("profiles/template")


# --- Entry Point ---


def parse_args() -> argparse.Namespace:
    """
    Parses the generator's command-line arguments

    Returns:
        The parsed arguments (clip, server, profile, model, out, kanji_audio)
    """
    parser = argparse.ArgumentParser(description="Generate Demo Fixtures")
    parser.add_argument(
        "--clip",
        required=True,
        type=Path,
        help="The sample clip to drive the demo",
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="The running mirumoji server base URL",
    )
    parser.add_argument(
        "--profile",
        default="demo",
        help="The profile id to record under",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="The provider:model selector for the LLM flows",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="The generated fixtures output directory",
    )
    parser.add_argument(
        "--no-kanji-audio",
        action="store_false",
        dest="kanji_audio",
        help="Skip kanji pronunciation clips to keep the assets small",
    )
    return parser.parse_args()


def main() -> None:
    """
    Drives the server through the frontend's flows and writes the fixtures,
    running each recording phase in the order a visitor exercises the app then
    writing the generated bundle
    """
    args = parse_args()
    fx = Fixtures(args.out)
    with httpx.Client(
        base_url=args.server,
        headers={"X-Profile-ID": args.profile},
        timeout=60,
    ) as client:
        drv = Driver(client, fx, args.model, kanji_audio=args.kanji_audio)

        record_health(drv)
        record_llm(drv, args.model)
        up = upload_clip(drv, args.clip)
        cues, transcript = process_clip(drv, up, args.clip.name)
        record_subtitles(drv, cues)
        record_transcript(drv, transcript, args.model)
        record_dictionary(drv)
        record_profile(drv)

    fx.write()
    console.print(
        f"Wrote {len(fx.fixtures)} Fixtures, {len(fx.sse)} Streams, "
        f"{len(fx.inset_kanji)} Kanji, And {len(fx.inset_words)} Words "
        f"To '{args.out}'",
        style="success",
    )


if __name__ == "__main__":
    main()
