FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    tar \
    gzip \
    coreutils \
    findutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash agent

RUN mkdir -p /workspace && chown agent:agent /workspace && chmod 777 /workspace

WORKDIR /home/agent