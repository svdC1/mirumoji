# Use the NVIDIA CUDA runtime image as the base for GPU support
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}" \
    PIP_NO_CACHE_DIR=1

# Install system dependencies from both Dockerfiles
# Includes build-essential for some python packages, git, ffmpeg, mecab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    wget \ 
    xz-utils \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Ensure /usr/bin/python and /usr/bin/python3 both point to python3.11
RUN update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11  1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
RUN python3.11 -m pip install --upgrade pip

# Install PyTorch with CUDA support
# Specify index URL for CUDA 12.1 compatible wheels, suitable for CUDA 12.3 base image.
RUN python3.11 -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# Install Helpers

RUN python3.11 -m pip install huggingface_hub \
    requests sentencepiece

# Download jamdict.db
RUN mkdir -p /root/.jamdict/data && \
    wget --no-check-certificate 'https://docs.google.com/uc?export=download&id=1QZRzOoMF4CGlkdl0FyU7ledAZLRlpoom' \
    -O /tmp/jamdict.db.xz && \
    unxz /tmp/jamdict.db.xz && \
    mv /tmp/jamdict.db /root/.jamdict/data/jamdict.db

# Copy requirements.txt and install all dependencies
COPY requirements.txt .
RUN python3.11 -m pip install -r requirements.txt

# Download UniDic Dictionary
RUN python3.11 -m unidic download

# Pre-cache the Faster-Whisper model (from modal Dockerfile)
RUN python3.11 -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Systran/faster-whisper-large-v3', local_dir_use_symlinks=False)"

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

CMD ["python3.11", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
