"""
Builds the Mirumoji Desktop GUI bundle with `flet build`

Writes a throwaway entry point and copies app assets to `mirumoji/`,
appends the GUI bundle's extra dependencies to `pyproject.toml`, runs
`flet build` from the `flet_cli` package in-process, and reverts all
changes afterwards

Usage:
    python scripts/build_gui.py <macos|linux|windows|web|apk|aab|ipa>
"""

import os
import re
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.theme import Theme

# `flet build` prints Unicode status glyphs such as ● (U+25CF)
#
# On Windows the std streams default to cp1252, which can't encode
# them and crashes the build with a UnicodeEncodeError
#
# Force UTF-8 on the streams before any output is written.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8", errors="replace")

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


# --- Build Constants ---

# root > scripts > __file__
REPO_ROOT = Path(__file__).parent.parent
APP_DIR = REPO_ROOT / "apps" / "mirumoji"
PYPROJECT = APP_DIR / "pyproject.toml"
MAIN_FILE = APP_DIR / "main.py"
ENTRY_POINT_CODE = """import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from mirumoji.launcher.gui.app import main

if __name__ == "__main__":
    main()
"""

GUI_ASSETS = APP_DIR / "src" / "mirumoji" / "launcher" / "gui" / "assets"
BUILD_ASSETS = APP_DIR / "assets"

# `flet build` resolves the bundle from `[project.dependencies]` +
# `[tool.flet.<platform>].dependencies`, so these are
# appended to `pyproject.toml` only for the duration of the build
BUNDLE_DEPS = ["flet==0.85.2", "certifi"]


# --- Staging Helpers ---


def stage_assets() -> None:
    """
    Copies the whole GUI assets folder into the build assets dir

    flet reads both the runtime assets and the app icons from
    `<app>/assets`, so the entire `gui/assets` tree is copied
    """
    shutil.copytree(GUI_ASSETS, BUILD_ASSETS, dirs_exist_ok=True)
    console.print(f"Copied GUI Assets To {BUILD_ASSETS}", style="info")


def bundle_deps_block(platform: str) -> str:
    """
    Renders the `[tool.flet.<platform>]` dependency table appended at build
    time

    Args:
        platform (str): Which platform to target

    Returns:
        The TOML snippet to append to `pyproject.toml`
    """
    deps = ", ".join(f'"{dep}"' for dep in BUNDLE_DEPS)
    return (
        f"\n# Appended by scripts/build_gui.py — reverted after the build\n"
        f"[tool.flet.{platform}]\n"
        f"dependencies = [{deps}]\n"
    )


# --- In-Process Flet Build ---


def build_version() -> str:
    """
    Returns the package version reduced to its `X.Y.Z` core

    `flet build` maps `[project].version` to `--build-version`, which must be a
    plain `x.y.z` string. A PEP 440 pre-release suffix (e.g. `3.0.0rc1`) leaves
    the Windows executable's VERSIONINFO resource blank or invalid, a common
    heuristic AV / SmartScreen flag for unsigned binaries, so it is trimmed and
    passed explicitly

    Returns:
        The `X.Y.Z` core of `[project].version`, or `0.0.0` if unreadable
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', text)
    version = match.group(1) if match else "0.0.0"
    core = re.match(r"\d+\.\d+\.\d+", version)
    return core.group(0) if core else version


def run_flet_build(platform: str) -> None:
    """
    Runs `flet build` in-process from the app directory

    Drives `flet_cli` directly (no subprocess) so its output renders straight
    to the terminal, keeping the Flutter progress animation intact

    Args:
        platform (str): Which platform to target

    Raises:
        SystemExit: Re-raised with flet's exit code when the build fails
    """
    from flet_cli.cli import main as flet_main  # type: ignore[import-untyped]

    # An explicit `x.y.z` build version keeps the VERSIONINFO resource valid;
    # the rest of the metadata (product / company / copyright / description) is
    # already resolved from pyproject.toml
    argv, cwd = sys.argv, os.getcwd()
    sys.argv = [
        "flet",
        "build",
        platform,
        "--yes",
        "--build-version",
        build_version(),
    ]
    os.chdir(APP_DIR)
    try:
        flet_main()
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise
    finally:
        sys.argv = argv
        os.chdir(cwd)


def main(platform: str) -> None:
    """
    Writes the entry point + assets + bundle deps, builds, and restores
    everything

    Args:
        platform (str): Which platform to target (e.g `windows`)
    """
    original_pyproject = PYPROJECT.read_text(encoding="utf-8")
    try:
        MAIN_FILE.write_text(ENTRY_POINT_CODE, encoding="utf-8")
        console.print(
            f"Wrote Temporary GUI Entry To {MAIN_FILE}",
            style="info",
        )

        stage_assets()

        PYPROJECT.write_text(
            original_pyproject + bundle_deps_block(platform), encoding="utf-8"
        )
        console.print(f"Added Bundle Dependencies {BUNDLE_DEPS}", style="info")

        console.print(f"Running Flet Build For {platform}...", style="accent")
        run_flet_build(platform)
        console.print("Build Complete", style="success")
    finally:
        # Restore pyproject.toml + remove the entry point and staged assets
        PYPROJECT.write_text(original_pyproject, encoding="utf-8")
        MAIN_FILE.unlink(missing_ok=True)
        shutil.rmtree(BUILD_ASSETS, ignore_errors=True)
        console.print("Cleaned Up Temporary Files", style="muted")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print(
            "Usage: python scripts/build_gui.py "
            "<macos|linux|windows|web|apk|aab|ipa|ios-simulator>",
            style="danger",
        )
        sys.exit(1)
    main(sys.argv[1])
