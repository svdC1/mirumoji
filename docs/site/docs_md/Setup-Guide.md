# Setup Guide

This guide will help you get the Mirumoji application running on your system.

## **System Prerequisites**

-   **Git**

> The launcher uses Git to fetch the application files. [`Download Git`](https://git-scm.com/downloads).

-   **Docker Desktop**

> Mirumoji runs using Docker containers. Docker Desktop provides the necessary Docker engine and command-line tools.
>
> -   [`Download Docker Desktop for Windows`](https://www.docker.com/products/docker-desktop/)
> -   [`Download Docker Desktop for macOS`](https://www.docker.com/products/docker-desktop/)
> -   [`Download Docker Desktop for Linux`](https://docs.docker.com/desktop/setup/install/linux/)

## Security Considerations

Since this is a bundled application program, it's common to have securities concerns regarding what exactly it is executing. This has been bundled as an executable mainly for the sake of convenience, so that you don't have to manually find which `docker-compose` file is suitable for the version you want to run, look up docker build and compose commands, etc.

-   Note

> On newer macOS versions, you might see a security warning the first time you run the launcher because it's a downloaded application. You may need to go to "System Settings" > "Privacy & Security", scroll down, and click "Open Anyway" or allow the app.

> **GUI Launcher**
>
> The executables for the various OSes are created in a [`GitHub Actions Runner`](https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners) with [`PyInstaller`](https://github.com/pyinstaller/pyinstaller) and the code used to create them can be found in this repository at [`.github/workflows/build_release.yaml`](https://github.com/svdC1/mirumoji/blob/main/.github/workflows/build_release.yaml). All the executable does is execute the [`launcher.py`](https://github.com/svdC1/mirumoji/blob/main/apps/cli/launcher.py) file, like the [`Python Package Option`](#python-package), with the added convenience that you don't need to have python, or the python dependencies the script needs, installed in order to run it.

> **Application**
>
> On the first time access on any device, the browser will display a security warning because the HTTPS certificate is [`self-signed`](https://www.keyfactor.com/blog/self-signed-certificate-risks/). This presents very little risk since the application runs entirely inside your system and is only available inside your local network. To learn more about this you can follow the link provided on `self-signed`.

## Setup Options

-   [`**GUI Launcher**`](#gui-launcher)

-   [`**Python Package**`](#python-package)

> If you prefer to not use the executable, you can still use the [`mirumoji`](https://pypi.org/project/mirumoji/) package within your own Python environment.

-   **Manual Setup**

> If you prefer to download the specific `docker-compose` file for the version you want to run and use it to build the containers directly, you can follow the instructions provided at the page linked in the [`Manual Setup`](#manual-setup) section below.

---

## GUI Launcher

### 1 - **Download the CLI Launcher**

> -   Download the executable for your operating system and place somewhere convenient
>     -   **Windows:** [`mirumoji-launcher-windows.exe`](https://github.com/svdC1/mirumoji/releases/latest/download/mirumoji-launcher-windows.exe)
>     -   **macOS:** [`mirumoji-launcher-macos`](https://github.com/svdC1/mirumoji/releases/latest/download/mirumoji-launcher-macos)
>     -   **Linux:** [`mirumoji-launcher-linux`](https://github.com/svdC1/mirumoji/releases/latest/download/mirumoji-launcher-linux)

### 2 - **Make the Launcher Executable (macOS and Linux only)**

> 1.  Open your terminal.
> 2.  Navigate to the directory where you saved the launcher.
> 3.  Make the file executable:
>     ```bash
>     chmod +x mirumoji-launcher-linux
>     ```

### 4 - **Run the Launcher**

> -   **Windows:**
>     1.  Open Command Prompt or PowerShell.
>     2.  Navigate to the directory where you saved `mirumoji-launcher-windows.exe`.
>     3.  Run the launcher by typing:
>         ```bash
>         .\mirumoji-launcher-windows.exe gui
>         ```
> -   **macOS:**
>     1.  In the Terminal (after making it executable), run:
>         ```bash
>         ./mirumoji-launcher-macos gui
>         ```
> -   **Linux:**
>     1.  In your terminal (after making it executable), run:
>         ```bash
>         ./mirumoji-launcher-linux gui
>         ```

### 5 - Start Through GUI

> If you have any doubts about the GUI you can check the [`Launcher GUI Guide`](Launcher-GUI-Guide.md)

---

## Python Package

### 1 - **Install**

> Install the [`mirumoji python package`](https://pypi.org/project/mirumoji/)
>
> ```bash
> pip install mirumoji
> ```

### 2 - **Run the GUI**

> In the same python environment you installed the mirumoji package run

> ```bash
> mirumoji-gui
> ```

---

## Accessing the Application

> Once the containers are running the application will be live in your [localhost](https://localhost) over HTTPS.

> You can access it from any device inside your local network by accessing your computer's local [`IPv4 address`](https://geekflare.com/consumer-tech/find-ip-address-of-windows-linux-mac-and-website/) over HTTPS.

---

# Manual Setup

> Please refer to the [`Manual Setup`](https://svdc1.github.io/mirumoji/docs/Manual-Setup) Page

---

If you encounter any issues, please feel free to open an issue.
