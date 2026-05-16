FROM node:22-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install mcporter globally for CLI usage
RUN npm install -g mcporter --registry https://registry.npmmirror.com || \
    npm install -g mcporter

# Install mcp-hello-world package globally to have it available
RUN npm install -g mcp-hello-world --registry https://registry.npmmirror.com || \
    npm install -g mcp-hello-world

WORKDIR /workspace