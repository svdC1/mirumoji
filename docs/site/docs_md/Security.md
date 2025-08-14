## Security Considerations

> Regarding the `GUI Launcher`. Since this is a bundled application program, it's common to have securities concerns regarding what exactly it is executing. This has been bundled as a GUI executable mainly for the sake of convenience, so that you don't have to manually find which `docker-compose` file is suitable for the version you want to run, look up docker build and compose commands, etc.

-   **Option 1 - GUI Launcher Program**

> The executables for the various OSes are created in a [`GitHub Actions Runner`](https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners) with [`PyInstaller`](https://github.com/pyinstaller/pyinstaller) and the code used to create them can be found in this repository at [`.github/workflows/build_release.yaml`](https://github.com/svdC1/mirumoji/blob/main/.github/workflows/build_release.yaml).

> If you would like this added convenience of the executable, you can find instructions at the [`Setup Guide`](Setup-Guide.md)

-   **Option 2**

> If you prefer to not use the executable, you can still run the `launcher.py` or `gui_launcher.py` script with your own Python environment by following the instructions detailed in [`Advanced CLI Reference`](Adavanced-CLI-Reference.md)

-   **Manual Setup**

> If you prefer to download the specific `docker-compose` file for the version you want to run and use it to build the containers directly, you can follow the instructions provided at the [`Manual Setup`](Manual-Setup.md) page.
