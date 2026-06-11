# Versioning Policy

From `v3.0.0` Mirumoji strictly follows [`Semantic Versioning`](https://semver.org/spec/v2.0.0.html)
and all notable changes are documented in the project
[`CHANGELOG`](https://github.com/svdC1/mirumoji/blob/main/CHANGELOG.md) using the
[`Keep a Changelog`](https://keepachangelog.com/en/1.1.0/) format. A single version string is shared across the python package and the frontend bundle.

???+ warning "Pre-`v3.0.0`"
    - `v1.0.0` - `v2.6.0` used semver-like tags but without a formal policy
      or changelog
   
    - Their history is preserved in [`GitHub Releases`](https://github.com/svdC1/mirumoji/releases)

---

## Semantic Versionsing Summary

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

Mirumoji exposes three versioned surfaces. A breaking change to **any one** of them
increments the `MAJOR` version for the whole project.

### REST API (Server)

???+ abstract "Breaking Changes"
    - Removing an endpoint
    - Renaming an endpoint path or HTTP method
    - Removing or renaming a required request field
    - Removing or renaming a response field that clients rely on
    - Narrowing an accepted type (e.g. `string | null` → `string`)
    - Adding a new **required** request field without a default

### CLI (`mirumoji` commands)

???+ abstract "Breaking Changes"
    - Removing a command or sub-command
    - Removing or renaming a flag/option that was documented
    - Changing the exit-code contract for a command

### Frontend

The frontend does not expose a versioned public API. It is versioned alongside the
server and CLI but does not independently trigger a `MAJOR` bump

---
