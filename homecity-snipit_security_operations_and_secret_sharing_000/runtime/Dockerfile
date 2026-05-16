FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    nodejs \
    npm \
    python3 \
    python3-pip \
    python3-venv \
    jq \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g snipit-sh --registry https://registry.npmmirror.com || npm install -g snipit-sh

RUN pip3 install flask -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace