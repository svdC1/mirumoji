# --- Start From Ubuntu ---
FROM ubuntu:22.04

# --- Set WORKDIR and Variables ---
WORKDIR /workspace

ENV PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}" \
    PIP_NO_CACHE_DIR=1\
    NODE_VERSION=22.0.0

# --- System Packages ---

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    wget \
    xz-utils \
    mecab \
    libmecab-dev \
    software-properties-common \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Install Python 3.11 ---
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3.11-venv python3-pip \
    && rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    python3.11 -m pip install --upgrade pip

# --- Install Torch ---
RUN python3.11 -m pip install --no-cache-dir \
    torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
    --index-url https://download.pytorch.org/whl/cpu

# --- Install Node 22 ---

RUN ARCH= && dpkgArch="$(dpkg --print-architecture)" \
    && case "${dpkgArch##*-}" in \
    amd64) ARCH='x64';; \
    ppc64el) ARCH='ppc64le';; \
    s390x) ARCH='s390x';; \
    arm64) ARCH='arm64';; \
    armhf) ARCH='armv7l';; \
    i386) ARCH='x86';; \
    *) echo "unsupported architecture"; exit 1 ;; \
    esac \
    && curl -fsSLO --compressed "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && tar -xJf "node-v$NODE_VERSION-linux-$ARCH.tar.xz" -C /usr/local --strip-components=1 --no-same-owner \
    && rm "node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && ln -s /usr/local/bin/node /usr/local/bin/nodejs \
    # smoke tests
    && node --version \
    && npm --version

# --- Backend Dependencies ---
COPY ../apps/backend/requirements.txt /tmp/backend_requirements.txt
RUN python3.11 -m pip install -r /tmp/backend_requirements.txt

# --- Install UniDic + KotobaseDB ---
RUN python3.11 -m unidic download && \
    kotobase pull-db

# --- Expose Vite Dev Port + Uvicorn Port ---
EXPOSE 8000 
EXPOSE 5173

# --- Drop into bash ---
CMD ["bash"]
