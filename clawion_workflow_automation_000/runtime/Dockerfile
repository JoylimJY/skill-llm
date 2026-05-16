FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    bash \
    python3 \
    python3-pip \
    nodejs \
    npm \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g clawion 2>/dev/null || true

RUN pip3 install pyyaml jsonschema -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace