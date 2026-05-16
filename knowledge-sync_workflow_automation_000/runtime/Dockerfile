FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    inotify-tools \
    bash \
    coreutils \
    python3 \
    python3-pip \
    curl \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pytest -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace