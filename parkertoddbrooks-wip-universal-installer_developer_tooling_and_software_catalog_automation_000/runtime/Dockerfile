FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install the wip-universal-installer globally from npm
RUN npm install -g @wipcomputer/universal-installer --registry https://registry.npmjs.org || true

# Ensure workspace directory exists
RUN mkdir -p /workspace

WORKDIR /workspace