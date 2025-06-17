import click
import os
import subprocess
import sys
import socket
from textwrap import dedent
from typing import Optional, List
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

MAIN_REPO_SUBDIR = Path("mirumoji_workspace")
MAIN_REPO_URL = "https://github.com/svdC1/mirumoji.git"
# Docker image names for local builds
FRONTEND_LOCAL_IMAGE_NAME = "mirumoji_frontend_local:latest"
BACKEND_GPU_LOCAL_IMAGE_NAME = "mirumoji_backend_gpu_local:latest"
BACKEND_CPU_LOCAL_IMAGE_NAME = "mirumoji_backend_cpu_local:latest"

# Relative paths within MAIN_REPO
FRONTEND_DOCKERFILE_RELPATH = Path("apps/frontend/Dockerfile")
FRONTEND_BUILD_CONTEXT_RELPATH = Path("apps/frontend")
BACKEND_GPU_DOCKERFILE_RELPATH = Path("apps/backend/Dockerfile")
BACKEND_CPU_DOCKERFILE_RELPATH = Path("apps/backend/Dockerfile.cpu")
BACKEND_BUILD_CONTEXT_RELPATH = Path("apps/backend")

COMPOSE_PREBUILT_CPU_RELPATH = Path("compose/docker-compose.cpu.yaml")
COMPOSE_PREBUILT_GPU_RELPATH = Path("compose/docker-compose.gpu.yaml")
COMPOSE_PREBUILT_DOCKER_GPU_RELPATH = Path(
    "compose/docker-compose.gpu.dockerpull.yaml")
COMPOSE_PREBUILT_DOCKER_CPU_RELPATH = Path(
    "compose/docker-compose.cpu.dockerpull.yaml")
COMPOSE_LOCAL_CPU_RELPATH = Path("compose/docker-compose.local.cpu.yaml")
COMPOSE_LOCAL_GPU_RELPATH = Path("compose/docker-compose.local.gpu.yaml")
ENV_FILE_NAME = ".env"

# --- Help Messages ---
BUILD_HELP = "Build Docker images locally (--build) or pull pre-built \
    images from registry. (--pull)"

GPU_HELP = "Use GPU Version of Backend (--gpu) or CPU version (--cpu)"
REG_HELP = "Pull Images from GitHub Registry (--github-pull) or \
    from Docker Hub (--docker-pull)"
# --- Helper Functions ---


