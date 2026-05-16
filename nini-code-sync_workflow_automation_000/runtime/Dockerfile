FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    bash \
    python3 \
    python3-pip \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "agent@fintech.local" && \
    git config --global user.name "Agent Bot" && \
    git config --global init.defaultBranch main

WORKDIR /workspace