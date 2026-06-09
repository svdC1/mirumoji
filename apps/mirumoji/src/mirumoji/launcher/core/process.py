"""
Defines subprocess execution helpers for the launcher core

info: Overview
    - `run` &rarr; Executes an external command to completion

    - `stream` &rarr;  Yields the combined stdout/stderr of an external
      command's execution line by line so a front-end can render live output

    - Neither prints anything, presentation is the caller's job
"""

import logging
import os
import subprocess
from collections.abc import Generator
from pathlib import Path

LOGGER = logging.getLogger(__name__)

# On Windows, a GUI app spawning a console program pops up a transient `cmd`
# window for each call. `CREATE_NO_WINDOW` suppresses it. The flag is
# Windows-only, so it resolves to `0` on other platforms
_NO_WINDOW: int = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _popen(cmd: list[str], cwd: Path | None) -> subprocess.Popen[str]:
    """
    Starts a subprocess with merged stdout/stderr as decoded text

    Args:
        cmd (list[str]): The external command to run and its arguments
        cwd (Path | None): The directory from which to run the command.
            When set to `None`, defaults to the directory from which the
            current python proccess was started from.

    Returns:
        The started process
    """
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
        env=env,
        creationflags=_NO_WINDOW,
    )


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    Runs an external command in a subprocess to completion and captures its
    output

    Args:
        cmd (list[str]): The external command to run and its arguments
        cwd (Path | None): The directory from which to run the command.
            When set to `None`, defaults to the directory from which the
            current python proccess was started from.
        check (bool): Raises an exception on a non-zero exit status when
            `True`

    Returns:
        The completed process with the captured `stdout`

    Raises:
        subprocess.CalledProcessError: If the command fails and `check=True`
        FileNotFoundError: If the executable is not found
    """
    cmd_str = " ".join(cmd)
    LOGGER.debug(f"Running Command : {cmd_str} (cwd={cwd or Path.cwd()})")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_NO_WINDOW,
    )
    if check and result.returncode != 0:
        LOGGER.error(
            f"Command Failed ({result.returncode}) : {cmd_str}\n"
            f"{result.stdout}",
        )
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd_str,
            result.stdout,
            result.stderr,
        )
    return result


def stream(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> Generator[str, None, int]:
    """
    Runs an external command in a subprocess and yields its combined output
    (stdout + stderr) line by line

    Args:
        cmd (list[str]): The external command to run and its arguments
        cwd (Path | None): The directory from which to run the command.
            When set to `None`, defaults to the directory from which the
            current python proccess was started from.
        check (bool): Raises an exception on a non-zero exit status when
            `True`

    Yields:
        Each stripped output line as it is produced

    Returns:
        The command's exit code

    Raises:
        subprocess.CalledProcessError: If the command fails and `check=True`
        FileNotFoundError: If the executable is not found
    """
    cmd_str = " ".join(cmd)
    LOGGER.debug(f"Streaming Command : {cmd_str} (cwd={cwd or Path.cwd()})")
    process = _popen(cmd, cwd)
    if process.stdout is not None:
        for line in iter(process.stdout.readline, ""):
            yield line.rstrip("\r\n")
        process.stdout.close()
    return_code = process.wait()
    if check and return_code != 0:
        LOGGER.error(f"Command Failed ({return_code}) : {cmd_str}")
        raise subprocess.CalledProcessError(return_code, cmd_str)
    return return_code
