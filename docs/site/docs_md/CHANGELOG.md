# Changelog

All notable changes to this project will be documented in this file.

The format is based on [`Keep a Changelog`](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [`Semantic Versioning`](https://semver.org/spec/v2.0.0.html)
starting from **`v3.0.0`**.

???+ warning "Pre-`v3.0.0`"
    - `v1.0.0` – `v2.6.0` used semver-like tags but without a formal policy or changelog
    - Their history is preserved in [`GitHub Releases`](https://github.com/svdC1/mirumoji/releases)

---

## [Unreleased]

### Added

- **Versioning Policy** &rarr; `CHANGELOG.md` (this file) and `versioning.md` establish the
  Keep-a-Changelog format and strict semver contract from v3.0.0 onward

- **Unified Python Package** &rarr; `apps/mirumoji/` merges `apps/backend/` and `apps/cli/`
  into a single `src`-layout package (`mirumoji.server`, `mirumoji.cli`) with optional
  dep extras &rarr; `server` (FastAPI + Heavy ML Deps For Docker), `gui` (flaskwebgui),
  `dev` (ruff, mypy, pytest, pip-tools).

- **`pyproject.toml`** &rarr; Single Python package declaration replacing
  `apps/backend/requirements.txt` and `apps/cli/mirumoji/pyproject.toml`.

- **Ruff + Mypy** &rarr; lint, format, and type-check configs for the Python package
  (warn-only baseline. Will be tightened incrementally in 3.x).

- **ESLint 9 + Prettier** &rarr; Flat config (`eslint.config.js`) and `.prettierrc` for the
  frontend. `npm run lint`, `npm run lint:fix`, `npm run format` scripts

- **Test Scaffolding** &rarr; `apps/mirumoji/tests/{server,cli}/` (pytest + httpx) and
  `apps/frontend/src/__tests__/` (Vitest + jsdom) with smoke tests to start

- **CI Quality Gate** &rarr; `.github/workflows/quality.yaml` runs ruff, mypy, pytest,
  ESLint, Prettier, and Vitest on every PR and push to `main` / `v3-refactor`.

- **Pre-Commit Hooks** — `.pre-commit-config.yaml` with ruff, end-of-file-fixer,
  trailing-whitespace, check-merge-conflict, and a frontend lint hook.

### Changed

- All Docker build contexts updated from `apps/backend/` &rarr; `apps/mirumoji/`.

- All GitHub Actions path triggers updated to match new `apps/mirumoji/` layout

- Backend Python imports rewritten from implicit top-level
  to package-qualified

### Removed

- `apps/backend/` directory &rarr; source moved to `apps/mirumoji/src/mirumoji/server/`

- `apps/cli/` directory &rarr; source moved to `apps/mirumoji/src/mirumoji/cli/`

---

[Unreleased]: https://github.com/svdC1/mirumoji/compare/v2.6.0...HEAD
