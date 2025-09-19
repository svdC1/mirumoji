# Launcher CLI Reference

## Introduction

> The Mirumoji Command-Line-Interface is a convenience program for automatically running the Docker Compose application. It's made available either as a [`Python Package`](https://pypi.org/project/mirumoji/) or as [`Standalone Executable`](https://github.com/svdC1/mirumoji/releases/latest) in the Releases section of the repository

??? note "Choosing between Python Package and Standalone Executable"
    For deciding which one to use, please refer to the [`Setup Guide`](Setup-Guide.md).

??? tip "Command Options and Flags"
    The CLI will prompt `y/N` questions which refer to the options available for a certain command. However, in order to avoid these option confirmations you can also use the specified flags for each command.

## Commands

``` bash
mirumoji launch [OPTIONS]
```

> Launches the Docker Compose application.

??? tip "Steps Performed"

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

??? info "Options"

    | Option                          | Description                                                                                                         |
    |---------------------------------| --------------------------------------------------------------------------------------------------------------------|
    | `--build / --pull`              | Whether to build Docker Images locally (`--build`) or pull pre-built images from a registry (`--pull`).             |
    | `--gpu / --cpu`                 | Whether to run the GPU version (`--gpu`) or CPU version (`--cpu`) of the application.                               |
    | `--github-pull / --docker-pull` | When pulling pre-built images, whether to pull from the GitHub Repository (`ghcr.io`) or Docker Hub (`docker.io`).  |
    | `--no-clear`                    | Stops clearing the terminal screen after each stage during command execution. Default is to clear.                  |

---

``` bash
mirumoji launch-local [OPTIONS] 
```

> Launches the Docker Compose application using previously built local images

??? tip "Steps Performed"

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

??? info "Options"
    | Option                 | Description                                                                                        |
    | ---------------------- | ---------------------------------------------------------------------------------------------------|
    | `--gpu / --cpu`        | Whether to run the GPU version (`--gpu`) or CPU version (`--cpu`).                                 |
    | `--no-clear`           | Stops clearing the terminal screen after each stage during command execution. Default is to clear. |

---

``` bash
mirumoji build [OPTIONS]
```

> Builds images locally without running the application

??? tip "Steps Performed"

    > -   Verifies options which were not passed as options flags.
    >
    > -   Clones the mirumoji repository into a `mirumoji_workspace` inside the directory in which the command is run.
    >
    > -   Runs Docker Build according to specified options

??? info "Options"
    | Option          | Description                                                                                        |
    | ----------------| ---------------------------------------------------------------------------------------------------|
    | `--gpu / --cpu` | Whether to build the GPU version (`--gpu`) or CPU version (`--cpu`).                               |
    | `--no-clear`    | Stops clearing the terminal screen after each stage during command execution. Default is to clear. |


---

``` bash
mirumoji shutdown [OPTIONS]
```

> Stops the Docker Compose Application

??? tip "Steps Performed"

    > -   Verifies options which were not passed as options flags.
    >
    > -   Runs appropriate Docker Compose command to stop application.

??? info "Options"
    | Option                 | Description                                                                                        |
    | -----------------------|----------------------------------------------------------------------------------------------------|
    | `--clean / --no-clean` | Whether to delete Docker Volumes created for the application (`--clean`) or not (`--no-clean`).    |
    | `--no-clear`           | Stops clearing the terminal screen after each stage during command execution. Default is to clear. |


---

``` bash
mirumoji gui
```

> Starts the [`GUI Launcher`](Launcher-GUI-Guide.md)
