FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    jq \
    coreutils \
    procps \
    python3 \
    python3-pip \
    curl \
    wget \
    git \
    gawk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace