"""
Defines subprocess execution helpers for the launcher core

info: Overview
    - `run` &rarr; Executes an external command to completion

    - `stream` &rarr;  Yields the combined stdout/stderr of an external
      command's execution line by line so a front-end can render live output

    - `StreamHandle` &rarr; An optional cancellation token a caller passes to
      `stream` to stop a long-running command (e.g. `docker compose logs -f`)
      on demand from another thread

    - Neither prints anything, presentation is the caller's job
"""

import contextlib
import logging
import os
import signal
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

LOGGER = logging.getLogger(__name__)

# On Windows, a GUI app spawning a console program pops up a transient `cmd`
# window for each call. `CREATE_NO_WINDOW` suppresses it. The flag is
# Windows-only, so it resolves to `0` on other platforms
_NO_WINDOW: int = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _kill_process_tree(process: subprocess.Popen[str]) -> None:
    """
    Forcefully stops a process together with any children it spawned

    info: Why The Whole Tree
        - `stream` reads the command's output through a pipe, and that read
          only reports "end of input" once every process able to write into
          the pipe has exited

        - A CLI like `docker compose` does its work in a child process (the
          compose plugin) that shares the same output pipe, so killing only
          the parent leaves that child running and still able to write. The
          read then waits forever for output that never comes

        - Killing the whole tree makes every writer exit, so the read reaches
          the end and `readline` returns

    info: Per-Platform Mechanism
        - Windows &rarr; `taskkill /T` walks and kills the child tree by PID

        - POSIX &rarr; the process is spawned as its own session/group leader
          (see `_popen`), so a single group signal reaches every child

    Args:
        process (subprocess.Popen[str]): The streamed process to stop. A no-op
            when it has already exited
    """
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_NO_WINDOW,
        )
    else:
        # The process can exit between the poll above and the signal
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)


class StreamHandle:
    """
    Cancellation token that stops a running `stream` from another thread

    info: The Problem It Solves
        - `stream` follows a command's output by blocking on `readline` until
          the next line arrives

        - For a tailing command like `docker compose logs -f`, lines can be
          minutes apart, so the consumer thread sits parked inside that read

        - The only way to release the read is to make the command's output
          stream reach EOF, which means killing the process that holds it

        - That process is created inside `stream` and is not visible to
          whatever owns the stop control (a GUI button, a signal handler),
          which typically lives on a different thread

        - `StreamHandle` is the shared object that bridges the two. The caller
          creates it, hands it to `stream`, and later calls `cancel` to stop
          the command from the outside

    info: How It Works With `stream`
        - The caller constructs a `StreamHandle` and passes it to `stream`

        - As soon as `stream` starts the subprocess it calls `bind`, giving
          the handle the live process to act on

        - When the caller invokes `cancel`, the whole process tree is killed
          (see `_kill_process_tree`). Its stdout closes, the blocked
          `readline` returns `""`, and the generator finishes normally

        - A killed process exits non-zero, so `stream` checks `cancelled` and
          skips raising `CalledProcessError` for that case. A deliberate stop
          is a normal end, not a command failure

    info: Threading And Ordering
        - `cancel` is meant to be called from a different thread than the one
          running the generator

        - Killing the tree only signals OS processes, so this is safe

        - `bind` also covers the race condition where `cancel` is called before
          the process has started. The handle remembers the request and kills
          the tree the moment it is bound

    Example:
        ```python
        handle = StreamHandle()
        gen = stream(["docker", "compose", "logs", "-f"], handle=handle)
        # ... use `gen` on a worker thread, render each line ...
        # ... from the UI thread, when the user clicks "Stop"
        handle.cancel()
        ```
    """

    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._cancelled = False

    @property
    def cancelled(self) -> bool:
        """
        Whether a stop was requested through `cancel`

        `stream` reads this after the process exits to decide whether a
        non-zero exit code is a real failure or the result of a deliberate
        stop

        Returns:
            `True` once `cancel` has been called, even if the process had not
            started yet at that moment
        """
        return self._cancelled

    def _terminate(self) -> None:
        """
        Kills the bound process tree when one is set

        Delegates to `_kill_process_tree` so the streamed command's children
        die too, closing the stdout pipe and releasing the consumer's blocked
        read. A no-op when no process is bound yet or it already exited
        """
        process = self._process
        if process is not None:
            _kill_process_tree(process)

    def bind(self, process: subprocess.Popen[str]) -> None:
        """
        Hands the handle the live process started by `stream`

        Called by `stream` right after it spawns the subprocess, so a later
        `cancel` has something to terminate. If `cancel` already ran before
        the process existed, the process is terminated immediately here so an
        early stop request is not lost

        Args:
            process (subprocess.Popen[str]): The subprocess `stream` just
                started and is about to read from
        """
        self._process = process
        if self._cancelled:
            self._terminate()

    def cancel(self) -> None:
        """
        Requests a stop, terminating the streamed process if it is running

        Marks the handle cancelled (so `stream` treats the resulting non-zero
        exit as a clean stop) and terminates the bound process. When the
        process has not started yet, `bind` performs the termination once it
        does. Safe to call from a thread other than the one using the
        generator
        """
        self._cancelled = True
        self._terminate()