def get_host_lan_ip():
    """
    Returns the primary LAN IPv4 address of the host machine
    and loads it as an environment variable
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
            f"Error Getting Host IPv4 Address: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)
    finally:
        s.close()


def run_command(command_list: List,
                cwd: Optional[Path] = None,
                check: bool = True,
                shell: bool = False
                ):
    """
    Runs a command, streams output, and handles errors.
    """

    if not shell and not isinstance(command_list, list):
        click.secho(
            message="'command_list' must be a list for non-shell commands.",
            fg='red',
            err=True
        )
        sys.exit(1)
    if shell:
        cmd_str = command_list
    else:
        cmd_str = " ".join(map(str, command_list))
    if not cwd:
        cwd = Path.cwd()

    click.secho(message=f"CWD: {cwd}",
                fg='cyan')
    click.secho(message=f"Running command: '{cmd_str}'",
                fg='cyan')

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

        # Stream output
        if process.stdout:
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
            raise subprocess.CalledProcessError(return_code, cmd_str)
        return process
    except subprocess.CalledProcessError as e:
        message = dedent(f"""\
        Error: Command '{e.cmd}' returned non-zero exit status "
        {e.returncode}.
        """)
        click.secho(message=message, fg="red", err=True)
        sys.exit(e.returncode or 1)

    except FileNotFoundError as e:
        message = dedent(f"""\
        Error: Command not found: {e.filename}.
        Please ensure it's installed and in your PATH.
        """)
        click.secho(message=message, fg='red', err=True)
        sys.exit(1)
    except Exception as e:
        message = dedent(f"""\
        An unexpected error occurred while trying to run command '{cmd_str}':
        {e}
        """)
        click.secho(message=message, fg='red', err=True)
        sys.exit(1)


def ensure_repo(repo_url: str,
                repo_path: Path):
    """
    Ensures the repository is cloned or updated.
    """
    if not repo_path.is_dir():
        click.secho(
            message=f"Cloning repository: {repo_url} into {repo_path}...",
            fg="green"
            )
        run_command(["git", "clone", repo_url, str(repo_path)])
    else:
        click.secho(
            message=f"Repo {repo_path} already exists. Fetching updates...",
            fg="green"
            )
        run_command(["git", "fetch", "--all"],
                    cwd=repo_path)

        try:
            git_rev_parse_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
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

        if current_branch == "HEAD":
            click.secho(
                message="Currently in a detached HEAD state.",
                fg="yellow"
                )
            click.secho(
                message="Attempting to checkout default branch (main)...",
                fg="yellow"
                )
            # Try checking out 'main'
            checkout_main_cmd = ["git", "checkout", "main"]
            run_command(checkout_main_cmd,
                        cwd=repo_path,
                        check=True)

            result = subprocess.run(
                git_rev_parse_cmd,
                cwd=repo_path,
                text=True,
                capture_output=True,
                check=True
            )
            current_branch = result.stdout.strip()

        click.secho(
            message=f"Pulling latest changes for branch '{current_branch}'...",
            fg="green"
            )
        run_command(["git", "pull", "origin", current_branch], cwd=repo_path)
    click.secho("Repository setup complete.", fg="bright_green")


def check_env_file(expected_vars: List,
                   env_file_path: Path):
    """
    Checks for .env file and required variables.
    """
    click.secho(
        message=f"Checking for {ENV_FILE_NAME} file at: {env_file_path}",
        fg="green"
        )
    if not env_file_path.is_file():
        message = dedent(f"""\
        Error: {ENV_FILE_NAME} file not found at {env_file_path}.
        Please create it with the variables: {', '.join(expected_vars)}
        """)
        click.secho(message=message, fg="red", err=True)
        sys.exit(1)

    click.secho(f"Loading variables from {ENV_FILE_NAME}...", fg="green")
    env_config = dotenv_values(env_file_path)
    missing_vars = [var for var in expected_vars if not env_config.get(var)]

    if missing_vars:
        message = dedent(f"""\
        Error: Missing or empty variables in {env_file_path}:
        {', '.join(missing_vars)}.
        Please ensure all required variables are set:
        {', '.join(expected_vars)}
        """)
        click.secho(message=message, fg="red", err=True)
        sys.exit(1)
    load_dotenv(dotenv_path=env_file_path)
    click.secho(message="Variable Configuration Passed", fg="bright_green")


def get_build_locally():
    """
    Asks for user input on whether to build images locally or pull
    pre-built images.
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
            f"Error while selecting configuration options: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)


