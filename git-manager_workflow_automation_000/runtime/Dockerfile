FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    bash \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest \
    pyyaml

# Configure git global identity so commits work inside container
RUN git config --global user.email "agent@testenv.local" && \
    git config --global user.name "Test Agent" && \
    git config --global init.defaultBranch main

WORKDIR /workspace