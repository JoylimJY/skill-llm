FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    bash \
    curl \
    python3 \
    python3-pip \
    coreutils \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "ci@genomics-lab.org" && \
    git config --global user.name "CI Bot" && \
    git config --global init.defaultBranch main

WORKDIR /workspace