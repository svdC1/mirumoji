# GUI Setup

This section will teach you how to get mirumoji running with the `Desktop Launcher`


!!! note "The Desktop Launcher Isn't The App"
    - The main Mirumoji application runs via [`Docker Compose`](https://docs.docker.com/compose/)

    - The `Desktop Launcher` is just a friendly front door to it which automatically runs all the Docker commands,checks if the external dependencies needed by Mirumoji are installed in your machine, and helps you manage the main application more easily

    - You still need [`Docker`](https://docs.docker.com/desktop/) to be installed and running

## Getting The Launcher

There are `2 Ways` To Run The `Desktop Launcher`

Pick The One That Fits You

=== "Standalone Bundle"

    Download the pre-built desktop bundles for your OS from the [`GitHub Release Page`](https://github.com/svdC1/mirumoji/releases)

    - Each bundle is `mirumoji-<version>-<os>.zip` folder containing a standalone executable

    - No Dependencies Required

=== "PyPI"

    Install the [`mirumoji`](https://pypi.org/project/mirumoji/) python package

    ```bash
    pip install mirumoji[gui]
    ```

    - Needs the `mirumoji[gui]` extra dependencies

    - Requires you to have `Python>=3.10` installed in your machine


### Starting The Launcher

=== "Standalone Bundle"

    - Unzip the `mirumoji-<version>-<os>.zip` folder

    === "Windows"
        Open the unzipped folder and run `Mirumoji.exe`

    === "MacOS"
        Open `Mirumoji.app`

        ???+ warning "Unsigned Build"
            Since the build is unsigned, the first launch needs Gatekeeper cleared

            - Right-Click App &rarr; `Open`

            - Alternatively, run `xattr -dr com.apple.quarantine Mirumoji.app` in the terminal

    === "Linux"
        Make the executable runnable and start it
        ```bash
        chmod +x mirumoji
        ./mirumoji
        ```

=== "PyPI"
    Run the GUI Command
    ```bash
    mirumoji gui
    ```


## Using the Launcher

<figure markdown>
![The desktop launcher Dashboard](../assets/images/gui-dashboard.png)
<figcaption>Dashboard &rarr; Start, stop, build, and view status in one place</figcaption>
</figure>

The `Desktop Launcher` Has 5 Panels

| Panel | What It Does |
| --- | --- |
| **Dashboard** | Start / Stop / Build Images / Watch Status |
| **Environment** | Run Dependency Checks *(Same as `mirumoji doctor`)* |
| **Settings** | Choose The Transcription Backend / Image Source / Image Version, Set LLM / Modal API Keys + Advanced Overrides, Delete All Local Data |
| **Logs** | Stream + Filter The Docker Compose Application's Logs |
| **Modal Host** | Deploy, Inspect, Tear Down, And Back Up The Full App On Your `Modal` Account *(mirrors the [`modal`](../cli.md#modal-host-commands) CLI commands)* |

### Typical First Run

- Open `Settings`

- Choose Your [`Transcription Backend`](index.md#transcription-backends)

- Enter Any Required API Keys *(If Using `Modal`)*

- Click `Save Configuration`

- Go Back To `Dashboard`

- Click `Up`

- Open [`https://localhost`](https://localhost) In Your Browser

<figure markdown>
![The launcher Settings panel](../assets/images/gui-settings.png)
<figcaption>Settings &rarr; Pick Transcription Backend + Image Source /  Store LLM / Modal Keys</figcaption>
</figure>

## Hosting On Modal

The `Modal Host` panel deploys and manages a full, private Mirumoji instance on your own `Modal` account, mirroring the [`mirumoji modal`](../cli.md#modal-host-commands) commands

- **Deploy** &rarr; Build And Deploy The Hosted App, Then See Its URL And Login Details

- **Status** &rarr; Check Whether The App And Its Data Volume Are Live

- **Download Data** &rarr; Back Up The Hosted Volume To A Local Folder

- **Stop** &rarr; Stop The App, Optionally Deleting The Data Volume

The config pills show what a deploy would use *(CPU, memory, requests, image version, GPU, and capacity)*

!!! tip "Full Walkthrough"
    See the [`Modal Host Setup`](modal-host.md) guide for the complete flow, including the GPU and non-preemptible host options
