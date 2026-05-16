FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    tmux \
    python3 \
    python3-pip \
    bash \
    curl \
    jq \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Set up git identity for commits
RUN git config --global user.email "test@sandbox.local" && \
    git config --global user.name "Sandbox Tester"

WORKDIR /workspace