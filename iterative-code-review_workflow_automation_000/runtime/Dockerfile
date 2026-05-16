FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    jq \
    curl \
    wget \
    bash \
    python3 \
    python3-pip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest \
    pyyaml

# Create a mock openclaw config tool
RUN mkdir -p /usr/local/bin
RUN printf '#!/bin/bash\nif [[ "$1" == "config" && "$2" == "get" && "$3" == "agents.defaults.subagents.maxSpawnDepth" ]]; then\n  echo "2"\nfi\n' > /usr/local/bin/openclaw && chmod +x /usr/local/bin/openclaw

WORKDIR /workspace