def get_gpu_cpu():
    """
    Asks for user input on whether to use CPU or GPU version.
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
            f"Error while selecting configuration options: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)


def get_registry():
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
            f"Error while selecting registry configuration options: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)


def build_imgs_locally(use_gpu: bool):
    """
    Runs the docker build command for the frontend and backend
    images based on whether CPU or GPU version is chosen.
    """
    try:
        click.secho("\n--- Building Docker Images ---", fg="blue")
        click.secho("\nBuilding frontend image...", fg="green")
        frontend_build_cmd = [
            "docker",
            "build",
            "-t",
            FRONTEND_LOCAL_IMAGE_NAME,
            "-f",
            str(FRONTEND_DOCKERFILE_RELPATH),
            str(FRONTEND_BUILD_CONTEXT_RELPATH)
        ]
        run_command(frontend_build_cmd)
        click.secho("Frontend image build complete.", fg="bright_green")

        if use_gpu:
            click.secho("Building GPU backend image...", fg="green")
            backend_image_name = BACKEND_GPU_LOCAL_IMAGE_NAME
            backend_dockerfile_relpath = BACKEND_GPU_DOCKERFILE_RELPATH
        else:
            click.secho("Building CPU backend image...", fg="green")
            backend_image_name = BACKEND_CPU_LOCAL_IMAGE_NAME
            backend_dockerfile_relpath = BACKEND_CPU_DOCKERFILE_RELPATH

        backend_build_cmd = [
            "docker",
            "build",
            "-t",
            backend_image_name,
            "-f",
            str(backend_dockerfile_relpath),
            str(BACKEND_BUILD_CONTEXT_RELPATH)
        ]
        run_command(backend_build_cmd)
        click.secho("\nBackend image build complete.", fg="bright_green")

    except Exception as e:
        click.secho(
            f"Error while building local images: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)


def configure_repo():
    """
    Displays a header, sets up the local repository path, clones or
    updates the repository, sets the working directory to the local repository
    path and returns both the local repository path and original working
    directory.
    """
    try:
        click.secho("--- Mirumoji Launcher ---", fg="magenta")
        current_user_cwd = Path.cwd()
        repo_path = current_user_cwd / MAIN_REPO_SUBDIR
        ensure_repo(MAIN_REPO_URL, repo_path)
        original_cwd = current_user_cwd
        # All subsequent paths are relative to repo_path
        os.chdir(repo_path)
        click.secho(message=f"Changed working directory to: {repo_path}",
                    fg="blue")
        return (repo_path, original_cwd)

    except Exception as e:
        click.secho(
            f"Error while configuring repository: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)


# --- Click CLI structure ---
@click.group()
def cli():
    """Mirumoji Launcher: Setup and run Mirumoji with Docker."""
    pass


@cli.command()
@click.option('--build/--pull',
              default=None,
              help=BUILD_HELP)
@click.option("--gpu/--cpu",
              default=None,
              help=GPU_HELP)
@click.option("--github-pull/--docker-pull",
              default=None,
              help=REG_HELP)
@click.option('--no-clear',
              is_flag=True,
              default=False,
              help="Do not clear the terminal after each step")
def launch(build, gpu, github_pull, no_clear):
    """
    Guides through setup, image building (optional), and running Mirumoji.
    """
    # --- Option Config ---
    try:
        if build is None:
            build_locally = get_build_locally()
            if not no_clear:
                click.clear()
        else:
            build_locally = build
        if gpu is None:
            use_gpu = get_gpu_cpu()
            if not no_clear:
                click.clear()
        else:
            use_gpu = gpu
    except Exception as e:
        click.secho(
            f"\nError while configuring options: {e}",
            fg="red",
            err=True
        )
        sys.exit(1)

    repo_path, original_cwd = configure_repo()
    if not no_clear:
        click.clear()
    try:
        if build_locally:
            build_imgs_locally(use_gpu=use_gpu)
            if not no_clear:
                click.clear()
        else:
            if github_pull is None:
                registry = get_registry()
                if not no_clear:
                    click.clear()
            else:
                if github_pull:
                    reg = "GitHub"
                else:
                    reg = "DockerHub"
                registry = reg
            click.secho("\nUsing pre-built images.", fg='green')

        click.secho(f"\n--- Checking {ENV_FILE_NAME} File ---", fg="blue")
        env_file_abs_path = original_cwd / ENV_FILE_NAME
        required_env_vars = ["OPENAI_API_KEY"]

        if not use_gpu:
            # CPU version requires Modal keys
            required_env_vars.extend(["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"])
        check_env_file(required_env_vars,
                       env_file_abs_path)
        if not no_clear:
            click.clear()
        # Get Host IPv4
        HOST_LAN_IP = get_host_lan_ip()
        if not no_clear:
            click.clear()

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

        click.secho("\n--- Running Docker Compose ---", fg="blue")
        click.secho(f"Using compose file: {compose_file_relpath}",
                    fg="bright_magenta")
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
        run_command(docker_compose_cmd)
        if not no_clear:
            click.clear()
        stop_instructions = dedent(f"""\

        --- Accessible at ---

        Local: 'https://localhost'

        LAN: 'https://{HOST_LAN_IP}'

        --- Launcher Stop Command ---

        launcher shutdown

        --- Docker Stop Command ---

        docker compose -p mirumoji down
        """)
        click.secho(message=stop_instructions, fg="bright_green")

    except Exception as e:
        click.secho(
            f"An unexpected error occurred during the launch process: {e}",
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
              help="Delete Docker Volumes")
@click.option('--no-clear',
              is_flag=True,
              default=False,
              help="Do not clear the terminal after each step")
def shutdown(clean, no_clear):
    """
    Runs docker compose down on application.
    """
    repo_path, original_cwd = configure_repo()
    if not no_clear:
        click.clear()
    if clean is None:
        delete_volumes = click.confirm(
            text="Delete Data (Docker Volumes) ?",
            default=False
            )
        if not no_clear:
            click.clear()
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
        run_command(cmd, cwd=repo_path)
        if not no_clear:
            click.clear()
        click.secho(message="All Services Stopped.", fg="bright_green")
    except Exception as e:
        click.secho(
            f"An unexpected error occurred during shutdown: {e}",
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
