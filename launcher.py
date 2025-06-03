import click
import os
import subprocess
import sys
from textwrap import dedent
from typing import Optional, List
from pathlib import Path
from dotenv import dotenv_values

MAIN_REPO_SUBDIR = Path("mirumoji_workspace")
MAIN_REPO_URL = "https://github.com/svdC1/mirumoji.git"
# Docker image names for local builds
FRONTEND_LOCAL_IMAGE_NAME = "mirumoji_frontend_local:latest"
BACKEND_GPU_LOCAL_IMAGE_NAME = "mirumoji_backend_gpu_local:latest"
BACKEND_CPU_LOCAL_IMAGE_NAME = "mirumoji_backend_cpu_local:latest"

# Relative paths within MAIN_REPO_SUBDIR
FRONTEND_DOCKERFILE_RELPATH = Path("build/mirumoji_open_front/Dockerfile")
FRONTEND_BUILD_CONTEXT_RELPATH = Path("build/mirumoji_open_front")
BACKEND_GPU_DOCKERFILE_RELPATH = Path("build/mirumoji_open_api/Dockerfile")
BACKEND_CPU_DOCKERFILE_RELPATH = Path("build/mirumoji_open_api/Dockerfile.cpu")
BACKEND_BUILD_CONTEXT_RELPATH = Path("build/mirumoji_open_api")

COMPOSE_PREBUILT_CPU_RELPATH = Path("compose/docker-compose.cpu.yaml")
COMPOSE_PREBUILT_GPU_RELPATH = Path("compose/docker-compose.gpu.yaml")
COMPOSE_LOCAL_CPU_RELPATH = Path("compose/docker-compose.local.cpu.yaml")
COMPOSE_LOCAL_GPU_RELPATH = Path("compose/docker-compose.local.gpu.yaml")
ENV_FILE_NAME = ".env"


# --- Helper Functions ---

