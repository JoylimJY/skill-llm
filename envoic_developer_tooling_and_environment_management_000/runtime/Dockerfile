FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    nodejs \
    npm \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (provides uvx)
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Install envoic via pip
RUN pip install envoic -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Install envoic via npm
RUN npm install -g envoic --force

# Install jq for JSON inspection in eval
RUN apt-get update && apt-get install -y --no-install-recommends jq && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace