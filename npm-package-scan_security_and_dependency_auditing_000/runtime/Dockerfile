FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    ripgrep \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install bun via npm (avoids external GitHub download)
RUN npm install -g bun
ENV PATH="/root/.bun/bin:$PATH"

# Make sure npm is up to date
RUN npm install -g npm@10

WORKDIR /workspace