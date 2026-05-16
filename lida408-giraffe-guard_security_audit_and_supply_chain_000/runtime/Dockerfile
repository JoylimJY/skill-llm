FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    grep \
    sed \
    findutils \
    gawk \
    perl \
    file \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace