"""
This module defines configuration Constants and utility functions for the
paths used in the Mirumoji Launcher GUI
"""
from pathlib import Path

# App and Repository Directories
APP_DIR = Path.home() / ".mirumoji_launcher"
REPO_DIR = APP_DIR / "mirumoji"
LOG_DIR = APP_DIR / "logs"
REPO_URL = "https://github.com/svdC1/mirumoji.git"
SRC_DIR = Path(__file__).parent.parent.resolve()

# Web Assets
WEB_DIR = SRC_DIR / "gui" / "web"

# Docker Image names for local builds
FRONTEND_LOCAL_IMAGE_NAME = "mirumoji_frontend_local:latest"
BACKEND_GPU_LOCAL_IMAGE_NAME = "mirumoji_backend_gpu_local:latest"
BACKEND_CPU_LOCAL_IMAGE_NAME = "mirumoji_backend_cpu_local:latest"

# Relative Paths for Dockerfiles within repository
FRONTEND_DOCKERFILE_RELPATH = Path("apps/frontend/Dockerfile")
BACKEND_GPU_DOCKERFILE_RELPATH = Path("apps/backend/Dockerfile")
BACKEND_CPU_DOCKERFILE_RELPATH = Path("apps/backend/Dockerfile.cpu")

# Relative Paths for local build contexts within repository
BACKEND_BUILD_CONTEXT_RELPATH = Path("apps/backend")
FRONTEND_BUILD_CONTEXT_RELPATH = Path("apps/frontend")

# Relative Paths for compose files withing repository
COMPOSE_PREBUILT_CPU_RELPATH = Path("compose/docker-compose.cpu.yaml")
COMPOSE_PREBUILT_GPU_RELPATH = Path("compose/docker-compose.gpu.yaml")
COMPOSE_PREBUILT_DOCKER_GPU_RELPATH = Path(
    "compose/docker-compose.gpu.dockerpull.yaml")
COMPOSE_PREBUILT_DOCKER_CPU_RELPATH = Path(
    "compose/docker-compose.cpu.dockerpull.yaml")
COMPOSE_LOCAL_CPU_RELPATH = Path("compose/docker-compose.local.cpu.yaml")
COMPOSE_LOCAL_GPU_RELPATH = Path("compose/docker-compose.local.gpu.yaml")
