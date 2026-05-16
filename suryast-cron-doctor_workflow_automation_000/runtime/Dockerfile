FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    cron \
    python3 \
    python3-pip \
    bash \
    procps \
    sudo \
    grep \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install python-dateutil --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN useradd -m -s /bin/bash agent && echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /workspace