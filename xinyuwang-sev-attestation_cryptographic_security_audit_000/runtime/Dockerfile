FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    openssl \
    python3 \
    python3-pip \
    xxd \
    curl \
    wget \
    git \
    build-essential \
    ca-certificates \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Install Python cryptography library for generating valid test artifacts
RUN pip3 install cryptography -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace