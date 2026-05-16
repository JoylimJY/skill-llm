FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    cron \
    systemd \
    inotify-tools \
    git \
    curl \
    wget \
    vim \
    nano \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pyyaml toml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace