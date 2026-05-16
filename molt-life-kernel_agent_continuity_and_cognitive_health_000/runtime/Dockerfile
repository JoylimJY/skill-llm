FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Pre-install molt-life-kernel globally so it's available for npm linking
WORKDIR /opt/molt-bootstrap
RUN npm install molt-life-kernel 2>/dev/null || true

# Pre-install in a shared location
RUN mkdir -p /usr/local/lib/node_modules_shared
WORKDIR /usr/local/lib/node_modules_shared
RUN npm install molt-life-kernel

ENV NODE_PATH=/usr/local/lib/node_modules_shared/node_modules

WORKDIR /workspace