def run_command(command_list: List,
                cwd: Optional[Path] = None,
                check: bool = True,
                shell: bool = False
                ):
    """
    Runs a command, streams output, and handles errors.
    """

    if not shell and not isinstance(command_list, list):
        click.echo(
            message="'command_list' must be a list for non-shell commands.",
            err=True
        )
        sys.exit(1)
    if shell:
        cmd_str = command_list
    else:
        cmd_str = " ".join(map(str, command_list))
    if not cwd:
        cwd = Path.cwd()

    click.echo(message=f"CWD: {cwd}")
    click.echo(message=f"Running command: '{cmd_str}'")

    try:
        process = subprocess.Popen(
            args=command_list,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=shell,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                click.echo(message=line, nl=False)
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
        click.echo(message=message, err=True)
        sys.exit(e.returncode or 1)

    except FileNotFoundError as e:
        message = dedent(f"""\
        Error: Command not found: {e.filename}.
        Please ensure it's installed and in your PATH.
        """)
        click.echo(message=message, err=True)
        sys.exit(1)
    except Exception as e:
        message = dedent(f"""\
        An unexpected error occurred while trying to run command '{cmd_str}':
        {e}
        """)
        click.echo(message=message, err=True)
        sys.exit(1)


def ensure_repo(repo_url: str,
                repo_path: Path):
    """
    Ensures the repository is cloned or updated,
    and submodules are initialized.
    """
    if not repo_path.is_dir():
        click.echo(
            message=f"Cloning repository: {repo_url} into {repo_path}..."
            )
        run_command(["git", "clone", repo_url, str(repo_path)])
    else:
        click.echo(
            message=f"Repo {repo_path} already exists. Fetching updates..."
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
            click.echo(
                message="Currently in a detached HEAD state."
                )
            click.echo(
                message="Attempting to checkout default branch (main)..."
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

        click.echo(
            message=f"Pulling latest changes for branch '{current_branch}'..."
            )
        run_command(["git", "pull", "origin", current_branch], cwd=repo_path)

    click.echo("Initializing/updating submodules...")
    submodule_cmd = ["git",
                     "submodule",
                     "update",
                     "--init",
                     "--recursive",
                     "--remote"]
    run_command(submodule_cmd, cwd=repo_path)
    click.echo("Repository setup complete.")


def check_env_file(expected_vars: List,
                   env_file_path: Path):
    """
    Checks for .env file and required variables.
    """
    click.echo(
        message=f"Checking for {ENV_FILE_NAME} file at: {env_file_path}"
        )
    if not env_file_path.is_file():
        message = dedent(f"""\
        Error: {ENV_FILE_NAME} file not found at {env_file_path}.
        Please create it with the variables: {', '.join(expected_vars)}
        """)
        click.echo(message=message, err=True)
        sys.exit(1)

    click.echo(f"Loading variables from {ENV_FILE_NAME}...")
    env_config = dotenv_values(env_file_path)
    missing_vars = [var for var in expected_vars if not env_config.get(var)]

    if missing_vars:
        message = dedent(f"""\
        Error: Missing or empty variables in {env_file_path}:
        {', '.join(missing_vars)}.
        Please ensure all required variables are set:
        {', '.join(expected_vars)}
        """)
        click.echo(message=message, err=True)
        sys.exit(1)
    click.echo(message="Variable Configuration Passed")


def get_options():
    try:
        click.echo("\n--- Configuration Choices ---")
        build_locally = click.confirm(
            text="Build Docker images locally?",
            default=False
        )
        use_gpu = click.confirm(
            text="Run Local GPU version of the backend (NVIDIA GPU required)?",
            default=False
        )

        click.echo(
            f"\nSelected: Build Locally: {build_locally}, Use GPU: {use_gpu}"
            )
        return (build_locally, use_gpu)

    except Exception as e:
        click.echo(
            f"Error while selecting configuration options: {e}",
            err=True
        )
        sys.exit(1)


def build_imgs_locally(use_gpu: bool):
    try:
        click.echo("\n--- Building Docker Images ---")
        click.echo("\nBuilding frontend image...")
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
        click.echo("Frontend image build complete.")

        if use_gpu:
            click.echo("Building GPU backend image...")
            backend_image_name = BACKEND_GPU_LOCAL_IMAGE_NAME
            backend_dockerfile_relpath = BACKEND_GPU_DOCKERFILE_RELPATH
        else:
            click.echo("Building CPU backend image...")
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
        click.echo("\nBackend image build complete.")

    except Exception as e:
        click.echo(
            f"Error while building local images: {e}",
            err=True
        )
        sys.exit(1)


# --- Click CLI structure ---
@click.group()
def cli():
    """Mirumoji Launcher: Setup and run Mirumoji with Docker."""
    pass


@cli.command()
def launch():
    """
    Guides through setup, image building (optional), and running Mirumoji.
    """
    click.echo("--- Mirumoji Launcher ---")

    script_location = Path(__file__).resolve().parent
    repo_path = script_location / MAIN_REPO_SUBDIR

    ensure_repo(MAIN_REPO_URL,
                repo_path)

    original_cwd = Path.cwd()
    # All subsequent paths are relative to repo_path
    os.chdir(repo_path)
    click.echo(message=f"Changed working directory to: {repo_path}")

    try:
        build_locally, use_gpu = get_options()

        if build_locally:
            build_imgs_locally(use_gpu=use_gpu)
        else:
            click.echo("\nUsing pre-built images.")

        click.echo(f"\n--- Checking {ENV_FILE_NAME} File ---")
        env_file_abs_path = Path.cwd() / ENV_FILE_NAME
        required_env_vars = ["OPENAI_API_KEY"]

        if not use_gpu:
            # CPU version requires Modal keys
            required_env_vars.extend(["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"])
        check_env_file(required_env_vars,
                       env_file_abs_path)

        if build_locally:
            if use_gpu:
                compose_file_relpath = COMPOSE_LOCAL_GPU_RELPATH
            else:
                compose_file_relpath = COMPOSE_LOCAL_CPU_RELPATH
        else:
            if use_gpu:
                compose_file_relpath = COMPOSE_PREBUILT_GPU_RELPATH
            else:
                compose_file_relpath = COMPOSE_PREBUILT_CPU_RELPATH

        click.echo("\n--- Running Docker Compose ---")
        click.echo(f"Using compose file: {compose_file_relpath}")
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
        stop_instructions = dedent(f"""\
        Mirumoji services started with {compose_file_relpath}.
        To stop them, navigate to "{repo_path}" and run:
        "docker compose -f {compose_file_relpath} down"
        """)
        click.echo(message=stop_instructions)

    except Exception as e:
        click.echo(
            f"An unexpected error occurred during the launch process: {e}",
            err=True
        )
        sys.exit(1)
    finally:
        os.chdir(original_cwd)
        click.echo(f"Returned to original working directory: {original_cwd}")


if __name__ == '__main__':
    cli()
