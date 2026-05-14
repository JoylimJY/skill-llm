FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    zfsutils-linux \
    python3 \
    python3-pip \
    jq \
    bash \
    coreutils \
    procps \
    && rm -rf /var/lib/apt/lists/*