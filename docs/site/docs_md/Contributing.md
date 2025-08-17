# Contributing

## Welcome!

> First off, thank you for considering contributing to Mirumoji !

## How to Contribute

This section outlines the different ways you can contribute to the Mirumoji project.

### Development Environment

Setting up the development environment using VSCode Dev Containers is the recommended way to get started. This provides a consistent environment with all necessary dependencies pre-configured.

???+ info "Benefits of using Dev Containers"

    - Pre-configured dependencies and tools.
    - Consistent environment across different operating systems.
    - Isolates development environment from your local system.

???+ tips "Prerequisites"

    > Make sure you have [`VSCode`](https://code.visualstudio.com/), [`Docker Desktop`](https://docs.docker.com/desktop/) and the [`VSCode Dev Containers Extension`](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed.

    > Make sure Docker Desktop is running.

#### Clone Repository

Clone the Mirumoji repository to your local machine:

```bash
git clone https://github.com/svdC1/mirumoji.git
```

#### Open in VSCode

```bash
code mirumoji
```

#### Starting Dev Containers

> Inside VSCode open the Command Pallet with ++ctrl+shift+p++

> Type in `Dev Containers`

> Click the option `Reopen in Container`

???+ info 
    A prompt will appear allowing you to choose between starting up the `Mirumoji (GPU)` development container _(~30GB Uncompressed)_ and the `Mirumoji (CPU)` development container _(~5.5GB Uncompressed)_.

> Choose the `GPU` option if your machine has an `NVIDIA GPU`, otherwise choose the `CPU` option.

???+ warning 
    The first startup might take a few minutes since the development image needs to be pulled from the repository

#### Running Services

=== "Running the Backend"

    > Once inside the development container environment, you can start up the Python backend by running the following command in a terminal. The `8000` port is already forwarded in the container and should be visible in your `localhost:8000`.

    ``` bash
    cd apps/backend
    # Run Uvicorn
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

=== "Running the Frontend"

    > Once inside the development container environment, you can start up the frontend by running the following command in a terminal. The `5173` port is already forwarded in the container and should be visible in your `localhost:5173`

    ```bash
    cd apps/frontend
    # Install package.json requirements
    npm install
    # Run Vite Dev Server
    npm run dev -- --host
    ```

=== "Installing the Launcher"

    > Once inside the development container environment, you can install the Python CLI launcher package in editable mode by running the following command.

    ```bash
    cd apps/cli/mirumoji
    pip install --editable .
    ```

### Repository

=== "Creating a Pull Request"

    > 1. Fork Repository
    > 2. Open fork in development container `(Optional)`
    > 3. Create a new branch
    >
    > ```bash
    > git chekout -b <BRANCH_NAME>
    > ```
    >
    > 4. Commit new changes
    > 5. Open a pull request according to the [`Pull Request Template`](https://github.com/svdC1/mirumoji/blob/main/.github/pull_request_template.md)

=== "Opening an Issue"

    > 1. Go to the repository's [`Issues`](https://github.com/svdC1/mirumoji/issues) page
    > 2. Click on `New Issue`
    > 3. Choose a pre-made template such as the [`Bug Issue Template`](https://github.com/svdC1/mirumoji/blob/main/.github/ISSUE_TEMPLATE/bug_report.md) and [`Feature Request Template`](https://github.com/svdC1/mirumoji/blob/main/.github/ISSUE_TEMPLATE/feature_request.md) or open a new blank issue.
    > 4. Edit the template / blank issue with required information.

## Rules

=== "Purpose of Guidelines"

    > Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

=== "Follow The Code of Conduct"

    > When submiting contributions, please adhere to the [`Code of Conduct`](https://github.com/svdC1/mirumoji/blob/main/.github/CODE_OF_CONDUCT.md)

    > Responsibilities
    >
    > -   Create issues for any major changes and enhancements that you wish to make. Discuss things transparently and get community feedback.
    > -   Follow provided issue templates when submitting.
    > -   Keep feature versions as small as possible, preferably one new feature per version.
    > -   Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. See the [Python Community Code of Conduct](https://www.python.org/psf/codeofconduct/).
