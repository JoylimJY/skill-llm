FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install glin-profanity globally and locally
RUN npm install -g glin-profanity
RUN mkdir -p /workspace && cd /workspace && npm init -y && npm install glin-profanity

WORKDIR /workspace