def _popen(
    cmd: list[str],
    cwd: Path | None,
    *,
    new_group: bool = False,
) -> subprocess.Popen[str]:
    """
    Starts a subprocess with merged stdout/stderr as decoded text

    Args:
        cmd (list[str]): The external command to run and its arguments
        cwd (Path | None): The directory from which to run the command.
            When set to `None`, defaults to the directory from which the
            current python proccess was started from.
        new_group (bool): On POSIX, run the command as its own session/group
            leader so the whole tree can later be signalled at once (see
            `_kill_process_tree`). Ignored on Windows, where the tree is killed
            by PID instead

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
        start_new_session=new_group,
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
    handle: StreamHandle | None = None,
) -> Generator[str, None, int]:
    """
    Runs an external command in a subprocess and yields its combined output
    (stdout + stderr) line by line

    info: `handle`
        - When a `StreamHandle` is given, `handle.cancel` (typically from
          another thread) terminates the command early and the resulting
          non-zero exit is treated as a clean stop rather than a failure

        - See `StreamHandle` for more information

    Args:
        cmd (list[str]): The external command to run and its arguments
        cwd (Path | None): The directory from which to run the command.
            When set to `None`, defaults to the directory from which the
            current python proccess was started from.
        check (bool): Raises an exception on a non-zero exit status when
            `True`
        handle (StreamHandle | None): An optional cancellation token

    Yields:
        Each stripped output line as it is produced

    Returns:
        The command's exit code

    Raises:
        subprocess.CalledProcessError: If the command fails and `check=True`,
            unless the run was stopped through `handle`
        FileNotFoundError: If the executable is not found
    """
    cmd_str = " ".join(cmd)
    LOGGER.debug(f"Streaming Command : {cmd_str} (cwd={cwd or Path.cwd()})")
    # With a handle, run as a group leader so `cancel` can kill the whole tree
    process = _popen(cmd, cwd, new_group=handle is not None)
    # Expose the live process so a holder of `handle` can stop it
    if handle is not None:
        handle.bind(process)
    if process.stdout is not None:
        for line in iter(process.stdout.readline, ""):
            yield line.rstrip("\r\n")
        process.stdout.close()
    return_code = process.wait()
    # A deliberate stop terminates the process, so its non-zero exit is
    # expected and must not be reported as a command failure
    cancelled = handle is not None and handle.cancelled
    if check and return_code != 0 and not cancelled:
        LOGGER.error(f"Command Failed ({return_code}) : {cmd_str}")
        raise subprocess.CalledProcessError(return_code, cmd_str)
    return return_code
