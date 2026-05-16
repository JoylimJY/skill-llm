FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    git \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    && rm -rf /var/lib/apt/lists/*

RUN git --version && bash --version

WORKDIR /workspace