# Changelog

All notable changes to this project will be documented in this file

The format is based on [`Keep a Changelog`](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [`Semantic Versioning`](https://semver.org/spec/v2.0.0.html)
starting from **`v3.0.0`**

???+ warning "Pre-`v3.0.0`"
    - `v1.0.0` – `v2.6.0` used semver-like tags but without a formal policy or changelog
    - Their history is preserved in [`GitHub Releases`](https://github.com/svdC1/mirumoji/releases)

???+ danger "`v3.0.0` Is `v0.1.0`"
    - Since `Mirumoji` underwent a complete refactoring / rewriting and has only started following `Semantic Versioning` in `v3.0.0`, it should be treated as a initial release

    - This means that the following `v3.x` versions **MIGHT STILL CONTAIN BREAKING CHANGES**

    - These changes will be clearly documented in this changelog

---

## [`3.7.1`](https://github.com/svdC1/mirumoji/releases/tag/v3.7.1) - 2026-07-21

This release makes the packaged desktop `GUI` read the `Modal`-hosted app's
logs without needing a `Python` interpreter on the machine, and makes
deletions feel instant on a hosted deployment by removing rows optimistically
instead of waiting for the server round trip. It has no breaking changes

### Fixed

- `Launcher` &rarr; Reading the `Modal`-hosted app's logs from the packaged
  desktop `GUI` failed with a `No Python Interpreter` message because the logs
  were the one `Modal` action that still shelled out to the `modal` `CLI`.
  Logs are now read through the `SDK` in-process like the stop and volume actions,
  with the `CLI` kept as a fallback, and a followed stream polls in-process when no
  `CLI` can be spawned

- `Frontend` &rarr; Deleting a file, transcript, or clip only updated the
  interface after the delete and a follow-up list refetch had both completed,
  which on a hosted deployment left the row visible for noticeable time after
  the click. Rows now leave the list immediately and are restored if the
  delete turns out to have failed

## [`3.7.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.7.0) - 2026-07-20

This release stops a local video being uploaded once per player action,
makes the interface report what actually happened instead of assuming success,
and fixes two `GUI` `Modal` actions that opened a second window and hung forever.
It also adds upload cancellation, double-tap seeking, a `Modal` log source in
the `GUI`, and quiets a large amount of misleading `ERROR` noise in the host logs.
It has no breaking changes

### Added

- `Frontend` &rarr; An in-flight upload can be cancelled from the task tray, which
  stops the transfer and drops the row rather than leaving it to finish

- `Frontend` &rarr; Double-tapping the left or right side of the player skips 5
  seconds, matching the arrow keys

- `Launcher` &rarr; The `GUI` Logs panel reads the `Modal`-hosted app's logs as
  well as the local `Docker Compose` stack, chosen with a new Source control,
  with the same tail and follow controls

### Fixed

- `Frontend` &rarr; Running two player actions on the same device video uploaded
  the whole file twice. Clicking `Generate SRT` and `To MP4` on one video sent it
  in full on each action and left two profile files sharing a name. An action
  started while an upload is still running now joins that upload instead of
  beginning its own

- `Frontend` &rarr; A player action on a file that had since been deleted reported
  success while the server rejected it, and no task ever appeared. Actions now
  wait for the result and report the real outcome, naming a deleted file rather
  than failing silently

- `Frontend` &rarr; A profile video deleted while it was loaded showed the
  `Convert To Play` prompt, which could never succeed. A deleted file is now told
  apart from a container the browser cannot decode, and clears the player

- `Frontend` &rarr; Deleting a file left the jobs it removed on the tasks
  dashboard, where deleting them failed with a not-found error that could not be
  cleared. Those jobs are dropped as the file is deleted, and any task that is
  already gone server-side clears instead of erroring. Transcripts and clips are
  refreshed the same way

- `Frontend` &rarr; On `iOS` a recording's audio slider never moved and its length
  showed as `0:00`, because a browser recording carries no duration until it has
  been read in full. The duration is now picked up when it becomes known

- `Frontend` &rarr; On `iOS` the file dialog stopped responding after a few
  uploads. Picking the same file twice raised no event, and each preview held its
  audio in memory for the rest of the session, so repeated picks exhausted the
  browser. File inputs now reset between picks and previews are released once
  nothing shows them

- `Launcher` &rarr; `Down` and `Download Data` in the `GUI`'s `Modal Host` panel
  opened a second application window and hung indefinitely. The packaged app
  embeds `Python`, so the `modal` CLI could not be run the way those two actions
  ran it. `Download Data` now streams the volume directly and `Down` stops the app
  in-process, so neither spawns anything

- `Launcher` &rarr; The `Modal Host` panel's mode pills kept whatever was true
  when the panel first opened, so a change made in `Settings` was not reflected on
  returning to it. They are re-read on every visit, as the `Dashboard` already did

- `CLI` &rarr; `mirumoji modal logs --tail` accepted counts the `modal` CLI
  rejects, surfacing its raw usage text. It is bounded to the accepted range, also
  takes `-t`, and states that it does not apply with `--follow`

- `Server` &rarr; Video conversions, saved clips and `Anki` exports were mirrored
  to the `Modal` volume repeatedly while they were still being written, re-copying
  the same output several times over. Each is now written aside and moved into
  place when finished, so it is copied once

- `Server` &rarr; Ordinary outcomes were logged as failures. A stale reference
  from the interface produced a database `ERROR` and a full traceback on every
  attempt, burying real problems. Only genuine failures are logged that way now

- `Server` &rarr; Deleting a task that was already gone failed instead of
  succeeding, which left the interface unable to clear it. Deleting a task that no
  longer exists now succeeds

- `Server` &rarr; A cancelled upload was recorded as a server failure rather than
  as the deliberate action it is

---

## [`3.6.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.6.0) - 2026-07-18

This release hardens the `Modal`-hosted deploy and adds new host compute modes.
It makes host data durable against a mid-write preemption, adds an offload-less
GPU host and a non-preemptible CPU host, adds a `modal logs` command, and reworks
the image-version pin into a single deploy-time option applied across every image
command. It also fixes a `Windows` crash in the `modal` CLI, several volume-sync
inefficiencies, a stop that could not delete the volume, and a host-mode toggle
that silently did nothing

### Breaking Changes
  - The image-version pin is renamed. The `MIRUMOJI_VERSION` config key becomes
    `MIRUMOJI_IMAGE_VERSION` and the `--version` command flag becomes
    `--image-version`, with no compatibility alias, so update any script or
    config that pinned an image version

  - The global `mirumoji --version` *(which prints the installed package
    version)* is unchanged

### Added

- `Launcher` &rarr; An offload-less GPU host. Setting `MIRUMOJI_HOST_ON_GPU=1`
  *(or passing `--host-on-gpu`)* runs the whole host on a GPU with the `local`
  whisper backend in-process, on the `MIRUMOJI_MODAL_GPU` type, so there is a
  single always-warm app and no on-demand offload worker

- `Launcher` &rarr; A non-preemptible CPU host. `MIRUMOJI_HOST_NONPREEMPTIBLE=1`
  *(or `--nonpreemptible`)* runs the host on guaranteed capacity at a 3x price, so
  a spot reclaim never restarts it mid-job. It cannot be combined with a GPU host,
  which `Modal` does not allow

- `Launcher` &rarr; A `mirumoji modal logs` command that fetches the hosted app's
  recent logs *(`--tail`)* or live-follows them *(`--follow`, stopped with
  Ctrl+C)*

- `Launcher` &rarr; `--image-version` is honored by every image command *(`up`,
  `pull`, `render`, `build`, `modal deploy`)*, and `build` now checks out the
  matching `v<version>` source tag

### Changed

- `Launcher` &rarr; The image-version pin is a single deploy-time option resolved
  in one place *(flag, then config, then shell, then the installed version)* and
  is never injected into a container. See the breaking note above for the
  `MIRUMOJI_VERSION` / `--version` rename

### Fixed

- `Launcher` &rarr; A `Fix-SRT` *(or any media write)* could survive a mid-write
  `Modal` preemption as a database row whose media file was missing. Media writes
  are now atomic *(written to a temporary sibling and renamed into place)* and the
  background volume sync is ordered, so the volume never holds a row referencing a
  file that has not been mirrored yet

- `Launcher` &rarr; The `modal` CLI could crash partway through on `Windows` when
  its output held a character the legacy `cp1252` console could not encode *(a box
  border or a Japanese filename)*, so `download-data` and log fetching could fail.
  Its subprocesses now encode their output as `utf-8`

- `Launcher` &rarr; `mirumoji modal down --volume` could not delete the data
  volume once the app had stopped or failed to stop. A stop failure is now a
  warning, so the volume is still deleted

- `Launcher` &rarr; The host volume sync thrashed the `FUSE` layer, re-copying a
  transcription's growing scratch audio and the streamed-back converted video many
  times over. Transient scratch is no longer mirrored, and the offload worker's
  result is written atomically, so each file is copied once

---

## [`3.5.1`](https://github.com/svdC1/mirumoji/releases/tag/v3.5.1) - 2026-07-16

This release fixes several issues with the `Modal`-hosted deploy. It moves media serving and the
database off the volume's slow network layer so hosted video plays smoothly,
makes shutdown and spot preemption exit cleanly, completes the `PWA` install
behind the host login on `iOS`, and stops the installed app from re-prompting for
the password. It also fixes a previously uncaught clip-recording hang on `iOS`.
It has no breaking changes

### Fixed

- `Launcher` &rarr; Besides an overall poor application performance when hosting on `Modal`,
  video playback stalled and clip recording failed. The `Modal` host served media and ran
  the database directly off the persistent volume's `FUSE` layer, whose per-request random
  reads take seconds, so every seek re-buffered and the browser recorder
  *(which captures live playback)* had no continuous stream to record.
  The host now reads and writes user data on the container's local disk and mirrors changes
  to the volume in the background, keeping media and database I/O off the slow layer while
  `Modal` still persists the data

- `Launcher` &rarr; The `Modal` host could overrun `Modal`'s shutdown grace and be
  force-killed *(logging `Runner has been shutting down for too long`)* when a stop
  or a spot preemption stranded an in-flight volume read on a background thread. A
  watchdog *(a daemon thread started at shutdown that terminates the process if it doesn't
  exit in less than 10 seconds)* now exits the container cleanly within the grace window,
  so a stop or preemption releases promptly

- `Launcher` &rarr; The `Modal` host wrote its request log to the persistent volume
  on every request, growing it unbounded and adding a volume write to the hot
  path. It now logs to standard output, which `Modal` captures, so nothing is
  written to the volume. `Modal` persists logs natively through the `Stopped Apps`
  interface, so writing to a log file would be redundant and decrease performance

- `Frontend` &rarr; The installed `PWA` icon did not render on `iOS` and the app was
  not installable behind the host login. `iOS` fetches the manifest, its icons, and
  the `apple-touch-icon` as install subresources without the login, so behind
  `HTTP Basic Auth` they returned `401`. The host now serves exactly those public
  install files without auth, while the shell, the hashed assets, and the API stay
  gated

- `Frontend` &rarr; An installed `iOS` `PWA` re-prompted for the host password on
  every reopen, since `iOS` drops the `Basic Auth` credential cache when the app is
  suspended. A passed login now sets a persistent, `HttpOnly` cookie that the host
  accepts in place of the credentials, so a reopened app authenticates silently
  *(rotating the password invalidates it)*

- `Frontend` &rarr; Saving a clip on `iOS` could hang on `Recording` from a fresh
  player. The recorder's audio pipeline needs its `AudioContext` resumed inside a
  user gesture, but fetching the word explanation first spent it, leaving the audio
  track dead. The save now resumes the context on the tap, and the recorder can no
  longer hang indefinitely

- `Server` &rarr; `GET /api/jobs` returned `400` for a poll that arrived without an
  `X-Profile-ID` header *(a service-worker replay the app cannot attach the header
  to)*. It now returns an empty list, so the errors stop

## [`3.5.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.5.0) - 2026-07-15

This release makes the launcher run the container images that match the
installed version instead of always pulling `latest`, so an install runs the
images built for it and any published version can be pinned. It also makes the
live demo installable as a PWA, adds an in-app cache reset, and fixes a set of
mobile, caching, and Modal deploy issues. It has no breaking changes

### Added

- `Launcher` &rarr; From this release on, the launcher pulls and composes the
  `<version>`-tagged images matching the installed package rather than `latest`,
  so a `pip install mirumoji==X` (for `X >= 3.5.0`) runs the images built for `X`
  and the launcher never drifts onto an incompatible `latest`. A `MIRUMOJI_VERSION`
  config variable and a `--version` flag on `up` / `pull` / `render` /
  `modal deploy` pin any published version, checked against Docker Hub first so a
  version with no published images fails early with a clear message *(older,
  pre-3.5.0 installs still pull `latest`, since the version-pinning code only
  ships from here on)*

- `Launcher` &rarr; `mirumoji --version` prints the installed version

- `Frontend` &rarr; The live demo is now an installable PWA, so a visitor can add
  it to their home screen and see how the app behaves once installed. The app
  also gained a `Reset App Data` action *(Dashboard &rarr; Advanced)* that
  unregisters the service worker and clears its caches, to recover from a stale
  cached build

### Fixed

- `Launcher` &rarr; `MODAL_FORCE_BUILD` had no effect on `mirumoji modal deploy`.
  The Modal SDK reads it from the local process environment when it builds the
  derived host image, but the deploy exported only the Modal tokens, so setting
  the variable never forced a rebuild and the host stayed on a stale cached image.
  It is now exported for the deploy, so `mirumoji config set MODAL_FORCE_BUILD 1`
  rebuilds the host image

- `Frontend` &rarr; Toasts were rendered under the notch on notched phones. They
  now inset off the safe area and clear it

- `Frontend` &rarr; The player's volume slider did nothing on iOS, where the media
  volume is read-only and owned by the hardware buttons, so it looked broken. It
  is now hidden on iOS, leaving the mute toggle, which still works

- `Frontend` &rarr; The PWA could not be installed behind the Modal host's HTTP
  Basic Auth. The manifest link was fetched without credentials, so it and its
  icons returned 401 and the browser saw no installable manifest, leaving no app
  icon or install prompt. The manifest is now requested with credentials

- `Frontend` &rarr; A new build could be hidden behind a stale cached shell.
  Neither Nginx nor the Modal host set `Cache-Control`, so `index.html`, the
  service worker, and the manifest could be served stale from the HTTP cache,
  pinning old hashed assets. They are now served `no-cache` *(with hashed assets
  marked immutable)*, so a new version is picked up on the next load

## [`3.4.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.4.0) - 2026-07-14

This release adds a one-command private full-host deploy to `Modal`, reworks the Modal GPU offload
into a warm, reusable worker that skips the per-job cold start, warms the tokenizer and dictionary at
startup, and takes the frontend edge-to-edge on notched phones. As a `v3.x` release *(see the
`v0.1.0` note above)* it includes two breaking changes, listed first

### Breaking Changes

- `REST API` &rarr; The Kanji dictionary endpoints now carry the Kanji as a query parameter instead
  of a path segment *(`/dict/kanji/{literal}` &rarr; `/dict/kanji?literal=...`, and likewise for
  `/strokes`, `/audio`, and `/audio/clip`)*. A Kanji literal is always non-ASCII, and a Modal-hosted
  deploy rejects any request whose URL path holds non-ASCII bytes, so the glyph is kept out of the
  path. Clients of these endpoints need to adopt the query-parameter form

- `Launcher` &rarr; The local data folder *(managed config, logs, cached builds, and any non-Docker
  data)* is no longer keyed by the app version. Earlier versions stored it under a per-version
  subfolder, so every upgrade silently started from an empty folder and orphaned the previous
  install's data, despite the compose comment promising data survived version bumps. From `3.4.0` the
  folder is unversioned, so future upgrades keep your data, but the one-time move to `3.4.0` does not
  read a pre-`3.4.0` versioned folder. Re-enter your keys, or import the old file with
  `mirumoji config import <path>`. The old data is left in place, not deleted, and Docker data volumes
  are unaffected

### Added

- `Launcher` &rarr; `mirumoji modal deploy` hosts the `entire` app *(the FastAPI server and the built
  React frontend)* privately on your own [`Modal`](https://modal.com) account, with no local Docker.
  It runs as a single always-warm CPU container gated by a browser login *(`HTTP Basic Auth`)*, keeps
  its database and media in a persistent Modal volume, and offloads GPU transcription to the same
  worker the local `modal` backend uses. `modal status`, `modal down`, and `modal download-data`
  inspect, tear down, and back it up. The deploy image is composed from the published backend and
  frontend images, so no new artifact ships. See the new [`Modal Host Setup`](../setup/modal-host.md)
  guide

- `Launcher` &rarr; `mirumoji config show` gained `--raw` *(reveal masked secret values, for reading a
  generated web password)* and `--json` *(export the config)*

- `Frontend` &rarr; A backend-free `live demo` now runs at the docs site root. A build-time
  `--mode demo` swaps the network layer for committed fixtures captured from a real session, so a
  pre-loaded sample episode *(the player, tokenized subtitles, and word breakdowns)* and a curated
  dictionary slice work with no server. Off-rails input *(upload, free search, profile switch)* is
  gated, and dictionary links outside the captured set are disabled

### Changed

- `Server` &rarr; The Modal GPU offload now runs a single deployed, warm worker that loads the
  multi-GB Whisper model once per container and stays warm for the scaledown window, instead of
  spinning up an ephemeral app per job that reloaded the model every time. Back-to-back jobs skip the
  cold start, while the worker still scales to zero when idle, so an idle GPU never costs you. The
  server auto-deploys it on first use *(tracked by ownership tags so it is never duplicated and rolls
  forward on upgrade)* and stops it on shutdown

- `Server` &rarr; The Japanese tokenizer *(`fugashi` / `UniDic`)* and the dictionary *(`kotobase`)*
  are warmed during startup, so the first tokenization and lookup are fast instead of paying a
  one-time cold load. Each warm-up runs in a thread and only warns on failure, so a broken language
  dependency degrades only its own endpoints while transcription and file management keep working

- `Frontend` &rarr; The app goes edge-to-edge on notched phones *(filling the letterbox bars via
  `viewport-fit=cover`)* while respecting safe-area insets across both headers, the drawer, the hover
  rail, the floating button, the player toolbar, and the task tray. Every inset resolves to zero on a
  non-notched display, so desktop and portrait layouts are unchanged

### Fixed

- `Server` &rarr; The `/health/system` probe runs off the event loop. It shells out to `nvidia-smi`
  *(up to a 5s timeout)*, which previously blocked every other request while it waited

- `Frontend` &rarr; The player adapts to a phone held in landscape, reusing the desktop side-by-side
  subtitle rail instead of stacking the panel below the video and splitting the short height in half.
  The subtitle-style popover is also bounded to the viewport with an internal scroll so it no longer
  runs off a short landscape screen

- `Server` + `Frontend` &rarr; Non-ASCII characters are kept out of URL paths and profile ids. The
  frontend gates profile names to ASCII and the server rejects a non-ASCII `X-Profile-ID` header with
  a `400`, so a profile named with Japanese or other Unicode text no longer produces invalid URLs or
  ids *(which also lets the whole app run on a Modal-hosted deploy)*

- `Launcher` &rarr; `mirumoji reset` prunes the `mirumoji` folder in every `platformdirs` root *(the
  cache, config, state, and log locations)*, so a reset cleans up uniformly on Linux, macOS, and
  Windows and leaves nothing orphaned

---

## [`3.3.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.3.0) - 2026-07-08

This release organizes profile files, lets a word breakdown pull in the surrounding subtitle
lines, adds a one-command local-data reset, and hardens the server's logging and shutdown.
As a `v3.x` release *(see the `v0.1.0` note above)* it includes a breaking database change

### Breaking Changes

- `Database` &rarr; Profile files now record their lineage *(the source video from which
  a generated subtitle or converted MP4 came)* through two new columns, added
  without a migration. An existing install must start from a fresh database *(run
  `mirumoji reset` first, or `mirumoji down -v` for a Docker deployment, before
  updating)*

### Added

- `Frontend` &rarr; Profile files are organized by video lineage. Each source video
  nests its derived files *(generated / fixed subtitles, a converted MP4)* beneath it
  with readable names instead of opaque ids, grouped by folder. The player's
  `Load Media` list is also updated to group related files

- `Server` + `Frontend` &rarr; A word breakdown can include the surrounding subtitle
  lines. A prompt template opts in with a `{context}` placeholder and
  `{#context}…{/context}` conditional blocks. The LLM template editor shows a live
  preview of the assembled prompt, and a control in the player toolbar sets how many
  lines on each side *(N lines before the current sentence + N lines after it)* are sent

- `Launcher` &rarr; A `mirumoji reset` command *(and a `Delete Data` button in the GUI
  Settings)* deletes Mirumoji's local data folder, which is otherwise tucked away in a
  hidden system directory. `--keep-config` and `--keep-logs` preserve those. Docker
  data volumes are left to `down --volumes`

- `Launcher` &rarr; The LLM batch concurrency and a Modal container keep-warm window
  are configurable through new environment variables and Settings fields

### Changed

- `Server` &rarr; Logging was reworked so the server console stays clean, every log
  line carries a per-request id, and upload progress shows a themed bar

- `Server` &rarr; The previously untyped JSON endpoints *(the profile deletes and the
  provider / model / health routes)* now return typed models, so they are documented
  in the API schema

- `Frontend` &rarr; Info tooltips are a single shared component that stays on-screen on
  mobile and can hold richer content

### Fixed

- `Frontend` &rarr; Deleting a file that is open in the player now clears it, so a
  deleted video no longer looks like an unplayable format and a deleted subtitle no
  longer lingers

- `Server + Frontend` &rarr; Deleting several files at once is safe *(previously, the database ran into a race-condition where deleting multiple files at once would try to wipe already-deleted jobs shared by them, stopping the deletion)*. The frontend now clears completed jobs related to already-deleted files from the task tray

- `Server` &rarr; On shutdown, the server releases its log file and stops any running
  `FFMPEG` process, so nothing is left holding a file open and the local data folder
  can be removed *(notably on Windows)*

- `Frontend` &rarr; The local CA can be downloaded over `HTTPS`. The service worker was
  catching the request and serving the app *(which rendered its 404 page)*, so the
  certificate could previously only be fetched over `HTTP`

## [`3.2.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.2.0) - 2026-07-04

This release turns the dictionary into a full study hub *(kanji stroke-order animations,
radical search, English lookup, pronunciation audio)* and makes `Mirumoji` installable as
an app on every device via a one-time certificate install. As a `v3.x` release (see the
`v0.1.0` note above) it includes a breaking change

### Breaking Changes

- `REST API` &rarr; The dictionary lookup response was restructured to carry the richer
  data below *(senses with multiple glosses and readable tags, examples with translations,
  furigana, fuller kanji profiles)*. Clients of `/dict/query` and `/dict/analyze` need to
  adopt the new shape

### Added

- `Frontend` &rarr; The `Dictionary` page is now a study hub. One search bar covers
  Japanese words, wildcard patterns, English meanings, and finding kanji by their
  radicals *(matching all or any of them)*, a breadcrumb trail connects every view, and
  the landing page offers your recent lookups plus kanji and words to explore

- `Frontend` &rarr; Kanji show animated stroke-order diagrams that draw themselves
  *(with replay, step, and speed controls on the kanji page)*, their radical components,
  pronunciation clips, words that use the kanji, and example sentences

- `Frontend` &rarr; Word entries show accurate furigana above the headword, senses with
  plain-language grammar tags instead of dictionary codes, common-word and JLPT badges,
  antonym and see-also links, and example sentences with English translations

- `Frontend` &rarr; The word pop-up in the player was reorganized into collapsible
  sections *(Entry, Names, Kanji, Examples, Grammar)* with playable stroke animations,
  grammar terms that explain themselves on hover, and a link into the Dictionary

### Changed

- `Server` &rarr; Dictionary lookups run on `kotobase 0.4.1` and use the sentence context
  of a clicked word *(its reading and part of speech)* to rank the right entry first, so
  words that share a written form resolve to the reading you actually clicked

- `Docker Images` &rarr; The server images now bake the pronunciation audio pack
  alongside the dictionary database

### Fixed

- `PWA` &rarr; Mirumoji can be installed as an app (with offline interface caching) on
  phones and other devices. The server now runs a persistent local certificate
  authority, and installing its certificate once per device *(downloadable from the
  running app, see the new docs guide)* makes the connection fully trusted. The app couldn't
  be installed before because browsers require a fully trusted certificate for service
  worker registration
---

## [`3.1.1`](https://github.com/svdC1/mirumoji/releases/tag/v3.1.1) - 2026-06-22

A patch release with two fixes

### Fixed

- `Server` &rarr; GPU video conversion now correctly detects `NVENC`. The capability
  check encoded a probe frame smaller than `NVENC`'s minimum supported size, so it always
  failed and every conversion fell back to CPU, even on a GPU whose encoder works

- `Package` &rarr; the package reports its real version again. `__version__` was not
  updated for the `3.1.0` release, so the version shown in the desktop launcher (and used
  to name the local data directory) was stale

---

## [`3.1.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.1.0) - 2026-06-21

This release moves every long-running media operation into a background job system,
adds batch processing so one operation can run over many files at once, and makes the
GPU Docker images much smaller. As a `v3.x` release (see the `v0.1.0` note above) it
includes a few breaking changes, listed first

### Breaking Changes

- `REST API` &rarr; the old one-shot endpoints for transcription, subtitle
  generation, conversion, and subtitle cleanup were removed. These operations now run
  through the background job system instead

- `REST API` &rarr; word breakdowns and sentence explanations are now sent as a live
  stream while they are generated, rather than as a single response at the end

- `CLI` &rarr; the `mirumoji server` command moved into a new development-only group
  and is now `mirumoji dev server`

- `Database` &rarr; the database format changed and is not upgraded automatically
  from `3.0.0`. Reset it when upgrading by running `mirumoji down -v` (this clears
  local data, in keeping with the pre-1.0 note above)

### Added

- `Server` &rarr; long operations (transcription, subtitle generation, conversion,
  and LLM subtitle cleanup) now run in the background. A file is uploaded once, and
  any number of operations can then run on it without uploading it again

- `Server` &rarr; batch processing runs one operation across many files at once and
  tracks each file on its own. On the Modal backend the files are processed in
  parallel

- `Frontend` &rarr; a task tray keeps your running and finished jobs visible as you
  move around the app, and loads each result back in when it is done

- `Frontend` &rarr; new `Files` and `Tasks` sections on the dashboard let you upload
  files or a whole folder, select several and run them as a batch, browse the full
  job history, and open each result

- `Frontend` &rarr; when setting up an LLM, you can now pick the model from a
  searchable list of your provider's models instead of typing its exact name

- `Frontend` &rarr; video conversion now has a quality preset (`Performance`,
  `Balanced`, or `Quality`) alongside the resolution and bitrate options, so you can
  trade encode speed for output quality

- `CLI` &rarr; `mirumoji dev up` builds and runs the app from a local source
  checkout, for testing the Docker setup during development

### Changed

- `Frontend` &rarr; running an operation in the player no longer freezes the toolbar.
  It is handed to the task tray, which loads the result back in when it finishes. The
  video player was also reworked into a shared component that clip previews reuse

- `Frontend` &rarr; a phone held sideways now uses the mobile layout, since the
  desktop layout only starts at tablet width

- `Launcher` &rarr; the launcher's logs and the Docker download progress are tidier
  and easier to follow, in both the CLI and the desktop app

- `Docker Images` &rarr; the GPU images are smaller. PyTorch was removed because
  transcription does not need it, and the speech model now downloads on first use into a
  persistent cache instead of being baked into the local GPU images

- `Server` &rarr; video conversion is faster and leaner. On the GPU the whole decode,
  scale, and encode pipeline now stays on the GPU instead of copying frames back and
  forth, and the GPU and Modal images ship a newer FFmpeg build to support it.
  Conversion also picks the encoder from what the GPU can actually do, so machines whose
  GPU cannot encode (and CPU-only setups) go straight to a fast CPU encode. Converted
  videos keep their original aspect ratio now rather than being padded with black bars

### Fixed

- `Frontend` &rarr; the player now handles video formats your browser cannot play
  (such as `.mkv` on iOS) by offering to convert them to MP4 instead of showing a
  broken player. Loading a different video also resets the saved position so it never
  starts past the end of a shorter one

- `Frontend` &rarr; the navigation menu scrolls on short screens (such as a phone
  held sideways) so every item stays reachable, and long entries on the `Home` page
  no longer stretch the layout out of shape

- `Server` &rarr; saving a clip no longer fails for clips with long Japanese text,
  and saved clips now use a server-generated filename that closes a security issue
  where a crafted upload name could write outside its folder

- `Server` &rarr; deleting a file also removes the jobs that used it (and is blocked
  while one of those jobs is still running), cancelling or deleting a running job no
  longer leaves the job list in a broken state, and a failed job now shows a clear
  reason

- `Server` &rarr; converting a video on a cloud GPU that has no video encoder (such as
  an `A100`, `H100`, or `B200`) no longer wastes time on a failed hardware-encode
  attempt before falling back, which had made GPU conversion slower than plain CPU

- `CLI` &rarr; `mirumoji logs -f` no longer crashes when you press Ctrl+C, and
  re-running `mirumoji up` no longer contacts Docker Hub when the images are already
  downloaded

---

## [`3.0.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.0.0) - 2026-06-15

A structural and packaging rewrite of `Mirumoji`

- The backend + CLI are merged into a single, pip-installable `mirumoji` package, and the release, docs, and  dev-container tooling are rebuilt around it

- The core immersion workflow is unchanged from `2.6.0`, the `Launcher` (CLI + Desktop GUI) is substantially expanded, and LLM support is no longer limited to `OpenAI`

- There is intentionally no `2.6.0` &rarr; `3.0.0` diff, since nearly everything moved internally, so this entry   answers `What Carried Over?` + `What's New?` + `How To Run It` instead

### What Carried Over From `2.6.0`

The immersion workflow is `Unchanged`

- Upload local videos, anime episodes, or audio for clickable `tokenized Japanese subtitles` with dictionary lookups

- Transcribe audio / generate subtitles with `Whisper`

- Get word / sentence breakdowns from LLMs, or prompt the LLM to refine the
  Whisper-generated subtitles

- Save `clips` and export them to an `Anki` deck

- Organize your data (clips, LLM templates, files, transcriptions, ...) on the
  server by profile

- Self-host the `Docker Compose Application` with `Local-NVIDIA-GPU` /
  `Modal Cloud-GPU Offload` backend options

- Access the application via HTTPS from any device on your local network using
  the automatically generated self-signed certificate

### What's New / Expanded

#### Multiple LLM Providers *(New)*

`2.6.0` required an `OpenAI` API key

`3.0.0` makes LLM features `completely optional` and adds `Anthropic (Claude)` + `Google (Gemini)` + `Any Custom OpenAI-Compatible Endpoint` support via a provider / model picker

#### CLI Launcher *(Expanded)*

The `2.6.0` CLI had 5 commands (`launch` / `shutdown` / `launch_local` /
`build` / `gui`) driven by interactive prompts and a hand-managed `.env`

`3.0.0` rebuilds it on `Typer` / `Rich`, adds the `status` / `logs` / `doctor`
/ `server` / `render` commands + a managed-config surface (`config set/delete/import/show/path/clear`)

#### Desktop Launcher *(Expanded)*

The `2.6.0` `flaskwebgui` / `PyInstaller` window is rebuilt on `Flet` and gains
a `Settings` panel where you can configure the transcription backend, image
source, and LLM / Modal keys. It also has full environment checks, live status
display, and Docker Compose log filtering

#### Modal Offload *(Hardened)*

`Modal` GPU jobs stream their media through a per-job ephemeral `Modal Volume`
instead of a baked image mount, so long media (multi-hour, multi-GB) transcodes
and transcribes reliably. Large uploads also stream at full speed rather than
being throttled at the reverse proxy

### How To Run It

The [`Setup Section`](../setup/index.md) contains detailed information on all of
the ways that you can get `Mirumoji` running

### Upgrading From `2.6.0`

???+ warning "Your Data Does Not Carry Over"
    The database schema changed in `3.0.0`, so existing `2.6.0` profiles,
    clips, transcripts, and templates are `NOT` migrated

    Treat `3.0.0` as a fresh install.

??? info "Additional Details &rarr; Changed Surfaces"
    - `Package` &rarr; `apps/backend` + `apps/cli` merged into one
      `apps/mirumoji/` package published to PyPI as `mirumoji`

    - `CI / CD` &rarr; 12 workflows redesigned as an orchestrated `release.yaml`
      calling reusable `_version` / `_images` / `_pypi` / `_pages` / `_desktop`
      workflows. Images are published to `Docker Hub` only (GHCR dropped)

    - `Docs` &rarr; MkDocs Material custom CSS theme, `mkdocstrings-python` (API) + `TypeDoc` (frontend API),   `awesome-nav` structure

    - `Dev Containers` &rarr; fixed builds + `postCreateCommand` bootstrap, and
      `flake8` changed to `ruff`

    `Community` &rarr; community files moved to `.github/`, `YAML` issue forms, quality-gate PR template
---
