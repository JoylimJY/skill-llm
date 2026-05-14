FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pre-install molt-life-kernel globally so it's available
RUN npm install -g molt-life-kernel

# Set up workspace
WORKDIR /workspace

# Install Python eval dependencies
RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple