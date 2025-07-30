# Setup Guide

This guide will help you get the Mirumoji application running on your system.

## **System Prerequisites**

> **Git:** The launcher uses Git to fetch the application files. [`Download Git`](https://git-scm.com/downloads).

> **Docker Desktop:** Mirumoji runs using Docker containers. Docker Desktop provides the necessary Docker engine and command-line tools.
>
>   -   [`Download Docker Desktop for Windows`](https://www.docker.com/products/docker-desktop/)
>   -   [`Download Docker Desktop for macOS`](https://www.docker.com/products/docker-desktop/)
>   -   [`Download Docker Desktop for Linux`](https://docs.docker.com/desktop/setup/install/linux/)

## Security Considerations

> Since this is a bundled application program, it's common to have securities concerns regarding what exactly it is executing. This has been bundled as an executable mainly for the sake of convenience, so that you don't have to manually find which `docker-compose` file is suitable for the version you want to run, look up docker build and compose commands, etc.

 - **Option 1**

> The executables for the various OSes are created in a [`GitHub Actions Runner`](https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners) with [`PyInstaller`](https://github.com/pyinstaller/pyinstaller) and the code used to create them can be found in this repository at [`.github/workflows/build_release.yaml`](https://github.com/svdC1/mirumoji/blob/main/.github/workflows/build_release.yaml). All the executable does is execute the [`launcher.py`](https://github.com/svdC1/mirumoji/blob/main/apps/cli/launcher.py) file, like Option 2, with the added convenience that you don't need to have python, or the two python dependencies the script needs, installed in order to run it.

> If you would like this added convenience of the executable, you can find instructions for your specific platform at the section [`Option 1`](#option-1) below.


 - **Option 2**

> If you prefer to not use the executable, you can still run the `launcher.py` script with your own Python environment by following the instructions detailed below in the section [`Option 2`](#option-2)

 - **Manual Setup**
> If you prefer to download the specific `docker-compose` file for the version you want to run and use it to build the containers directly, you can follow the instructions provided at the page linked in the [`Manual Setup`](#manual-setup) section below.
---

## Option 1

### 1 - **Download the Launcher**

>   *   Download the executable for your operating system and place somewhere convenient
>       *   **Windows:** [`mirumoji-launcher-windows.exe`](https://github.com/svdC1/mirumoji/releases/latest/download/mirumoji-launcher-windows.exe)
>       *   **macOS:** [`mirumoji-launcher-macos`](https://github.com/svdC1/mirumoji/releases/latest/download/mirumoji-launcher-macos)
>       *   **Linux:** [`mirumoji-launcher-linux`](https://github.com/svdC1/mirumoji/releases/latest/download/mirumoji-launcher-linux)


### 2 - **Make the Launcher Executable (macOS and Linux only)**

>   *   **macOS:**
>        1.  Open the Terminal application.
>        2.  Navigate to the directory where you saved the launcher. For example, if it's on your Desktop:
>            ```bash
>            cd ~/Desktop
>            ```
>        3.  Make the file executable:
>            ```bash
>            chmod +x mirumoji-launcher-macos
>            ```
>    *   **Linux:**
>        1.  Open your terminal.
>        2.  Navigate to the directory where you saved the launcher.
>        3.  Make the file executable:
>            ```bash
>            chmod +x mirumoji-launcher-linux
>            ```

### 3 - **Configure `.env` File**

>    The Mirumoji application requires a `.env` file to be present in the same folder as the `launcher`.

>    This file stores your API keys. The launcher will check for this file and the required keys based on your choices.

>    *   **Required for all setups:**
>        ```bash
>        OPENAI_API_KEY=***
>        ```

>    *   **Required For CPU Version:**
>        ```bash
>        MODAL_TOKEN_ID=***
>        MODAL_TOKEN_SECRET=***
>        ```

### 4 - **Run the Launcher**

>    *   **Windows:**
>        1.  Open Command Prompt or PowerShell.
>        2.  Navigate to the directory where you saved `mirumoji-launcher-windows.exe`.
>        3.  Run the launcher by typing:
>            ```bash
>            .\mirumoji-launcher-windows.exe launch
>            ```
>    *   **macOS:**
>        1.  In the Terminal (after making it executable), run:
>            ```bash
>            ./mirumoji-launcher-macos launch
>            ```
>            *Security Note:* On newer macOS versions, you might see a security warning the first time you run it because it's a downloaded application. You may need to go to "System Settings" > "Privacy & Security", scroll down, and click "Open Anyway" or allow the app.
>    *   **Linux:**
>        1.  In your terminal (after making it executable), run:
>            ```bash
>            ./mirumoji-launcher-linux launch
>            ```

### 5 - **Follow On-Screen Instructions**

>    The launcher will guide you through the rest of the setup process:
>    *   It will clone the main Mirumoji application files into a `mirumoji_workspace` folder.
>    *   It will ask if you want to build Docker images locally or use pre-built ones.
>    *   It will ask if you want to use a GPU-accelerated backend (NVIDIA GPU required for this option).
>    *   It will check for a necessary `.env` configuration file and guide you if it's missing or incomplete.
>    *   It will discover and print you machine's local IPv4 address which is needed to validate the HTTPS certificate.


### 6 - **Starting Services**

>    Once configured, the launcher will start the Mirumoji Docker services.

### 7 - **Managing Services**

> After services have started you can manage them in the `Containers` section of your Docker Desktop application.

---

## Option 2

### 1 -  **Install Dependencies**

>    Install the [`mirumoji python package`](https://pypi.org/project/mirumoji/)
>    ```bash
>    pip install mirumoji
>    ```

### 2 - **Configure `.env` File**

> See [`Step 3`](#3-configure-env-file) of [`Option 1`](#option-1).

### 3 - **Run the Launcher Script**

> In the same python environment you installed the mirumoji package run

>    ```bash
>    mirumoji launch
>    ```

---
## Accessing the Application

> Once the containers are running the application will be live in your [localhost](https://localhost) over HTTPS.

> You can access it from any device inside your local network by accessing your computer's local [`IPv4 address`](https://geekflare.com/consumer-tech/find-ip-address-of-windows-linux-mac-and-website/) over HTTPS.

> On the first time access on any device, the browser will display a security warning because the HTTPS certificate is [`self-signed`](https://www.keyfactor.com/blog/self-signed-certificate-risks/). This presents very little risk since the application runs entirely inside your system and is only available inside your local network. To learn more about this you can follow the link provided on `self-signed`.

---
# Manual Setup

> Please refer to the [`Manual Setup`](https://github.com/svdC1/mirumoji/wiki/Manual-Setup) Page

---
If you encounter any issues, please feel free to open an issue.
