FROM node:24-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    jq \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @mynthai/nova 2>/dev/null || true

WORKDIR /workspace