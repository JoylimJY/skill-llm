FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Pre-cache the skillgate package so the agent doesn't need to wait
RUN npm install -g npm@latest && \
    npx --yes @skillgate/openclaw-skillgate@0.1.3 --version 2>/dev/null || true

WORKDIR /workspace

ENV NODE_PATH=/usr/local/lib/node_modules
ENV NPM_CONFIG_CACHE=/root/.npm