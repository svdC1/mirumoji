# Manual Setup

This guide explains how to run Mirumoji on your local machine using Docker Compose. This setup uses pre-built Docker images for both the frontend and backend services, which will be pulled from GitHub Container Registry (ghcr.io) or Docker Hub (docker.io)

??? info "Prerequisites"

    Before you begin, ensure you have the following installed on your system:

    -   **Docker Desktop:**
        -   Install [`Docker Desktop`](https://www.docker.com/products/docker-desktop/)

??? tip "When Running With Local GPU"

    These apply only if you choose to run using your local GPU.

    -   **NVIDIA GPU:** You need an NVIDIA graphics card.

    -   **NVIDIA Drivers:** Ensure you have the latest NVIDIA drivers installed for your operating system.

    -   **NVIDIA Container Toolkit:** Install the [`NVIDIA Container Toolkit`](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). This allows Docker containers to access your NVIDIA GPU.

## Installing

???+ info "**Clone the Repository**"

    ```bash
    git clone https://github.com/svdC1/mirumoji.git
    cd mirumoji
    ```

???+ info "**Create an Environment File for the API Keys**"

    -   The backend service requires an OpenAI API Key for any GPT-related tasks. If you don't have one you can create it at [`OpenAI's API Dashboard`](https://platform.openai.com/settings/organization/api-keys)
    -   The frontend image needs the [`Internal IPv4`](https://geekflare.com/consumer-tech/find-ip-address-of-windows-linux-mac-and-website/) of the machine which will run the application in order to create a [`self-signed`](https://www.keyfactor.com/blog/self-signed-certificate-risks/) HTTPS certificate using `openssl` for the `Nginx` server. The launcher will find it automatically and insert into the environment, however when setting up manually you'll need to include it as `HOST_LAN_IP` in the `.env` file so Docker Compose can pick it up. You can find instructions on how to find your IP and more information on self-signed certificates in the links provided.
    ??? warning "Important"
        If you choose to run without a local GPU, using [`MODAL`](https://modal.com), you'll need to insert your `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` into the `.env` file as well.
    -   In the same repository root, create a new file named `.env`.
    -   Open the `.env` file with a text editor and add your API keys as follows:

    === "Local GPU"
        ```env
        OPENAI_API_KEY=***
        HOST_LAN_IP=***
        ```

    === "CPU + MODAL"

        ```env
        OPENAI_API_KEY=***
        HOST_LAN_IP=***
        MODAL_TOKEN_ID=***
        MODAL_TOKEN_SECRET=***
        ```

## Running the Application

1.  **Open your terminal or command prompt.**
2.  **Navigate to the repo directory**
3.  **Run the following commands based on your setup choice**

    === "CPU + Modal"

        ```bash
        docker compose -f compose/docker-compose.cpu.yaml up -d
        ```

    === "Local GPU"

        ```bash
        docker compose -f compose/docker-compose.gpu.yaml up -d
        ```

-   This command will download the necessary Docker images (if you don't have them already), build the containers, and start them in detached mode (`-d`), meaning they will run in the background.
??? warning 
    The first time you run this, downloading the images might take a while, especially the GPU backend image, depending on your internet connection.

??? note
    To pull images from Docker Hub (`docker.io`) instead of GitHub Registry (`ghcr.io`)
    
    === "CPU + Modal"
        ```bash
        docker compose -f compose/docker-compose.cpu.dockerpull.yaml up -d
        ```
    === "Local GPU"
        ```bash
        docker compose -f compose/docker-compose.gpu.dockerpull.yaml up -d
        ```

## Accessing the Application

Once the containers are running:

=== "**Frontend Application**"
    -   Open your web browser and go to you [`localhost`](https://localhost) over HTTPS where `Nginx` will serve the application.
=== "**Backend API (Direct Access)**"
    -   The backend API will be accessible at your [`localhost`](http://localhost:8000) at port `8000` where uvicorn will deploy the API. It will also be available at your [`localhost/api`](https://localhost/api/health/status) through a reverse-proxy.
    -   The frontend application is configured to communicate with the backend automatically.
    -   If you want to check if the backend is running correctly you can access the [`/health/status`](http://localhost:8000/health/status) endpoint, where you should see the following `JSON` response: `{'status':'ok'}`. You can also check information about the Docker Container running the backend at the [`/health/system`](http://localhost:8000/health/system) endpoint.

> You can access it from any device inside your local network using your computer's [`Internal IPv4 address`](https://geekflare.com/consumer-tech/find-ip-address-of-windows-linux-mac-and-website/) over HTTPS.

> On the first time access on any device, the browser will display a security warning because the HTTPS certificate is [`self-signed`](https://www.keyfactor.com/blog/self-signed-certificate-risks/). This presents very little risk since the application runs entirely inside your system and is only available inside your local network. To learn more about this you can follow the link provided on self-signed.

## Stopping the Application

To stop the application and remove the containers:

1.  **Open your terminal or command prompt.**
2.  **Navigate to the repo directory**
3.  **Run the command:**

=== "CPU + Modal"

    ```bash
    docker compose -f compose/docker-compose.cpu.yaml down
    ```

=== "Local GPU"

    ```bash
    docker compose -f compose/docker-compose.gpu.yaml down
    ```

-   This command will stop and remove the containers. If you also want to remove the volumes (Application cache to speed up subsequent runs and your database/files), you can attach the `-v` flag at the end of the command.

## Troubleshooting

??? warning "**Port Conflicts**"
    If you see errors about ports already being in use (e.g., port `443`, `8000` or `80`), it means another application on your system is using that port. You can either stop the other application or modify the port mappings in the specific docker compose file you’re running (e.g., change `"80:80"` to `"YOUR_NEW_PORT:80"`).
??? warning "**Docker Not Running**"
    Ensure the Docker service/daemon is running on your system.
??? warning "**GPU Issues (Backend)**"
    If you encounter issues with the backend and GPU acceleration, double-check your NVIDIA driver installation and that the NVIDIA Container Toolkit is correctly set up. You can check Docker's access to the GPU by running this test image:
    ```bash
    docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
    ```

---

-   **Enjoy using Mirumoji !**
-   **If you encounter any issues not covered here, please check the Wiki and Discussions for support or open an issue in the repository.**
