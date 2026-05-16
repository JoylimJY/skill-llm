FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    bash \
    curl \
    wget \
    git \
    procps \
    coreutils \
    jq \
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    pytest \
    pyyaml \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a non-root user to simulate realistic environment
RUN useradd -m -s /bin/bash quant && \
    mkdir -p /home/quant/.local/bin && \
    mkdir -p /home/quant/.openclaw/workspace/tools/claw-guard

# Set up the workspace directory
RUN mkdir -p /workspace && chown quant:quant /workspace

WORKDIR /workspace

# Add ~/.local/bin to PATH
ENV PATH="/home/quant/.local/bin:$PATH"
ENV HOME="/home/quant"