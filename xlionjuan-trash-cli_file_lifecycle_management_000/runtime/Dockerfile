FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install trash-cli -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN mkdir -p /workspace
WORKDIR /workspace