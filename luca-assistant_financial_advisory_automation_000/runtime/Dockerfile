FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    bash \
    git \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Install luca-assistant via uv
RUN uv tool install luca-assistant -i https://pypi.tuna.tsinghua.edu.cn/simple || \
    uv tool install luca-assistant

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace