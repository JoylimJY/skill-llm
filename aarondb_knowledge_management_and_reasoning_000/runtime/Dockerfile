FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Pre-install the aarondb-edge package globally so it's available
RUN npm install @criticalinsight/aarondb-edge

# Make node_modules accessible from workspace subdirectories
ENV NODE_PATH=/workspace/node_modules