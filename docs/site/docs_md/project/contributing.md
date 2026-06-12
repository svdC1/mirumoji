# Contributing

## Welcome!

First off, thank you for considering contributing to `Mirumoji` !

This section outlines the different ways you can contribute to the `Mirumoji` project

### Development Environment

Setting up the development environment using `VSCode Dev Containers` is the recommended way to get started

This provides a consistent environment with all necessary dependencies pre-configured

???+ info "Benefits Of Using Dev Containers"
    - Pre-Configured Dependencies + Tools

    - Consistent Environment Across Different OSes

    - Isolates Development Environment From Your Local System

???+ abstract "Prerequisites"

    - [`VSCode`](https://code.visualstudio.com/)
    
    - [`Docker Desktop`](https://docs.docker.com/desktop/) *(Make Sure It's Running)*
    
    - [`VSCode Dev Containers Extension`](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Clone Repository

Clone The `Mirumoji` Repo

```bash
git clone https://github.com/svdC1/mirumoji.git
```

#### Open In VSCode

```bash
code mirumoji
```

#### Starting Dev Containers

- Inside `VSCode` Open The Command Pallet With ++ctrl+shift+p++

- Type in `Dev Containers`

- Click The Option `Reopen in Container`

???+ abstract "Chossing Between Images"
    - Choose The `Mirumoji (GPU)` Development Container If You Have An `NVIDIA GPU` + Enough Disk Space _(~30GB Uncompressed)_ 
    
    - Choose The `Mirumoji (CPU)` Development Container _(~5.5GB Uncompressed)_ If Your Don't Have An `NVIDIA GPU`


???+ warning 
    The First Startup Might Take A Few Minutes Since Images Need To Be Pulled

#### Useful Commands

=== "Running the Backend"
    ``` bash
    cd apps/mirumoji
    pip install -e .[server,dev]
    # The Container Already Forwards The `8000` Port
    # (Reloads On Code Changes)
    mirumoji server
    ```

=== "Running the Frontend"
    ```bash
    cd apps/frontend
    npm install
    # The Container Already Forwards The `5173` Port
    # Run Vite Dev Server
    npm run dev -- --host
    ```

=== "Running The Desktop Launcher"
    ```bash
    mirumoji gui
    ```

=== "Installing Pre-Commmit Hooks"
    ```bash
    pip install pre-commit
    pre-commit install
    ```

### Repository

=== "Creating a Pull Request"

    - Fork Repository
    - Open Fork In Development Container `(Optional)`
    - Create New Branch

    ```bash
    git checkout -b <BRANCH_NAME>
    ```
    
    - Commit New Changes
    - Open A Pull Request According To The [`Pull Request Template`](https://github.com/svdC1/mirumoji/blob/main/.github/pull_request_template.md)

=== "Opening an Issue"

    - Go To The Repo's  [`Issues Page`](https://github.com/svdC1/mirumoji/issues)
    - Click on `New Issue`
    - Choose A Pre-Made Template ([`Bug Issue Template`](https://github.com/svdC1/mirumoji/blob/main/.github/ISSUE_TEMPLATE/bug_report.md) / [`Feature Request Template`](https://github.com/svdC1/mirumoji/blob/main/.github/ISSUE_TEMPLATE/feature_request.md)) Or Open A New Blank Issue
    - Edit Template / Blank Issue With Required Information

## Rules

=== "Purpose of Guidelines"

    Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests

=== "Follow The Code of Conduct"

    When submitting contributions, please adhere to the [`Code of Conduct`](https://github.com/svdC1/mirumoji/blob/main/.github/CODE_OF_CONDUCT.md)

    ???+ info "Responsibilities"
        - Create issues for any major changes and enhancements that you wish to make. Discuss things transparently and get community feedback
        - Follow provided issue templates when submitting
        - Keep feature versions as small as possible, preferably one new feature per version
        - Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. See the [`Python Community Code of Conduct`](https://www.python.org/psf/codeofconduct/)
