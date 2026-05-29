# Use the NVIDIA CUDA runtime image (recommended in FasterWhisper repo) as the base for GPU support
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# --- Set working directory ---
WORKDIR /app

# --- Set env ---
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}" \
    PIP_NO_CACHE_DIR=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# --- Install System Dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    wget \ 
    xz-utils \
    mecab \
    libmecab-dev \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# --- Ensure 'python' and 'python3' commands both point to python3.11 ---
RUN update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11  1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# --- Upgrade PIP ---
RUN python3.11 -m pip install --upgrade pip

# --- Install PyTorch with CUDA support with index URL for CUDA 12.4 compatible wheels, suitable for CUDA 12.3 base image. ---
RUN python3.11 -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# --- Install Helper Packages ---
RUN python3.11 -m pip install huggingface_hub \
    requests sentencepiece

# --- Copy package files and install server dependencies ---
COPY pyproject.toml README.md ./
COPY src/ src/
RUN python3.11 -m pip install ".[server,whisper-local,llm-openai,llm-anthropic]"

# --- Download UniDic Dictionary and Kotobase DB ---
RUN python3.11 -m unidic download
RUN kotobase pull-db

# --- Pre-cache the Faster-Whisper model from huggingface ---
RUN python3.11 -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Systran/faster-whisper-large-v3', local_dir_use_symlinks=False)"

# --- Expose the uvicorn port ---
EXPOSE 8000

# --- Start uvicorn with host mode ---
CMD ["python3.11", "-m", "uvicorn", "mirumoji.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
