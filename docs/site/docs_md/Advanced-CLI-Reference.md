# Advanced CLI Reference

The `mirumoji` command provides a command-line interface for advanced users and automation. While the `mirumoji-gui` is recommended for most users, the CLI offers more direct control.

## Installation

Ensure the launcher package is installed:

```bash
pip install mirumoji-launcher
```

## `launch`

The primary command to configure and start the application. It guides you through the setup process.

**Usage:**

```bash
mirumoji launch [OPTIONS]
```

**Options:**

-   `--build` / `--pull`: Choose between building Docker images locally or pulling them from a registry.
-   `--gpu` / `--cpu`: Select the GPU or CPU version of the backend.
-   `--github-pull` / `--docker-pull`: If pulling, specify whether to use GitHub Container Registry or Docker Hub.
-   `--no-clear`: Prevents the terminal from being cleared after each step.

**Example:**

To launch the application using pre-built images with the GPU backend:

```bash
mirumoji launch --pull --gpu
```

## `shutdown`

Stops and removes the application containers.

**Usage:**

```bash
mirumoji shutdown [OPTIONS]
```

**Options:**

-   `--clean` / `--no-clean`: If specified, this will also remove the Docker volumes associated with the application, deleting all persistent data (user profiles, media files, etc.).
-   `--no-clear`: Prevents the terminal from being cleared.

## `launch-local`

Starts the application using previously built local Docker images, skipping the build/pull selection.

**Usage:**

```bash
mirumoji launch-local [OPTIONS]
```

**Options:**

-   `--gpu` / `--cpu`: Select which locally built backend to use.
-   `--no-clear`: Prevents the terminal from being cleared.

## `build`

Builds the local Docker images without starting the application. This is useful for pre-building images before a deployment.

**Usage:**

```bash
mirumoji build [OPTIONS]
```

**Options:**

-   `--gpu` / `--cpu`: Select which backend version to build.
-   `--no-clear`: Prevents the terminal from being cleared.
