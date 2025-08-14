"""
This module contains the main helper functions to check the environment and
launch the mirumoji application.
"""
import logging
import subprocess
from subprocess import Popen
from typing import (List,
                    Optional,
                    Union,
                    Generator,
                    overload,
                    Literal
                    )
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
import socket
import os
import platform

LOGGER = logging.getLogger(__name__)


def git_installed() -> subprocess.CompletedProcess[str]:
    """
    Checks if git is installed by running `git --version`

    Raises:
      subprocess.CalledProcessError: If command fails

    Returns:
      CompletedProcess[str]: The `subprocess.CompletedProcess` object
    """
    try:
        git_check = subprocess.run(
            ["git", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        LOGGER.info("Git Installed")
        return git_check
    except subprocess.CalledProcessError as e:
        LOGGER.error(
            (f"Git Check Failed: '{e.stderr}'; Return Code: '{e.returncode}'"))
        raise
    except FileNotFoundError as e:
        LOGGER.error(f"Git not found: '{e}'")
        raise


def docker_running() -> subprocess.CompletedProcess[str]:
    """
    Checks if the Docker service/daemon is currently running by executing
    `docker info` command.

    Raises:
      subprocess.CalledProcessError: If command fails

    Returns:
      CompletedProcess[str]: The `subprocess.CompletedProcess` object
    """
    try:
        p = subprocess.run(
             ["docker", "info"],
             check=True,
             capture_output=True,
             text=True
             )
        LOGGER.info("Docker is Running")
        return p
    except subprocess.CalledProcessError as e:
        LOGGER.error((
            f"Docker Check Failed: '{e.stderr}'; Return Code: '{e.returncode}'"
            ))
        raise
    except FileNotFoundError as e:
        LOGGER.error(f"Docker not found: '{e}'")
        raise


def has_nvidia_gpu() -> bool:
    """
    Checks if an NVIDIA GPU is available on the system by running nvidia-smi.

    Returns:
      bool: `False` if command returns non-zero exit status, `True` otherwhise.
    """
    if platform.system() in ["Windows", "Linux"]:
        try:
            subprocess.check_output("nvidia-smi", shell=True)
            LOGGER.info("NVIDIA GPU Detected")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            LOGGER.info("No NVIDIA GPU Detected")
            return False
    return False


def has_nvidia_container_toolkit() -> bool:
    """
    Checks if the NVIDIA Container Toolkit is installed and configured.

    Returns:
      bool: `False` if command returns non-zero exit status, `True` otherwhise.
    """
    try:
        docker_running()
    except Exception:
        LOGGER.error(("Docker is not running, cannot perform NVIDIA Container "
                      "Toolkit check"))
        raise
    try:
        if not has_nvidia_gpu():
            return False

        # Run a test container
        gpu_test = ["docker",
                    "run",
                    "--rm",
                    "--gpus",
                    "all",
                    "nvidia/cuda:12.3.0-base-ubuntu22.04",
                    "nvidia-smi"
                    ]
        LOGGER.info("Starting Nvidia Container Toolkit Test")
        run_command(gpu_test, stream=False)
        return True
    except subprocess.CalledProcessError as e:
        LOGGER.info((f"NVIDIA Container Toolkit Test Failed: '{e.stderr}';"
                     f"Return Code:'{e.returncode}'"))
        return False


def get_host_lan_ip(load_to_env: bool = True,
                    var_name: str = "HOST_LAN_IP"
                    ) -> str:
    """
    Get the primary LAN IPv4 address of the host machine and loads
    it as an environment variable.

    Args:
      load_to_env (bool, optional): If `True`, load IPv4 as an environemnt
                                    variable. Defaults to `True`
      var_name (str, optional): Name of the environment variable if
                                `load_to_env=True`. Defaults to `HOST_LAN_IP`

    Returns:
      str: The Primary LAN IPv4 address of the host machine
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        if load_to_env:
            os.environ[var_name] = ip
        return ip
    except Exception as e:
        LOGGER.error(f"Error getting LAN IPv4: '{e}'")
        raise
    finally:
        s.close()


def check_env_file(expected_vars: List[str],
                   env_file_path: Path
                   ) -> None:
    """
    Checks for existence of required `.env` file and its contents.

    Raises:
      ValueError: If `env_file_path` doesn't contain one of `expected_vars`
      FileNotFoundError: If `env_file_path` isn't a file

    Args:
      expected_vars (List[str]): List of variables that should be present
      env_file_path (Path): Path to the environment file
    """
    if not env_file_path.is_file():
        LOGGER.error(f"`.env` file not found at '{env_file_path}'")
        raise FileNotFoundError(filename=str(env_file_path))

    env_config = dotenv_values(env_file_path)
    missing_vars = [var for var in expected_vars if not env_config.get(var)]

    if missing_vars:
        e = f"Missing Variables in `.env` file : '{missing_vars}'"
        LOGGER.error(e)
        raise ValueError(e)
    # Load variables into session environment
    load_dotenv(dotenv_path=env_file_path)


@overload
def run_command(command_list: List[str],
                *,
                cwd: Optional[Path] = None,
                check: bool = True,
                shell: bool = False,
                stream: Literal[True]
                ) -> Generator[str, str, Popen[str]]:
    ...


@overload
def run_command(command_list: List[str],
                *,
                cwd: Optional[Path] = None,
                check: bool = True,
                shell: bool = False,
                stream: Literal[False]
                ) -> Popen[str]:
    ...


def run_command(command_list: List[str],
                *,
                cwd: Optional[Path] = None,
                check: bool = True,
                shell: bool = False,
                stream: bool = True
                ) -> Union[subprocess.Popen[str],
                           Generator[str, str, Popen[str]]
                           ]:
    """
    `subprocess.Popen` wrapper with error handling and logging

    Args:
      command_list (List[str]): List of command arguments to be executed
      cwd (Path, optional): Path in which to execute the command from.
                            If `None` use program execution cwd
      check (bool, optional): When True, if the command returns an error status
                              code an exception is propagated. Defaults to True
      shell (bool, optional): When True, concatenate the list of arguments
                              into a string and run in shell mode. Defaults to
                              False
      stream (bool, optional): When True, stream command output.
                               Defaults to True

    Returns:
      Union[Popen[str],Generator[str,str,Popen[str]]:
        Subprocess object with `pid`, `stdin`, `stdout`, `stderr`
        and `returncode` or a generator that yields stdout lines
        (str) and has a return value of the completed `subprocess.Popen`
        object.

    Raises:
      subprocess.CalledProcessError: If command raises an error and
                                     `check=True`

    """

    cmd_str = " ".join(map(str, command_list))

    # Concatenate command for shell
    if shell:
        command_list = cmd_str

    # Set up CWD
    if not cwd:
        cwd = Path.cwd()
    LOGGER.debug(f"CWD: '{cwd}'")
    LOGGER.debug(f"Running command '{cmd_str}'")
    # Set Up Env
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if not stream:
        try:
            process = subprocess.Popen(
                args=command_list,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=shell,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            return_code = process.wait()
            if check and return_code != 0:
                raise subprocess.CalledProcessError(
                    return_code,
                    cmd_str,
                    process.stdout,
                    process.stderr
                    )
            return process
        except subprocess.CalledProcessError as e:
            LOGGER.error(
                (f"Error: Command '{e.cmd}' returned non-zero exit status "
                 f"Return Code: '{e.returncode}'")
            )
            if check:
                raise
        except FileNotFoundError as e:
            LOGGER.error(f"Error: Command not found: '{e.filename}'.")
            if check:
                raise

    def _stream_generator() -> Generator[str, str, Popen[str]]:
        """
        A generator that yields stdout lines and returns the Popen object.
        """
        try:
            process = subprocess.Popen(
                args=command_list,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=shell,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            if process.stdout:
                yield f"Running Command: `{cmd_str}`"
                for line in iter(process.stdout.readline, ''):
                    line_content = line.strip()
                    if line_content:
                        yield line_content
                    else:
                        yield ""
                process.stdout.close()
            return_code = process.wait()
            if check and return_code != 0:
                raise subprocess.CalledProcessError(
                    return_code,
                    cmd_str,
                    process.stdout,
                    process.stderr
                    )
            return process
        except subprocess.CalledProcessError as e:
            LOGGER.error(
                (f"Error: Command '{e.cmd}' returned non-zero exit status; "
                 f"stderr: {e.stderr}; "
                 f"stdout: {e.stdout}; "
                 f"Return Code: '{e.returncode}'")
            )
            if check:
                raise
        except FileNotFoundError as e:
            LOGGER.error(f"Error: Command not found: '{e.filename}'.")
            if check:
                raise
    return _stream_generator()


def build_img(image_name: str,
              dockerfile: Path,
              build_context: Path
              ) -> Generator[str, str, Popen[str]]:
    """
    Runs the docker build command for a specified image name and streams the
    command's stdout and stderr, finally returning the `Popen` process object.

    Args:
      image_name (str): Name the image will be given
      dockerfile (Path): Path to the Dockefile which should be used
      build_context (Path): Path to the directory which should be used as the
                            build context

    Raises:
      FileNotFoundError: If `dockerfile` or `build_context` couldn't be found

    Returns:
      Generator[str, str, Popen[str]]: Generator that yields stdout lines
                                       (str) and has a return value of the
                                       completed `subprocess.Popen` object.
    """
    if not dockerfile.is_file():
        LOGGER.error(f"Dockerfile couldn't be found at '{dockerfile}'")
        raise FileNotFoundError(filename=str(dockerfile))
    if not build_context.is_dir():
        LOGGER.error(f"Build context '{build_context}' is not a directory")
        raise FileNotFoundError(filename=str(build_context))
    docker_running()
    try:
        build_cmd = [
            "docker",
            "build",
            "--no-cache",
            "-t",
            image_name,
            "-f",
            str(dockerfile),
            str(build_context)
        ]
        return run_command(build_cmd, stream=True)

    except Exception as e:
        LOGGER.error(f"Error while building '{image_name}': '{e}'")
        raise


def docker_compose(compose_command: str,
                   *,
                   name_only: bool,
                   command_flags: List[str] = [],
                   docker_compose_file: Optional[Path] = None,
                   compose_app_name: str = "mirumoji"
                   ) -> Generator[str, str, Popen[str]]:
    """
    Run a docker compose command on `docker_compose_file` with
    `compose_app_name` as the compose application name and stream
    the stdout and stderr.

    Args:
      compose_command (str): Name of the compose command to run
      name_only (bool): If `True` use only `compose_app_name` in the command.
      command_flags (List[str], optional): Optional flags to run command with.
                                           Defaults to empty list
      docker_compose_file (Path, optional): Path to the docker compose file if
                                            `name_only=False`. Defaults to
                                            `None`
      compose_app_name (str, optional): Name to give the compose app or to
                                        identify it by. Defaults to `mirumoji`

    Raises:
      FileNotFoundError: If `docker_compose_file` can't be found
      ValueError: If `name_only=False`and `docker_compose_file=None`

    Returns:
      Generator[str, str, Popen[str]]: Generator that yields stdout lines
                                       (str) and has a return value of the
                                       completed `subprocess.Popen` object.
    """
    if not name_only and docker_compose_file is None:
        LOGGER.error("`name_only=False` and compose file not provided")
        raise ValueError(
            "`docker_compose_file` must be provided is `name_only=False`"
            )
    if not name_only and not docker_compose_file.is_file():
        LOGGER.error(
            f"Docker Compose file coulnd't be found at '{docker_compose_file}'"
            )
        raise FileNotFoundError(filename=str(docker_compose_file))
    docker_running()
    base_command = [
        "docker",
        "compose"
        ]
    identifier = [
        "-p",
        compose_app_name,
        ]
    if not name_only:
        identifier = ["-f", str(docker_compose_file)] + identifier
    cmd = [
        *base_command,
        *identifier,
        compose_command,
        *command_flags
        ]
    try:
        return run_command(cmd, stream=True)
    except Exception as e:
        LOGGER.error(f"Error running compose command '{cmd}': '{e}'")
        raise


def ensure_repo(repo_url: str,
                repo_path: Path
                ) -> None:
    """
    Clones or updates a git repository `repo_url ` at `repo_path`

    Args:
      repo_url (str): The GitHub repository url
      repo_path (Path): Where to clone the repo or where to find it for updates
    """
    git_installed()
    if not repo_path.is_dir():
        LOGGER.debug(f"Cloning repository: '{repo_url}' into '{repo_path}'")
        run_command(["git", "clone", repo_url, str(repo_path)],
                    stream=False
                    )
    else:
        LOGGER.debug(f"Repo '{repo_path}' already exists. Fetching updates")
        run_command(["git", "fetch", "--all"],
                    cwd=repo_path,
                    stream=False
                    )

    try:
        # Get Current Branch
        git_rev_parse_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

        result = run_command(
            git_rev_parse_cmd,
            cwd=repo_path,
            stream=False
            )
        current_branch = result.stdout.read().strip()
    except subprocess.CalledProcessError:
        current_branch = "HEAD"

    # Handle detached states
    if current_branch == "HEAD":
        LOGGER.debug(("Currently in a detached HEAD state."
                      "Attempting to checkout default branch (main)"
                      ))

        # Try checking out 'main' and fail on error
        checkout_main_cmd = ["git", "checkout", "main"]
        run_command(checkout_main_cmd,
                    cwd=repo_path,
                    stream=False
                    )

        # Try getting current branch again and fail on error
        git_rev_parse_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

        result = run_command(
            git_rev_parse_cmd,
            cwd=repo_path,
            stream=False
            )
        current_branch = result.stdout.read().strip()
    LOGGER.debug(f"Pulling latest changes for branch '{current_branch}'")
    run_command(["git", "pull", "origin", current_branch],
                cwd=repo_path,
                stream=False)
    LOGGER.debug("Repository Setup Complete")
