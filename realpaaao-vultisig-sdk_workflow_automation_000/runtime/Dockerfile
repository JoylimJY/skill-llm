FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install ast-grep-py 2>/dev/null || true

# Install TypeScript tooling globally
RUN npm install -g typescript ts-node @types/node --registry https://registry.npmmirror.com 2>/dev/null || \
    npm install -g typescript ts-node @types/node

WORKDIR /workspace