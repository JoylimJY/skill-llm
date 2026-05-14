FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    git \
    python3 \
    python3-pip \
    grep \
    findutils \
    coreutils \
    sed \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test"

WORKDIR /workspace