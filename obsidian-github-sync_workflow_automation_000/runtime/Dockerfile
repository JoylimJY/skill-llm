FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    bash \
    cron \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test" && \
    git config --global pull.rebase true && \
    git config --global init.defaultBranch master

WORKDIR /workspace