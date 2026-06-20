# Versioning Policy

From `v3.0.0` Mirumoji follows [`Semantic Versioning`](https://semver.org/spec/v2.0.0.html)
and all notable changes are documented in the project
[`CHANGELOG`](changelog.md) using the
[`Keep a Changelog`](https://keepachangelog.com/en/1.1.0/) format. A single version string is shared across the python package and the frontend bundle.

???+ warning "Pre-`v3.0.0`"
    - `v1.0.0` - `v2.6.0` used semver-like tags but without a formal policy
      or changelog

    - Their history is preserved in [`GitHub Releases`](https://github.com/svdC1/mirumoji/releases)

???+ danger "`v3.0.0` Is `v0.1.0`"
    - Since `Mirumoji` underwent a complete refactoring / rewrite, and has only started following `Semantic Versioning` in `v3.0.0`, it should be treated as an initial release

    - This means that the following `v3.x` versions **MIGHT STILL CONTAIN BREAKING CHANGES**

    - These changes will be clearly documented in this changelog

---

## Semantic Versioning Summary

???+ abstract "Version Increments"
    ```
    MAJOR.MINOR.PATCH
    ```

    | Segment | Incremented When |
    |---------|-------------------|
    | `MAJOR` | A breaking change is introduced |
    | `MINOR` | A new backward-compatible functionality is added |
    | `PATCH` | A backward-compatible bug fix is implemented |

---

## Breaking Changes

Mirumoji exposes a single, unified, versioned public API across 3 surfaces

### REST API (Server)

This is the `FastAPI` application defined under the [`server`](../python_api/server/index.md) sub-package of
the `mirumoji` Python Package. Following the release of `v4.0.0`, any of the following `Breaking Changes` triggers a `MAJOR` bump to the unified versioned public API

???+ abstract "Breaking Changes"
    - Removing an endpoint
    - Renaming an endpoint path or HTTP method
    - Removing or renaming a required request field
    - Removing or renaming a response field that clients rely on
    - Narrowing an accepted type (e.g. `string | null` &rarr; `string`)
    - Adding a new **required** request field without a default

### CLI (`mirumoji` commands)

This is the `Typer` + `Rich` CLI application defined in the [`launcher/cli`](../python_api/launcher/cli/main.md) sub-package of the `mirumoji` Python Package. Following the release of `v4.0.0`, any of the following `Breaking Changes` triggers a `MAJOR` bump to the unified versioned public API

???+ abstract "Breaking Changes"
    - Removing a command or sub-command
    - Removing or renaming a flag/option that was documented
    - Changing the exit-code contract for a command

### Frontend

This is the [`React / Vite / Typescript Application`](../frontend_api/README.md) which provides the UI for interacting with the `REST API`. It is versioned alongside the `REST API` and the `CLI`, but **DOES NOT** independently trigger a `MAJOR` bump to the unified versioned public API

This is because it is built around the `REST API` and has no useful functionality as a standalone `npm` module, which is why it's marked as `private` in `package.json`

---
