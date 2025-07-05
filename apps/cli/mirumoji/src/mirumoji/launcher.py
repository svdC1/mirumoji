"""
This module defines the `Click` CLI application to automatically
setup the `Mirumoji` Docker Compose application.
"""

import click
import os
import subprocess
from subprocess import Popen
import sys
import socket
from textwrap import dedent
from typing import (Optional,
                    List,
                    Tuple,
                    Callable,
                    TypeVar,
                    ParamSpec
                    )
from functools import wraps
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

# -----------------------------
# --- Pre-defined Constants ---

# Repository URL and Path constants
MAIN_REPO_SUBDIR = Path("mirumoji_workspace")
MAIN_REPO_URL = "https://github.com/svdC1/mirumoji.git"

# Docker Image names for local builds
FRONTEND_LOCAL_IMAGE_NAME = "mirumoji_frontend_local:latest"
BACKEND_GPU_LOCAL_IMAGE_NAME = "mirumoji_backend_gpu_local:latest"
BACKEND_CPU_LOCAL_IMAGE_NAME = "mirumoji_backend_cpu_local:latest"

# Relative Paths for Dockerfiles within repository
FRONTEND_DOCKERFILE_RELPATH = Path("apps/frontend/Dockerfile")
BACKEND_GPU_DOCKERFILE_RELPATH = Path("apps/backend/Dockerfile")
BACKEND_CPU_DOCKERFILE_RELPATH = Path("apps/backend/Dockerfile.cpu")

# Relative Paths for local build contexts within repository
BACKEND_BUILD_CONTEXT_RELPATH = Path("apps/backend")
FRONTEND_BUILD_CONTEXT_RELPATH = Path("apps/frontend")

# Relative Paths for compose files withing repository
COMPOSE_PREBUILT_CPU_RELPATH = Path("compose/docker-compose.cpu.yaml")
COMPOSE_PREBUILT_GPU_RELPATH = Path("compose/docker-compose.gpu.yaml")
COMPOSE_PREBUILT_DOCKER_GPU_RELPATH = Path(
    "compose/docker-compose.gpu.dockerpull.yaml")
COMPOSE_PREBUILT_DOCKER_CPU_RELPATH = Path(
    "compose/docker-compose.cpu.dockerpull.yaml")
COMPOSE_LOCAL_CPU_RELPATH = Path("compose/docker-compose.local.cpu.yaml")
COMPOSE_LOCAL_GPU_RELPATH = Path("compose/docker-compose.local.gpu.yaml")
# ---------------------
# --- Env File Name ---

ENV_FILE_NAME = ".env"

# -----------------------------
# --- Command Help Messages ---
BUILD_HELP = "Build Docker images locally (--build) or pull pre-built \
    images from registry. (--pull)"

GPU_HELP = "Use GPU Version of Backend (--gpu) or CPU version (--cpu)"
REG_HELP = "Pull Images from GitHub Registry (--github-pull) or \
    from Docker Hub (--docker-pull)"

# ------------------------
# --- Helper Functions ---


