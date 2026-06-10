"""
Keeps the community-health files in `.github/` in sync with the
per-app copies that need to live beside the code they ship with

Rather than hand-maintain three READMEs, edit `.github/README.md` and let this
script propagate it

Usage:
    python scripts/sync_meta.py            # write the copies
    python scripts/sync_meta.py --check    # exit 1 if any copy is out of date
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB = REPO_ROOT / ".github"

# (Source, Destination) pairs, relative to the repo root
SYNC_MAP: list[tuple[Path, Path]] = [
    (GITHUB / "README.md", REPO_ROOT / "apps" / "mirumoji" / "README.md"),
    (GITHUB / "README.md", REPO_ROOT / "apps" / "frontend" / "README.md"),
    (GITHUB / "LICENSE", REPO_ROOT / "apps" / "mirumoji" / "LICENSE"),
]


def _rel(path: Path) -> str:
    """
    Returns a path relative to the repo root for tidy log output

    Args:
        path (Path): The path to render

    Returns:
        The POSIX-style path relative to the repo root
    """
    return path.relative_to(REPO_ROOT).as_posix()


def sync(check: bool) -> int:
    """
    Copies each `.github/` file onto its destinations, or verifies they match

    Args:
        check (bool): When True, report drift without writing and return 1 if
            any destination differs from its source

    Returns:
        A process exit code (0 when in sync, 1 when drift was found in check
        mode)
    """
    drifted: list[str] = []
    for source, dest in SYNC_MAP:
        if not source.exists():
            print(f"Missing Source: {_rel(source)}", file=sys.stderr)
            return 1
        source_text = source.read_text(encoding="utf-8")
        current = dest.read_text(encoding="utf-8") if dest.exists() else None
        if current == source_text:
            continue
        drifted.append(_rel(dest))
        if not check:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)

    if check and drifted:
        print("Out Of Sync With .github/ (run scripts/sync_meta.py):")
        for path in drifted:
            print(f"  - {path}")
        return 1
    if drifted and not check:
        for path in drifted:
            print(f"Synced {path}")
    return 0


def main() -> None:
    """
    Parses arguments and runs the sync
    """
    parser = argparse.ArgumentParser(description="Sync .github/ meta files")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the copies are up to date without writing",
    )
    args = parser.parse_args()
    sys.exit(sync(check=args.check))


if __name__ == "__main__":
    main()
