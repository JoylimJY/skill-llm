FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    rsync \
    python3 \
    python3-pip \
    jq \
    curl \
    bash \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test" && \
    git config --global init.defaultBranch main

WORKDIR /workspace