def check_git_installed() -> None:
    """
    Click command helper which checks if `git` is installed
    in the system.
    """
    try:
        subprocess.run(
            ["git", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_message = dedent("""\
        Error: Git is not installed or not in your PATH.
        Please install Git and ensure it is accessible from your terminal.
        """)
        click.secho(error_message, fg="red", err=True)
        sys.exit(1)


def check_docker_running() -> None:
    """
    Click command helper which checks if the
    Docker service/daemon is currently running
    """
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_message = dedent("""\
        Error: Docker is not running.
        Please start Docker Desktop and try again.
        """)
        click.secho(error_message, fg="red", err=True)
        sys.exit(1)


def get_host_lan_ip() -> str:
    """
    Click command helper which returns the primary
    LAN IPv4 address of the host machine and loads
    it as an environment variable.

    Returns:
      str: The Primary LAN IPv4 address of the host machine
    """
    click.secho("\n--- Getting HOST IPv4 ---", fg="blue")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        click.secho(f"HOST IPv4 Acquired : {ip}", fg="bright_green")
        os.environ["HOST_LAN_IP"] = ip
        return ip
    except Exception as e:
        click.secho(
            f"Error Getting Host IPv4 Address: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)
    finally:
        s.close()


def run_command(command_list: List[str],
                cwd: Optional[Path] = None,
                check: bool = True,
                shell: bool = False,
                stream: bool = True
                ) -> Popen[str]:
    """
    Click command helper which runs a command as a subprocess,
    streams its output and handles errors.

    Args:
      command_list (List[str]): List of command arguments to be executed
      cwd (Path, optional): Path in which to execute the command from
      check (bool, optional): When True, if the command returns an error status
                              code an exception is propagated. Defaults to True
      shell (bool, optional): When True, concatenate the list of arguments
                              into a string and run in shell mode. Defaults to
                              False
      stream (bool, optional): When True, stream command output to `Click`.
                               Defaults to True.

    Returns:
      Popen[str]: Subprocess object with `pid`, `stdin`, `stdout`, `stderr`
                  and `returncode`

    Raises:
      subprocess.CalledProcessError: If command raises an error and
                                     `check=True`
      Exception: If an unexpected Exception occurs while running the command.

    """

    if not isinstance(command_list, list):
        click.secho(
            message="'command_list' must be a list.",
            fg='red',
            err=True
        )
        sys.exit(1)

    cmd_str = " ".join(map(str, command_list))

    # Concatenate command for shell
    if shell:
        command_list = cmd_str

    # Set up CWD
    if not cwd:
        cwd = Path.cwd()

    click.secho(message=f"CWD: {cwd}",
                fg='cyan')
    click.secho(message=f"Running command: '{cmd_str}'",
                fg='cyan')

    # If it's a docker command make sure it's running
    if "docker" in command_list[0]:
        check_docker_running()

    # If it's a GIT command make sure it's installed
    if "git" in command_list[0]:
        check_git_installed()

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
            errors='replace'
        )

        # Stream Output with Click
        if stream and process.stdout:
            for line in iter(process.stdout.readline, ''):
                line_content = line.rstrip('\r\n')
                if line_content:
                    click.secho(message=f"  ↪ {line_content}",
                                fg="cyan"
                                )
                else:
                    click.echo("")
            process.stdout.close()

        return_code = process.wait()
        if check and return_code != 0:
            # Error message printed after all output has been streamed
            raise subprocess.CalledProcessError(return_code,
                                                cmd_str,
                                                process.stdout,
                                                process.stderr
                                                )
        return process

    # Catch process error and display with Click when check is True
    except subprocess.CalledProcessError as e:
        message = dedent(f"""\
        Error: Command '{e.cmd}' returned non-zero exit status
        Return Code: '{e.returncode}'
        """)
        click.secho(message=message, fg="red", err=True)
        sys.exit(e.returncode or 1)

    # Catch not found command errors
    except FileNotFoundError as e:
        message = dedent(f"""\
        Error: Command not found: '{e.filename}'.
        Please ensure it's installed and in your PATH.
        """)
        click.secho(message=message, fg='red', err=True)
        sys.exit(1)

    # Catch general exceptions and display with Click
    except Exception as e:
        message = dedent(f"""\
        An unexpected error occurred while trying to run command '{cmd_str}':
        '{e}'
        """)
        click.secho(message=message, fg='red', err=True)
        sys.exit(1)


def ensure_repo(repo_url: str,
                repo_path: Path
                ) -> None:
    """
    Click command helper which ensures the repository is cloned or updated.

    Args:
      repo_url (str): The GitHub repository url
      repo_path (Path): Where to clone the repo or where to find it for updates
    """
    if not repo_path.is_dir():
        click.secho(
            message=f"Cloning repository: '{repo_url}' into '{repo_path}' ...",
            fg="green"
            )
        run_command(["git", "clone", repo_url, str(repo_path)])
    else:
        click.secho(
            message=f"Repo '{repo_path}' already exists. Fetching updates ...",
            fg="green"
            )
        run_command(["git", "fetch", "--all"],
                    cwd=repo_path)

        try:
            # Get Current Remote Branch
            git_rev_parse_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

            # Not using `run_command` here to catch the error without sys.exit
            # GIT installation is already checked by previous commands
            result = subprocess.run(
                git_rev_parse_cmd,
                cwd=repo_path,
                text=True,
                capture_output=True,
                check=True
            )
            current_branch = result.stdout.strip()
        except subprocess.CalledProcessError:
            current_branch = "HEAD"

        # Handle detached states
        if current_branch == "HEAD":
            click.secho(
                message="Currently in a detached HEAD state.",
                fg="yellow"
                )
            click.secho(
                message="Attempting to checkout default branch (main) ...",
                fg="yellow"
                )

            # Try checking out 'main' and fail on error
            checkout_main_cmd = ["git", "checkout", "main"]
            run_command(checkout_main_cmd,
                        cwd=repo_path,
                        check=True
                        )

            # Try getting current branch again and exit on error
            git_rev_parse_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

            result = run_command(
                git_rev_parse_cmd,
                cwd=repo_path,
                check=True,
                stream=False
            )
            current_branch = result.stdout.strip()

        click.secho(
            message=f"Pulling latest changes for branch '{current_branch}'...",
            fg="green"
            )
        run_command(["git", "pull", "origin", current_branch], cwd=repo_path)
    click.secho("Repository Setup Complete", fg="bright_green")


def check_env_file(expected_vars: List[str],
                   env_file_path: Path
                   ) -> None:
    """
    Click command helper which checks for existence of
    required `.env` file and its contents.

    Args:
      expected_vars (List[str]): List of variables that should be present
      env_file_path (Path): Path to the environment file
    """
    click.secho(
        message=f"Checking for '{ENV_FILE_NAME}' file at: '{env_file_path}'",
        fg="green"
        )
    if not env_file_path.is_file():
        message = dedent(f"""\
        Error: '{ENV_FILE_NAME}' file not found at '{env_file_path}'.
        Please create it with the variables: '{', '.join(expected_vars)}'
        """)
        click.secho(message=message, fg="red", err=True)
        sys.exit(1)

    click.secho(f"Loading variables from '{ENV_FILE_NAME}' ...", fg="green")
    env_config = dotenv_values(env_file_path)
    missing_vars = [var for var in expected_vars if not env_config.get(var)]

    if missing_vars:
        message = dedent(f"""\
        Error: Missing or empty variables in '{env_file_path}':
        {', '.join(missing_vars)}.
        Please ensure all required variables are set:
        {', '.join(expected_vars)}
        """)
        click.secho(message=message, fg="red", err=True)
        sys.exit(1)
    # Load variables into session environment
    load_dotenv(dotenv_path=env_file_path)
    click.secho(message="Variable Configuration Passed", fg="bright_green")


def get_build_locally() -> bool:
    """
    Click command helper which asks for user input on
    whether to build images locally or pull pre-built images.

    Returns:
      bool: True for building locally, False for using pre-built images.
    """
    try:
        click.secho("\n--- Build Configuration ---", fg="blue")
        build_locally = click.confirm(
            text="Build Docker images locally?",
            default=False
        )
        click.secho(
            f"\nSelected:\nBuild Locally: {build_locally}",
            fg="blue"
            )
        return build_locally

    except Exception as e:
        click.secho(
            f"Error while selecting configuration options: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)


def get_gpu_cpu() -> bool:
    """
    Click command helper which asks for user input on
    whether to use GPU or CPU version of backend.

    Returns:
      bool: True for GPU version, False for CPU version
    """
    try:
        click.secho("\n--- Backend Configuration ---", fg="blue")
        use_gpu = click.confirm(
            text="Run Local GPU version of the backend (NVIDIA GPU required)?",
            default=False
        )

        click.secho(
            f"\nSelected:\nUse GPU: {use_gpu}",
            fg="blue"
            )
        return use_gpu

    except Exception as e:
        click.secho(
            f"Error while selecting configuration options: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)


def get_registry() -> str:
    """
    Click command helper which asks for user input on
    whether to use pull pre-built images from GitHub
    Registry or from Docker Hub Registry.

    Returns:
      str: `GitHub` for GitHub Registry or `DockerHub` for Docker Hub Registry
    """
    try:
        click.secho("\n--- Registry Configuration ---", fg="blue")
        pull_registry = click.confirm(
            text="Pull from GitHub Registry ? (N = Pull from DockerHub)",
            default=False
            )
        if pull_registry:
            reg = "GitHub"
        else:
            reg = "DockerHub"
        click.secho(
            f"\nSelected:\nRegistry:{reg}",
            fg="blue"
            )
        return reg

    except Exception as e:
        click.secho(
            f"Error while selecting registry configuration options: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)


def build_imgs_locally(use_gpu: bool) -> None:
    """
    Click command helper which runs the docker build command
    for the frontend and backend images based on whether CPU or GPU
    version is chosen.

    Args:
      use_gpu (bool): True to use GPU version, False to use CPU version
    """
    try:
        click.secho("\n--- Building Docker Images ---", fg="blue")
        click.secho("\nBuilding Frontend Image ...", fg="green")
        frontend_build_cmd = [
            "docker",
            "build",
            "--no-cache",
            "-t",
            FRONTEND_LOCAL_IMAGE_NAME,
            "-f",
            str(FRONTEND_DOCKERFILE_RELPATH),
            str(FRONTEND_BUILD_CONTEXT_RELPATH)
        ]
        run_command(frontend_build_cmd)
        click.secho("Frontend Image Build Complete", fg="bright_green")

        if use_gpu:
            click.secho("Building GPU Backend Image ...", fg="green")
            backend_image_name = BACKEND_GPU_LOCAL_IMAGE_NAME
            backend_dockerfile_relpath = BACKEND_GPU_DOCKERFILE_RELPATH
        else:
            click.secho("Building CPU Backend Image ...", fg="green")
            backend_image_name = BACKEND_CPU_LOCAL_IMAGE_NAME
            backend_dockerfile_relpath = BACKEND_CPU_DOCKERFILE_RELPATH

        backend_build_cmd = [
            "docker",
            "build",
            "--no-cache",
            "-t",
            backend_image_name,
            "-f",
            str(backend_dockerfile_relpath),
            str(BACKEND_BUILD_CONTEXT_RELPATH)
        ]
        run_command(backend_build_cmd)
        click.secho("\nBackend Image Build Complete.", fg="bright_green")

    except Exception as e:
        click.secho(
            f"Error while building local images: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)


def configure_repo() -> Tuple[Path, Path]:
    """
    Click command helper which displays a header, sets up the local repository
    path, clones or updates the repository, sets the working directory to the
    local repository path.

    Returns:
      Tuple[Path]: contains both the local repository path and the
                   original working directory.
    """
    try:
        click.secho("--- Mirumoji Launcher ---", fg="magenta")
        current_user_cwd = Path.cwd()
        repo_path = current_user_cwd / MAIN_REPO_SUBDIR
        ensure_repo(MAIN_REPO_URL, repo_path)
        original_cwd = current_user_cwd
        # All subsequent paths are relative to repo_path
        os.chdir(repo_path)
        click.secho(message=f"Changed Working Directory To: '{repo_path}'",
                    fg="blue")
        return (repo_path, original_cwd)

    except Exception as e:
        click.secho(
            f"Error while configuring repository: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)


P = ParamSpec("P")
R = TypeVar("R")


def clear_wrapper(func: Callable[P, R],
                  no_clear: bool,
                  ) -> Callable[P, R]:
    """
    Decorator to call a helper function and clean the terminal after execution.

    Args:
      no_clean (bool, optional): If True, function is run without cleaning
                                 terminal
      func (Callable[P,R]): Helper function object

    Returns:
      Callable[P,R]: Wrapped function with clear choice applied
    """

    @wraps(func)
    def inner(*args: P.args,
              **kwargs: P.kwargs
              ) -> R:
        r = func(*args, **kwargs)
        if not no_clear:
            click.clear()
        return r
    return inner


# -----------------
# --- Click CLI ---

@click.group()
def cli():
    """
    Mirumoji Launcher: Setup and run Mirumoji with Docker.
    """
    pass


@cli.command()
@click.option('--build/--pull',
              default=None,
              help=BUILD_HELP
              )
@click.option("--gpu/--cpu",
              default=None,
              help=GPU_HELP
              )
@click.option("--github-pull/--docker-pull",
              default=None,
              help=REG_HELP
              )
@click.option('--no-clear',
              is_flag=True,
              default=False,
              help="Do not clear the terminal after each step"
              )
def launch(build: Optional[bool],
           gpu: Optional[bool],
           github_pull: Optional[bool],
           no_clear: bool
           ):
    """
    Guides through the Mirumoji application setup with Docker
    """
    # --- Option Config ---
    try:
        # Build Locally Option / Confirmation
        if build is None:
            build_locally = clear_wrapper(get_build_locally, no_clear)()
        else:
            build_locally = build

        # GPU or CPU Option / Confirmation
        if gpu is None:
            use_gpu = clear_wrapper(get_gpu_cpu, no_clear)()
        else:
            use_gpu = gpu

    except Exception as e:
        click.secho(
            f"\nError while configuring options: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)

    # --- Pull Repo ---
    _, original_cwd = clear_wrapper(configure_repo, no_clear)()

    # --- Image Configuration ---
    try:
        # Build Locally
        if build_locally:
            clear_wrapper(build_imgs_locally, no_clear)(use_gpu=use_gpu)

        # Pull pre-built
        else:
            # --- Option Config ---
            # Pull from GitHub or DockerHub Option / Confirmation
            if github_pull is None:
                registry = clear_wrapper(get_registry, no_clear)()
            else:
                if github_pull:
                    reg = "GitHub"
                else:
                    reg = "DockerHub"
                registry = reg
            click.secho("\nUsing pre-built images.", fg='green')

        # --- Environment Configuration ---
        click.secho(f"\n--- Checking '{ENV_FILE_NAME}' File ---", fg="blue")
        env_file_abs_path = original_cwd / ENV_FILE_NAME
        required_env_vars = ["OPENAI_API_KEY"]

        # CPU version requires Modal keys
        if not use_gpu:
            required_env_vars.extend(["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"])

        clear_wrapper(check_env_file, no_clear)(required_env_vars,
                                                env_file_abs_path
                                                )

        # --- Get Host IPv4 ---
        HOST_LAN_IP = clear_wrapper(get_host_lan_ip, no_clear)()
        # --- Choose Docker Compose ---
        if build_locally:
            if use_gpu:
                compose_file_relpath = COMPOSE_LOCAL_GPU_RELPATH
            else:
                compose_file_relpath = COMPOSE_LOCAL_CPU_RELPATH
        else:
            if use_gpu:
                if registry == "DockerHub":
                    compose_file_relpath = COMPOSE_PREBUILT_DOCKER_GPU_RELPATH
                else:
                    compose_file_relpath = COMPOSE_PREBUILT_GPU_RELPATH
            else:
                if registry == "DockerHub":
                    compose_file_relpath = COMPOSE_PREBUILT_DOCKER_CPU_RELPATH
                else:
                    compose_file_relpath = COMPOSE_PREBUILT_CPU_RELPATH

        # --- Start Application ---
        click.secho("\n--- Running Docker Compose ---", fg="blue")
        click.secho(f"Using Compose File: '{compose_file_relpath}'",
                    fg="bright_magenta"
                    )
        docker_compose_cmd = [
            "docker",
            "compose",
            "-f",
            str(compose_file_relpath),
            "-p",
            "mirumoji",
            "up",
            "-d"
        ]
        clear_wrapper(run_command, no_clear)(docker_compose_cmd)

        # --- Display Instructions ---
        stop_instructions = dedent(f"""\

        --- Accessible at ---

        Local: 'https://localhost'

        LAN: 'https://{HOST_LAN_IP}'

        --- CLI Stop Command ---

        mirumoji shutdown

        --- Docker Stop Command ---

        docker compose -p mirumoji down
        """)
        click.secho(message=stop_instructions, fg="bright_green")

    except Exception as e:
        click.secho(
            f"An unexpected error occurred during the launch process: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)
    finally:
        os.chdir(original_cwd)
        click.secho(f"Returned to original working directory: {original_cwd}",
                    fg="blue")


@cli.command()
@click.option("--clean/--no-clean",
              default=None,
              help="Delete Docker Volumes"
              )
@click.option('--no-clear',
              is_flag=True,
              default=False,
              help="Do not clear the terminal after each step"
              )
def shutdown(clean: Optional[bool],
             no_clear: bool
             ):
    """
    Stops application by running Docker Compose Down.
    """
    # --- Update Repository ---
    repo_path, original_cwd = clear_wrapper(configure_repo, no_clear)()

    # --- Option Config ---
    # Clean Option / Confirmation
    if clean is None:
        delete_volumes = clear_wrapper(click.confirm, no_clear)(
            text="Delete Data (Docker Volumes) ?",
            default=False
            )
    else:
        delete_volumes = clean
    try:
        cmd = ['docker',
               'compose',
               '-p',
               'mirumoji',
               "down"
               ]
        if delete_volumes:
            cmd.append("-v")
        clear_wrapper(run_command, no_clear)(cmd, cwd=repo_path)
        click.secho(message="All Services Stopped", fg="bright_green")
    except Exception as e:
        click.secho(
            f"An unexpected error occurred during shutdown: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)
    finally:
        os.chdir(original_cwd)
        click.secho(f"Returned to original working directory: {original_cwd}",
                    fg="blue")


@cli.command()
@click.option("--gpu/--cpu",
              default=None,
              help=GPU_HELP
              )
@click.option('--no-clear',
              is_flag=True,
              default=False,
              help="Do not clear the terminal after each step"
              )
def launch_local(gpu: Optional[bool],
                 no_clear: bool
                 ):
    """
    Launch Mirumoji with previously built local images
    """
    # --- Option Config ---
    try:
        # GPU or CPU Option / Confirmation
        if gpu is None:
            use_gpu = clear_wrapper(get_gpu_cpu, no_clear)()
        else:
            use_gpu = gpu

    except Exception as e:
        click.secho(
            f"\nError while configuring options: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)

    # Pull Repo
    _, original_cwd = clear_wrapper(configure_repo, no_clear)()
    try:
        # --- Environment Configuration ---
        click.secho(f"\n--- Checking '{ENV_FILE_NAME}' File ---", fg="blue")
        env_file_abs_path = original_cwd / ENV_FILE_NAME
        required_env_vars = ["OPENAI_API_KEY"]

        # CPU version requires Modal keys
        if not use_gpu:
            required_env_vars.extend(["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"])

        clear_wrapper(check_env_file, no_clear)(required_env_vars,
                                                env_file_abs_path
                                                )

        # --- Get Host IPv4 ---
        HOST_LAN_IP = clear_wrapper(get_host_lan_ip, no_clear)()

        # --- Choose Docker Compose ---
        if use_gpu:
            compose_file_relpath = COMPOSE_LOCAL_GPU_RELPATH
        else:
            compose_file_relpath = COMPOSE_LOCAL_CPU_RELPATH

        # --- Start Application ---
        click.secho("\n--- Running Docker Compose ---", fg="blue")
        click.secho(f"Using Compose File: '{compose_file_relpath}'",
                    fg="bright_magenta"
                    )
        docker_compose_cmd = [
            "docker",
            "compose",
            "-f",
            str(compose_file_relpath),
            "-p",
            "mirumoji",
            "up",
            "-d"
        ]
        clear_wrapper(run_command, no_clear)(docker_compose_cmd)

        # --- Display Instructions ---
        stop_instructions = dedent(f"""\

        --- Accessible at ---

        Local: 'https://localhost'

        LAN: 'https://{HOST_LAN_IP}'

        --- CLI Stop Command ---

        mirumoji shutdown

        --- Docker Stop Command ---

        docker compose -p mirumoji down
        """)
        click.secho(message=stop_instructions, fg="bright_green")

    except Exception as e:
        click.secho(
            f"An unexpected error occurred during the launch process: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)
    finally:
        os.chdir(original_cwd)
        click.secho(f"Returned to original working directory: {original_cwd}",
                    fg="blue")


@cli.command()
@click.option("--gpu/--cpu",
              default=None,
              help=GPU_HELP
              )
@click.option('--no-clear',
              is_flag=True,
              default=False,
              help="Do not clear the terminal after each step"
              )
def build(gpu: Optional[bool],
          no_clear: bool
          ):
    """
    Build local images only, but don't run application
    """
    # --- Option Config ---
    try:
        # GPU or CPU Option / Confirmation
        if gpu is None:
            use_gpu = clear_wrapper(get_gpu_cpu, no_clear)()
        else:
            use_gpu = gpu

    except Exception as e:
        click.secho(
            f"\nError while configuring options: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)

    # Pull Repo
    _, original_cwd = clear_wrapper(configure_repo, no_clear)()

    try:
        clear_wrapper(build_imgs_locally, no_clear)(use_gpu=use_gpu)
        if use_gpu:
            click.secho(
                (f"\nBuilt Images\nFrontend: {FRONTEND_LOCAL_IMAGE_NAME}"
                 f"\nBACKEND: {BACKEND_GPU_LOCAL_IMAGE_NAME}"),
                fg="bright_green"
                )
        else:
            click.secho(
                (f"\nBuilt Images\nFrontend: {FRONTEND_LOCAL_IMAGE_NAME}"
                 f"\nBACKEND: {BACKEND_CPU_LOCAL_IMAGE_NAME}"),
                fg="bright_green"
                )

    except Exception as e:
        click.secho(
            f"\nUnexpected error while building images: '{e}'",
            fg="red",
            err=True
        )
        sys.exit(1)
    finally:
        os.chdir(original_cwd)
        click.secho(f"Returned to original working directory: {original_cwd}",
                    fg="blue")


if __name__ == '__main__':
    cli()
