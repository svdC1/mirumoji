# Launcher CLI Reference

## Introduction

> The Mirumoji Command-Line-Interface is a convenience program for automatically running the Docker Compose application. It's made available either as a [`Python Package`](https://pypi.org/project/mirumoji/) or as [`Standalone Executable`](https://github.com/svdC1/mirumoji/releases/latest) in the Releases section of the repository

> For deciding which one to use, please refer to the [`Setup Guide`](Setup-Guide.md).

> The CLI will prompt `y/N` questions which refer to the options available for a certain command. However, in order to avoid these option confirmations you can also use the specified flags for each command.

## Commands

### `launch`

> Launches the Docker Compose application.

#### Steps Performed

> -   Verifies options which were not passed as options flags.
>
> -   Clones the mirumoji repository into a `mirumoji_workspace` inside the directory in which the command is run.
>
> -   Pulls pre-built images from repository, or builds images locally depending on option chosen.
>
> -   Confirms existence of `.env` file inside the directory in which the command is run and checks presence of required API keys.
>
> -   Extracts the Local IPv4 of the machine running the command in order to create certificates for serving over HTTPS.
>
> -   Starts Docker Compose Application using the correct `docker-compose.yaml` file according to options.
>
> -   Prints Local and LAN web addresses where the application is running.

#### Options

> `--build / --pull` &rarr; Whether to build the Docker Images locally (`--build`), or pull pre-built images from a registry (--pull)

> `--gpu / --cpu` &rarr; Whether to run the GPU version (`--gpu`), or CPU (`--cpu`) version of the application

> `--github-pull / --docker-pull` &rarr; When pulling pre-built images, whether to pull from the GitHub Repository _(ghcr.io)_ or from Docker Hub _(docker.io)_

> `--no-clear` &rarr; To stop clearing the terminal screen after each stage during command execution. Default behavior is to clear the screen to avoid clutter.

---

### `launch-local`

> Launches the Docker Compose application using previously built local images

#### Steps Performed

> -   Verifies options which were not passed as options flags.
>
> -   Clones the mirumoji repository into a `mirumoji_workspace` inside the directory in which the command is run.
>
> -   Confirms existence of `.env` file inside the directory in which the command is run and checks presence of required API keys.
>
> -   Extracts the Local IPv4 of the machine running the command in order to create certificates for serving over HTTPS.
>
> -   Starts Docker Compose Application using the correct `docker-compose.yaml` file according to options.
>
> -   Prints Local and LAN web addresses where the application is running.

#### Options

> `--gpu / --cpu` &rarr; Whether to run the GPU version (`--gpu`), or CPU (`--cpu`) version of the application

> `--no-clear` &rarr; To stop clearing the terminal screen after each stage during command execution. Default behavior is to clear the screen to avoid clutter.

---

### `build`

> Builds images locally without running the application

#### Steps Performed

> -   Verifies options which were not passed as options flags.
>
> -   Clones the mirumoji repository into a `mirumoji_workspace` inside the directory in which the command is run.
>
> -   Runs Docker Build according to specified options

#### Options

> `--gpu / --cpu` &rarr; Whether to build the GPU version (`--gpu`), or CPU (`--cpu`) version of the application

> `--no-clear` &rarr; To stop clearing the terminal screen after each stage during command execution. Default behavior is to clear the screen to avoid clutter.

---

### `shutdown`

> Stops the Docker Compose Application

#### Steps Performed

> -   Verifies options which were not passed as options flags.
>
> -   Runs appropriate Docker Compose command to stop application.

#### Options

> `--clean / --no-clean` &rarr; Whether to delete Docker Volumes which where created for the application (`--clean`), or not (`--no-clean`)

> `--no-clear` &rarr; To stop clearing the terminal screen after each stage during command execution. Default behavior is to clear the screen to avoid clutter.

---
