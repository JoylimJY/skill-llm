FROM debian:12

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    bash \
    coreutils \
    findutils \
    rsync \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash agent
WORKDIR /home/agent