FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    bash \
    findutils \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test" && \
    git config --global init.defaultBranch main

RUN mkdir -p /root/Documents

WORKDIR /workspace