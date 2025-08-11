"""
Defines the `/api` router of the GUI launcher application
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from subprocess import Popen, CalledProcessError
import logging
import os
from typing import (Generator,
                    Dict,
                    AsyncGenerator
                    )

from core import (docker_running,
                  has_nvidia_gpu,
                  get_host_lan_ip,
                  docker_compose,
                  build_img
                  )
from models import (StartRequest,
                    StopRequest,
                    BuildRequest
                    )
from paths import (COMPOSE_LOCAL_CPU_RELPATH,
                   COMPOSE_LOCAL_GPU_RELPATH,
                   COMPOSE_PREBUILT_CPU_RELPATH,
                   COMPOSE_PREBUILT_DOCKER_CPU_RELPATH,
                   COMPOSE_PREBUILT_DOCKER_GPU_RELPATH,
                   COMPOSE_PREBUILT_GPU_RELPATH,
                   REPO_DIR,
                   FRONTEND_BUILD_CONTEXT_RELPATH,
                   FRONTEND_DOCKERFILE_RELPATH,
                   FRONTEND_LOCAL_IMAGE_NAME,
                   BACKEND_BUILD_CONTEXT_RELPATH,
                   BACKEND_CPU_DOCKERFILE_RELPATH,
                   BACKEND_CPU_LOCAL_IMAGE_NAME,
                   BACKEND_GPU_DOCKERFILE_RELPATH,
                   BACKEND_GPU_LOCAL_IMAGE_NAME,
                   )

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# --- Stream Helper ---


async def _stream_gen(gen: Generator[str, str, Popen[str]]
                      ) -> AsyncGenerator[str, str]:
    """
    Formats a generator's output for event-stream

    Args:
      gen (Generator[str,str,Popen[str]]): Generator from `core.run_command`

    Yields:
      str: Generator's stdout
    """
    while True:
        try:
            yield f"data: {next(gen)}\n\n"
        except StopIteration:
            yield "event: done\ndata:\n\n"
            break


@router.get("/dockerRunning")
async def check_docker() -> Dict[str, bool]:
    """
    GET endpoint which checks if Docker deamon is running

    Returns:
      Dict[str,bool]: Dictionary with `status` key
    """
    try:
        p = docker_running()
        if p.returncode == 0:
            return {"status": True}
        else:
            return {"status": False}
    except CalledProcessError:
        return {"status": False}


@router.get("/hasGPU")
async def has_gpu() -> Dict[str, bool]:
    """
    GET endpoint which checks if the system has an NVIDIA GPU installed

    Returns:
      Dict[str,bool]: Dictionary with `status` key
    """
    return {"status": has_nvidia_gpu()}


@router.post("/start")
async def start_app(request: StartRequest) -> StreamingResponse:
    """
    POST endpoint which starts the mirumoji application by running docker
    compose up command and streaming back the process's stdout.

    Args:
      request (StartRequest): Endpoint request in the format of `StartRequest`

    Returns:
      StreamingResponse: Docker command's stdout
    """
    try:
        # Configure IP
        get_host_lan_ip()
        # Configure Environment
        os.environ["OPENAI_API_KEY"] = request.OPENAI_API_KEY
        if not request.gpu:
            os.environ["MODAL_TOKEN_ID"] = request.MODAL_TOKEN_ID
            os.environ["MODAL_TOKEN_SECRET"] = request.MODAL_TOKEN_SECRET

        # Configure Compose File
        compose_file = None
        if request.local:
            if request.gpu:
                compose_file = REPO_DIR / COMPOSE_LOCAL_GPU_RELPATH
            else:
                compose_file = REPO_DIR / COMPOSE_LOCAL_CPU_RELPATH
        else:
            if request.repository == "GitHub":
                if request.gpu:
                    compose_file = REPO_DIR / COMPOSE_PREBUILT_GPU_RELPATH
                else:
                    compose_file = REPO_DIR / COMPOSE_PREBUILT_CPU_RELPATH
            else:
                if request.gpu:
                    compose_file = (
                        REPO_DIR / COMPOSE_PREBUILT_DOCKER_GPU_RELPATH
                        )
                else:
                    compose_file = (
                        REPO_DIR / COMPOSE_PREBUILT_DOCKER_CPU_RELPATH
                        )
        # Build Response
        stream = StreamingResponse(
            content=_stream_gen(docker_compose("up",
                                               name_only=False,
                                               command_flags=["-d"],
                                               docker_compose_file=compose_file
                                               )
                                ),
            status_code=200,
            media_type="text/event-stream"
        )
        return stream
    except Exception as e:
        LOGGER.error(f"Failed to start app: '{e}'")
        raise HTTPException(400, detail=str(e))


@router.post("/stop")
async def stop_app(request: StopRequest) -> StreamingResponse:
    """
    POST endpoint which stops the mirumoji application by running docker
    compose down command and streaming back the process's stdout.

    Args:
      request (StartRequest): Endpoint request in the format of `StopRequest`

    Returns:
      StreamingResponse: Docker command's stdout
    """
    try:
        flags = []
        if request.clean:
            flags.append("-v")
        stream = StreamingResponse(
            content=_stream_gen(docker_compose("down",
                                               name_only=True,
                                               command_flags=flags
                                               )
                                ),
            status_code=200,
            media_type="text/event-stream"
        )
        return stream
    except Exception as e:
        LOGGER.error(f"Failed to stop application: '{e}'")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/build")
async def build_imgs(request: BuildRequest) -> StreamingResponse:
    """
    POST endpoint which builds the mirumoji Docker images locally by running
    docker build command and streaming back the process's stdout.

    Args:
      request (StartRequest): Endpoint request in the format of `StopRequest`

    Returns:
      StreamingResponse: Docker command's stdout
    """
    async def _build_stream() -> AsyncGenerator[str, str]:
        # Build Frontend
        frontend_dockerfile = REPO_DIR / FRONTEND_DOCKERFILE_RELPATH
        frontend_context = REPO_DIR / FRONTEND_BUILD_CONTEXT_RELPATH
        frontend = build_img(image_name=FRONTEND_LOCAL_IMAGE_NAME,
                             dockerfile=frontend_dockerfile,
                             build_context=frontend_context
                             )
        while True:
            try:
                yield await f"data: {next(frontend)}\n\n"
            except StopAsyncIteration:
                yield "data: Frontend Image Built !\n\n"
                break
        # Build Backend
        backend_context = REPO_DIR / BACKEND_BUILD_CONTEXT_RELPATH
        if request.gpu:
            backend_dockerfile = REPO_DIR / BACKEND_GPU_DOCKERFILE_RELPATH
            backend_image_name = REPO_DIR / BACKEND_GPU_LOCAL_IMAGE_NAME
        else:
            backend_dockerfile = REPO_DIR / BACKEND_CPU_DOCKERFILE_RELPATH
            backend_image_name = REPO_DIR / BACKEND_CPU_LOCAL_IMAGE_NAME

        backend = build_img(image_name=backend_image_name,
                            dockerfile=backend_dockerfile,
                            build_context=backend_context
                            )
        while True:
            try:
                yield await f"data: {next(backend)}\n\n"
            except StopAsyncIteration:
                yield "data: Backend Image Built !\n\n"
                yield "event: done\ndata:\n\n"
    try:
        # Build Stream
        stream = StreamingResponse(
            content=_build_stream,
            status_code=200,
            media_type="text/event-stream"
        )
        return stream
    except Exception as e:
        LOGGER.error(f"Error building images locally: '{e}'")
        raise HTTPException(400, detail=str(e))
