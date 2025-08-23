# Launcher GUI Guide

The Mirumoji Launcher (`mirumoji-gui`) is the recommended way to install, configure, and manage your Mirumoji application. It provides a user-friendly graphical interface that handles all the complex setup steps for you.

??? info "Installation"

    -   View the [`Setup Guide`](Setup-Guide.md) for installation instructions.

## Interface Tabs

=== "Launcher Tab"

    <figure markdown="span">
    ![Launcher Tab Screenshot](assets/images/launch.png)
    <figcaption>
    This is the main control panel for your application.
    ???+ info "**Controls**"
        |     Button    | Details                                                                                                              |
        |:-------------:|----------------------------------------------------------------------------------------------------------------------|
        | Start App     | Starts the Mirumoji application using the settings from the Configuration tab.                                       |
        | Stop App      | Stops the Mirumoji application.                                                                                      |
        | Build Locally | Builds the necessary Docker images on your machine instead of downloading them. This is for more advanced use cases. |
    ???+ info "**System Info**"
        -   Shows the status of Docker and whether an NVIDIA GPU is detected. You can click the refresh button to re-check the status.
    ???+ "**App Status**"
        -   Indicates whether the main Mirumoji application is `Running`, `Not Ready`, or `Unhealthy`.
    </figcaption>
    </figure>

=== "Configuration Tab"

    <figure markdown="span">
    ![Configuration Tab Screenshot](assets/images/config.png)
    <figcaption>
    This tab allows you to configure all aspects of your Mirumoji installation before you start it.
    ???+ info "**Image Repository**"
        Choose whether to download the pre-built Docker images from `GitHub` or `DockerHub`.
    ???+ info "**OpenAI API Key** **(Required)**"
        You must provide a valid OpenAI API key for the application's AI features to work.
    ???+ info "**Modal Tokens (CPU Only)**"
        If you are running in CPU mode, you must provide your Modal Token ID and Secret. This is required for transcription tasks.
    ???+ info "**Use Local Docker Images**"
        If toggled, the launcher will use images you built locally with the "Build Locally" button instead of pulling pre-built ones.
    ???+ info "**Clean Stop**"
        If toggled, stopping the application will also remove all of its data (Docker volumes). This is useful for a fresh start.
    ???+ info "**Use NVIDIA GPU**"
        If an NVIDIA GPU is detected on your system, this option will be available. Toggling it on will use the GPU-enabled backend for significantly faster AI performance.
        ??? warning
            The availability of the "Use NVIDIA GPU" option depends on whether an NVIDIA GPU is detected on your system and if the necessary drivers and NVIDIA Container Toolkit are installed. Refer to the [`Manual Setup Guide`](Manual-Setup.md) for more details.
    </figcaption>
    </figure>

=== "App Logs Tab"

    <figure markdown="span">
    ![Logs Tab Screenshot](./assets/images/appLogs.png)
    <figcaption>
    This tab allows you to view the real-time logs from the running Mirumoji application, which is useful for monitoring its activity or debugging issues.
    ???+ info "**Start/Stop Streaming**"
        Use these buttons to connect or disconnect from the log stream.
    </figcaption>
    </figure>
---

??? tip
    For advanced users who prefer the command line, see the [`Launcher CLI Reference`](Launcher-CLI-Docs.md)
